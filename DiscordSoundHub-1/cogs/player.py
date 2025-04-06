import os
import logging
import asyncio
import traceback
import shutil
from collections import deque
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer
import database
import utils

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('discord_bot.player')
        self.currently_playing = {}  # {guild_id: audio_name}
        self.queues = {}  # {guild_id: deque([audio1, audio2, ...])}
        self.is_loop = {}  # {guild_id: bool} - Se a fila está em loop
        
        # Log de inicialização
        self.logger.info("Sistema de fila de reprodução inicializado")
        self.logger.info(f"FFmpeg disponível: {shutil.which('ffmpeg') is not None}")
    
    async def _play_from_queue(self, guild_id):
        """Reproduz o próximo áudio da fila"""
        if guild_id not in self.queues or not self.queues[guild_id]:
            self.logger.info(f"Fila vazia para o servidor {guild_id}")
            return False
        
        # Obter o voice client
        guild = self.bot.get_guild(guild_id)
        if not guild:
            self.logger.error(f"Servidor {guild_id} não encontrado")
            return False
        
        voice_client = guild.voice_client
        if not voice_client:
            self.logger.error(f"Voice client não encontrado para o servidor {guild_id}")
            return False
        
        # Obter o próximo áudio da fila
        audio_name = self.queues[guild_id].popleft()
        audio = database.get_audio_by_name(audio_name)
        
        if not audio:
            self.logger.error(f"Áudio '{audio_name}' não encontrado no banco de dados")
            # Tentar reproduzir o próximo da fila
            return await self._play_from_queue(guild_id)
        
        # Se estiver em modo loop, adicionar o áudio novamente ao final da fila
        if guild_id in self.is_loop and self.is_loop[guild_id]:
            self.queues[guild_id].append(audio_name)
        
        try:
            # Log para diagnóstico
            self.logger.info(f"Reproduzindo próximo áudio da fila: {audio['nome']} de {audio['caminho']}")
            
            # Adicionar opções do FFmpeg
            ffmpeg_options = {
                'options': '-vn -loglevel warning -nostats',
                'before_options': '-nostdin -y'
            }
            
            try:
                # Verificar se Opus está carregado
                opus_loaded = discord.opus.is_loaded()
                self.logger.info(f"Status Opus: {'Carregado' if opus_loaded else 'Não carregado'}")
                
                # Criar o player de áudio e aplicar controle de volume
                audio_source = FFmpegPCMAudio(audio['caminho'], **ffmpeg_options)
                
                # Aplicar transformador de volume apenas se Opus estiver disponível
                if opus_loaded:
                    audio_source = PCMVolumeTransformer(audio_source, volume=0.5)
                
                # Reproduzir o áudio
                voice_client.play(
                    audio_source,
                    after=lambda e: self._queue_callback(guild_id, audio_name, e)
                )
            except discord.opus.OpusNotLoaded as opus_error:
                self.logger.warning(f"Opus não carregado. Usando modo não otimizado: {opus_error}")
                
                # Abordagem simplificada sem Opus
                simple_audio = FFmpegPCMAudio(audio['caminho'], options='-vn')
                voice_client.play(
                    simple_audio,
                    after=lambda e: self._queue_callback(guild_id, audio_name, e)
                )
            except Exception as audio_error:
                self.logger.error(f"Erro específico ao criar fonte de áudio da fila: {audio_error}")
                
                # Tentativa alternativa com configurações mínimas
                self.logger.info("Tentando abordagem alternativa para áudio da fila...")
                try:
                    simple_audio = FFmpegPCMAudio(audio['caminho'], options='-vn')
                    voice_client.play(
                        simple_audio,
                        after=lambda e: self._queue_callback(guild_id, audio_name, e)
                    )
                except Exception as final_error:
                    self.logger.error(f"Falha final ao tentar reproduzir áudio: {final_error}")
                    raise RuntimeError(f"Não foi possível reproduzir o áudio: {audio_name}")
            
            # Registrar que está tocando
            self.currently_playing[guild_id] = audio_name
            
            # Enviar confirmação se possível
            try:
                # Encontrar um canal para enviar a mensagem
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        embed = utils.create_embed_for_audio(audio, is_playing=True)
                        await channel.send(f"🎵 **Reproduzindo da fila:**", embed=embed)
                        break
            except Exception as channel_error:
                self.logger.error(f"Erro ao enviar mensagem de reprodução: {channel_error}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao reproduzir áudio da fila: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _queue_callback(self, guild_id, audio_name, error):
        """Callback para reprodução de áudios da fila"""
        if error:
            self.logger.error(f"Erro ao reproduzir áudio '{audio_name}' da fila: {error}")
            self.logger.error(f"Traceback: {traceback.format_exception(type(error), error, error.__traceback__)}")
        
        # Remover do registro de reprodução
        if guild_id in self.currently_playing:
            del self.currently_playing[guild_id]
        
        # Verificar se há mais áudios na fila
        if guild_id in self.queues and self.queues[guild_id]:
            # Usar asyncio.run_coroutine_threadsafe para executar a corotina de forma segura
            # a partir deste callback que não é uma corotina
            coro = self._play_from_queue(guild_id)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                self.logger.error(f"Erro ao reproduzir próximo áudio da fila: {e}")
        else:
            self.logger.info(f"Fila do servidor {guild_id} concluída")
    
    @commands.command(name="tocar")
    async def play_audio(self, ctx, *, audio_name: str):
        """Reproduz um arquivo de áudio pelo nome ou o adiciona à fila se algo já estiver tocando"""
        # Buscar o áudio no banco de dados
        audio = database.get_audio_by_name(audio_name)
        if not audio:
            await ctx.send(f"❌ Áudio '{audio_name}' não encontrado. Use !listar para ver os áudios disponíveis.")
            return
        
        # Verificar se o arquivo existe
        if not os.path.isfile(audio['caminho']):
            await ctx.send(f"❌ Arquivo de áudio não encontrado em '{audio['caminho']}'.")
            return
        
        # Conectar ao canal de voz
        voice_client = await utils.ensure_voice_client(ctx)
        if not voice_client:
            return
        
        # Inicializar fila para o servidor se não existir
        guild_id = ctx.guild.id
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        
        # Verificar se já está tocando algo
        if voice_client.is_playing():
            # Adicionar à fila em vez de interromper
            self.queues[guild_id].append(audio_name)
            position = len(self.queues[guild_id])
            
            embed = utils.create_embed_for_audio(audio)
            embed.title = f"🎵 Adicionado à fila: {audio['nome']}"
            embed.add_field(name="Posição na fila", value=f"{position}", inline=True)
            
            await ctx.send(embed=embed)
            return
        
        # Tocar o áudio imediatamente
        try:
            # Log para diagnóstico
            self.logger.info(f"Tentando reproduzir áudio: {audio['nome']} de {audio['caminho']}")
            self.logger.info(f"Canal de voz: {voice_client.channel.name}, guild: {ctx.guild.name}")
            
            # Adicionar opções do FFmpeg para melhorar a estabilidade
            ffmpeg_options = {
                'options': '-vn -loglevel warning -nostats',  # Desativar vídeo, reduzir logs
                'before_options': '-nostdin -y'  # Evitar problemas de entrada e sobrescrever arquivos
            }
            
            # Verificar se o ffmpeg está disponível
            ffmpeg_path = shutil.which('ffmpeg')
            self.logger.info(f"FFMPEG path: {ffmpeg_path}")
            
            try:
                # Verificar se Opus está carregado
                opus_loaded = discord.opus.is_loaded()
                self.logger.info(f"Status Opus: {'Carregado' if opus_loaded else 'Não carregado'}")
                
                # Criar o player de áudio e aplicar controle de volume
                audio_source = FFmpegPCMAudio(audio['caminho'], **ffmpeg_options)
                
                # Aplicar transformador de volume apenas se Opus estiver disponível
                if opus_loaded:
                    audio_source = PCMVolumeTransformer(audio_source, volume=0.5)
                
                # Reproduzir o áudio
                voice_client.play(
                    audio_source,
                    after=lambda e: self._queue_callback(ctx.guild.id, audio['nome'], e)
                )
            except discord.opus.OpusNotLoaded as opus_error:
                self.logger.warning(f"Opus não carregado. Usando modo não otimizado: {opus_error}")
                
                # Abordagem simplificada sem Opus
                simple_audio = FFmpegPCMAudio(audio['caminho'], options='-vn')
                voice_client.play(
                    simple_audio,
                    after=lambda e: self._queue_callback(ctx.guild.id, audio['nome'], e)
                )
            except Exception as audio_error:
                self.logger.error(f"Erro específico ao criar fonte de áudio: {audio_error}")
                
                # Tentativa alternativa com opções mínimas
                self.logger.info("Tentando abordagem alternativa sem controle de volume...")
                try:
                    simple_audio = FFmpegPCMAudio(audio['caminho'], options='-vn')
                    voice_client.play(
                        simple_audio,
                        after=lambda e: self._queue_callback(ctx.guild.id, audio['nome'], e)
                    )
                except Exception as final_error:
                    self.logger.error(f"Falha final ao tentar reproduzir áudio: {final_error}")
                    await ctx.send(f"❌ Não foi possível reproduzir o áudio: {audio_name}")
                    return
            
            # Registrar que está tocando
            self.currently_playing[ctx.guild.id] = audio['nome']
            
            # Enviar confirmação com embed
            embed = utils.create_embed_for_audio(audio, is_playing=True)
            await ctx.send(embed=embed)
            
            self.logger.info(f"Reprodução iniciada com sucesso: {audio['nome']}")
            
        except Exception as e:
            self.logger.error(f"Erro ao reproduzir áudio: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await ctx.send(f"❌ Erro ao reproduzir áudio: {e}")
    
    @commands.command(name="pausar")
    async def pause_audio(self, ctx):
        """Pausa a reprodução atual"""
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("⏸️ Áudio pausado.")
        else:
            await ctx.send("❌ Não há áudio sendo reproduzido.")
    
    @commands.command(name="continuar")
    async def resume_audio(self, ctx):
        """Continua uma reprodução pausada"""
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Áudio continuando.")
        else:
            await ctx.send("❌ Não há áudio pausado para continuar.")
    
    @commands.command(name="parar")
    async def stop_audio(self, ctx):
        """Para a reprodução e desconecta"""
        guild_id = ctx.guild.id
        voice_client = ctx.guild.voice_client
        if voice_client:
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await ctx.send("⏹️ Reprodução interrompida.")
            
            await voice_client.disconnect()
            await ctx.send("👋 Desconectado do canal de voz.")
            
            # Limpar o registro de reprodução e fila
            if guild_id in self.currently_playing:
                del self.currently_playing[guild_id]
            
            if guild_id in self.queues:
                self.queues[guild_id].clear()
                await ctx.send("🗑️ Fila de reprodução limpa.")
        else:
            await ctx.send("❌ O bot não está conectado a um canal de voz.")
    
    @commands.command(name="pular")
    async def skip_audio(self, ctx):
        """Pula para o próximo áudio na fila"""
        guild_id = ctx.guild.id
        voice_client = ctx.guild.voice_client
        
        if not voice_client:
            await ctx.send("❌ O bot não está conectado a um canal de voz.")
            return
        
        if not voice_client.is_playing():
            await ctx.send("❌ Nenhum áudio está sendo reproduzido no momento.")
            return
        
        # Verificar se existe uma fila e se há próximos áudios
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("⏭️ Pulando áudio, mas não há mais áudios na fila.")
            voice_client.stop()
            return
        
        # Parar o áudio atual para que o callback seja chamado
        # e o próximo áudio da fila seja reproduzido automaticamente
        await ctx.send("⏭️ Pulando para o próximo áudio...")
        voice_client.stop()
    
    @commands.command(name="fila")
    async def show_queue(self, ctx):
        """Mostra a fila de reprodução atual"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("📃 A fila de reprodução está vazia.")
            return
        
        # Criar embed para listar os áudios na fila
        embed = discord.Embed(
            title="🎶 Fila de Reprodução",
            description=f"Total de áudios na fila: {len(self.queues[guild_id])}",
            color=discord.Color.blue()
        )
        
        # Adicionar o áudio que está sendo reproduzido atualmente
        if guild_id in self.currently_playing:
            current_audio_name = self.currently_playing[guild_id]
            audio = database.get_audio_by_name(current_audio_name)
            if audio:
                embed.add_field(
                    name="🔊 Tocando Agora:",
                    value=f"{audio.get('emoji', '🎵')} **{audio['nome']}**",
                    inline=False
                )
        
        # Adicionar os próximos áudios da fila (limitado a 10)
        items = list(self.queues[guild_id])
        max_items = min(10, len(items))
        
        queue_text = ""
        for i in range(max_items):
            audio_name = items[i]
            audio = database.get_audio_by_name(audio_name)
            if audio:
                emoji = audio.get('emoji', '🎵')
                queue_text += f"{i+1}. {emoji} **{audio['nome']}**\n"
            else:
                queue_text += f"{i+1}. 🎵 **{audio_name}** (não encontrado)\n"
        
        # Se houver mais de 10 áudios, indicar quantos não foram mostrados
        if len(items) > 10:
            queue_text += f"\n... e mais {len(items) - 10} áudios na fila."
        
        embed.add_field(
            name="📋 Próximos na Fila:",
            value=queue_text if queue_text else "Nenhum áudio na fila.",
            inline=False
        )
        
        # Adicionar informação sobre o modo de loop
        loop_status = "✅ Ativado" if guild_id in self.is_loop and self.is_loop[guild_id] else "❌ Desativado"
        embed.add_field(
            name="🔄 Modo Loop:",
            value=loop_status,
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="limpar")
    async def clear_queue(self, ctx):
        """Limpa a fila de reprodução"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("❌ A fila já está vazia.")
            return
        
        # Limpar a fila
        queue_size = len(self.queues[guild_id])
        self.queues[guild_id].clear()
        
        await ctx.send(f"🗑️ Fila limpa! {queue_size} áudios foram removidos.")
    
    @commands.command(name="loop")
    async def toggle_loop(self, ctx):
        """Ativa ou desativa o modo de repetição da fila"""
        guild_id = ctx.guild.id
        
        # Inicializar o estado do loop se necessário
        if guild_id not in self.is_loop:
            self.is_loop[guild_id] = False
        
        # Inverter o estado atual
        self.is_loop[guild_id] = not self.is_loop[guild_id]
        
        if self.is_loop[guild_id]:
            await ctx.send("🔄 Modo loop **ativado**! A fila será repetida continuamente.")
        else:
            await ctx.send("🔄 Modo loop **desativado**! A fila será reproduzida apenas uma vez.")
    
    @commands.command(name="embaralhar")
    async def shuffle_queue(self, ctx):
        """Embaralha a fila de reprodução"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("❌ A fila está vazia, não há o que embaralhar.")
            return
        
        # Converter a deque para lista, embaralhar e voltar para deque
        queue_list = list(self.queues[guild_id])
        import random
        random.shuffle(queue_list)
        self.queues[guild_id] = deque(queue_list)
        
        await ctx.send("🔀 Fila embaralhada com sucesso!")
        # Mostrar a nova fila
        await self.show_queue(ctx)
    
    @commands.command(name="adicionar")
    async def add_to_queue(self, ctx, *, audio_names: str):
        """Adiciona múltiplos áudios à fila de reprodução, separados por vírgula"""
        guild_id = ctx.guild.id
        
        # Inicializar fila se não existir
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        
        # Conectar ao canal de voz
        voice_client = await utils.ensure_voice_client(ctx)
        if not voice_client:
            return
        
        # Separar os nomes de áudio por vírgula
        names = [name.strip() for name in audio_names.split(',')]
        if not names:
            await ctx.send("❌ Por favor, forneça pelo menos um nome de áudio.")
            return
        
        added_count = 0
        not_found = []
        
        # Adicionar cada áudio à fila
        for audio_name in names:
            if not audio_name:  # Pular strings vazias
                continue
                
            audio = database.get_audio_by_name(audio_name)
            if not audio:
                not_found.append(audio_name)
                continue
            
            if not os.path.isfile(audio['caminho']):
                not_found.append(f"{audio_name} (arquivo não encontrado)")
                continue
            
            # Adicionar à fila
            self.queues[guild_id].append(audio_name)
            added_count += 1
        
        # Se não houver nada tocando, iniciar a reprodução
        if added_count > 0 and not voice_client.is_playing():
            await self._play_from_queue(guild_id)
            return
        
        # Mensagem de confirmação
        if added_count > 0:
            message = f"✅ {added_count} áudio(s) adicionado(s) à fila."
            if not_found:
                message += f"\n❌ Não encontrado(s): {', '.join(not_found)}"
            await ctx.send(message)
        else:
            await ctx.send(f"❌ Nenhum áudio válido encontrado. Não encontrado(s): {', '.join(not_found)}")
    
    @commands.command(name="remover")
    async def remove_from_queue(self, ctx, position: int):
        """Remove um áudio da fila pela sua posição"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("❌ A fila está vazia.")
            return
        
        if position < 1 or position > len(self.queues[guild_id]):
            await ctx.send(f"❌ Posição inválida. A fila tem {len(self.queues[guild_id])} áudios.")
            return
        
        # Converter para lista para poder remover por índice
        queue_list = list(self.queues[guild_id])
        audio_name = queue_list[position - 1]
        audio = database.get_audio_by_name(audio_name)
        
        # Remover o áudio
        del queue_list[position - 1]
        self.queues[guild_id] = deque(queue_list)
        
        # Enviar confirmação
        if audio:
            await ctx.send(f"❌ **{audio['nome']}** removido da fila.")
        else:
            await ctx.send(f"❌ Áudio na posição {position} removido da fila.")
    
    def play_callback(self, guild_id, audio_name, error):
        """Callback chamado após a conclusão de um áudio (versão legada, mantida para compatibilidade)"""
        # Redirecionar para o novo callback de fila
        self._queue_callback(guild_id, audio_name, error)
    
    @commands.command(name="tocando")
    async def now_playing(self, ctx):
        """Mostra o que está tocando atualmente"""
        guild_id = ctx.guild.id
        if guild_id in self.currently_playing:
            audio_name = self.currently_playing[guild_id]
            audio = database.get_audio_by_name(audio_name)
            
            if audio:
                embed = utils.create_embed_for_audio(audio, is_playing=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"🎵 Tocando: {audio_name}")
        else:
            await ctx.send("❌ Não há nada tocando no momento.")
    
    # Lidar com reações de emoji (para tocar via emoji)
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Toca um áudio quando um emoji associado é clicado"""
        # Ignorar reações do próprio bot
        if payload.user_id == self.bot.user.id:
            return
        
        # Obter o emoji e verificar se está associado a um áudio
        emoji = str(payload.emoji)
        audio = database.get_audio_by_emoji(emoji)
        
        if not audio:
            return
        
        # Obter o canal e o usuário
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        user = guild.get_member(payload.user_id)
        
        # Verificar se o usuário está em um canal de voz
        if not user.voice:
            return
        
        # Criar um contexto fake para usar as funções existentes
        ctx = type('obj', (object,), {
            'guild': guild,
            'send': channel.send,
            'author': user
        })
        
        # Tocar o áudio
        await self.play_audio(ctx, audio_name=audio['nome'])

async def setup(bot):
    await bot.add_cog(Player(bot))
