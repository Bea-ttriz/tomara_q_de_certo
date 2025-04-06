import os
import logging
import discord
from discord.ext import commands
from discord import app_commands
import database
import utils
from pathlib import Path

class Storage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('discord_bot.storage')
        self.originals_dir, self.edited_dir = utils.get_audio_paths()
    
    @commands.command(name="upload")
    async def upload_audio(self, ctx):
        """Faz upload de um arquivo de áudio"""
        if not ctx.message.attachments:
            await ctx.send("❌ Nenhum arquivo anexado. Use !upload e adicione um arquivo de áudio como anexo.")
            return
        
        attachment = ctx.message.attachments[0]
        # Verificar se é um arquivo de áudio
        if not any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
            await ctx.send("❌ O arquivo anexado não é um arquivo de áudio suportado. Formatos aceitos: .mp3, .wav, .ogg, .m4a")
            return
        
        # Sanitizar o nome do arquivo
        filename = utils.sanitize_filename(attachment.filename)
        file_extension = os.path.splitext(attachment.filename)[1].lower()
        
        # Definir o caminho do arquivo
        file_path = self.originals_dir / f"{filename}{file_extension}"
        
        # Verificar se já existe um arquivo com este nome
        if os.path.exists(file_path):
            await ctx.send(f"❌ Já existe um arquivo com o nome '{filename}'. Por favor, use outro nome ou renomeie o arquivo.")
            return
        
        # Baixar o arquivo
        try:
            await attachment.save(file_path)
            self.logger.info(f"Arquivo salvo em {file_path}")
            
            # Obter duração do áudio
            duracao = utils.get_audio_duration(file_path)
            
            # Adicionar ao banco de dados
            success, result = database.add_audio(
                nome=filename,
                caminho=str(file_path),
                tipo='original',
                duracao=duracao
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Áudio adicionado com sucesso!",
                    description=f"**Nome:** {filename}\n**Duração:** {utils.format_duration(duracao)}",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Use !tocar {filename} para reproduzir este áudio")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Erro ao registrar áudio no banco de dados: {result}")
                
                # Remover o arquivo se houve erro no registro
                os.remove(file_path)
        
        except Exception as e:
            self.logger.error(f"Erro ao salvar arquivo: {e}")
            await ctx.send(f"❌ Erro ao salvar arquivo: {e}")
    
    @commands.command(name="renomear")
    async def rename_audio(self, ctx, old_name: str, new_name: str):
        """Renomeia um arquivo de áudio"""
        # Buscar o áudio no banco de dados
        audio = database.get_audio_by_name(old_name)
        if not audio:
            await ctx.send(f"❌ Áudio '{old_name}' não encontrado. Use !listar para ver os áudios disponíveis.")
            return
        
        # Sanitizar o novo nome
        new_name = utils.sanitize_filename(new_name)
        
        # Verificar se já existe um áudio com o novo nome
        if database.get_audio_by_name(new_name):
            await ctx.send(f"❌ Já existe um áudio com o nome '{new_name}'. Escolha outro nome.")
            return
        
        # Atualizar no banco de dados
        success, message = database.update_audio(old_name, {'nome': new_name})
        
        if success:
            await ctx.send(f"✅ Áudio renomeado de '{old_name}' para '{new_name}'.")
        else:
            await ctx.send(f"❌ Erro ao renomear áudio: {message}")
    
    @commands.command(name="emoji")
    async def set_emoji(self, ctx, audio_name: str, emoji: str):
        """Associa um emoji a um arquivo de áudio"""
        # Buscar o áudio no banco de dados
        audio = database.get_audio_by_name(audio_name)
        if not audio:
            await ctx.send(f"❌ Áudio '{audio_name}' não encontrado. Use !listar para ver os áudios disponíveis.")
            return
        
        # Verificar se o emoji é válido
        if len(emoji) > 2 and not (emoji.startswith('<') and emoji.endswith('>')):
            await ctx.send("❌ Emoji inválido. Use um emoji padrão ou um emoji personalizado do Discord.")
            return
        
        # Atualizar no banco de dados
        success, message = database.update_audio(audio_name, {'emoji': emoji})
        
        if success:
            await ctx.send(f"✅ Emoji {emoji} associado ao áudio '{audio_name}'.")
        else:
            await ctx.send(f"❌ Erro ao associar emoji: {message}")
    
    @commands.command(name="excluir")
    async def delete_audio(self, ctx, audio_name: str):
        """Remove um arquivo de áudio do sistema"""
        # Buscar o áudio no banco de dados
        audio = database.get_audio_by_name(audio_name)
        if not audio:
            await ctx.send(f"❌ Áudio '{audio_name}' não encontrado. Use !listar para ver os áudios disponíveis.")
            return
        
        # Confirmar exclusão
        confirm_msg = await ctx.send(f"⚠️ Tem certeza que deseja excluir o áudio '{audio_name}'? Reaja com ✅ para confirmar ou ❌ para cancelar.")
        
        # Adicionar reações
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        # Função para verificar a reação
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            # Aguardar reação
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            # Cancelar
            if str(reaction.emoji) == "❌":
                await ctx.send("❌ Exclusão cancelada.")
                return
            
            # Confirmar exclusão
            if str(reaction.emoji) == "✅":
                # Remover do banco de dados
                success, result = database.remove_audio(audio_name)
                
                if success:
                    # Tentar excluir o arquivo
                    try:
                        os.remove(result['caminho'])
                        await ctx.send(f"✅ Áudio '{audio_name}' removido com sucesso.")
                    except Exception as e:
                        self.logger.error(f"Erro ao excluir arquivo: {e}")
                        await ctx.send(f"⚠️ Áudio removido do banco de dados, mas houve um erro ao excluir o arquivo: {e}")
                else:
                    await ctx.send(f"❌ Erro ao remover áudio: {result}")
        
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Tempo esgotado. Exclusão cancelada.")

async def setup(bot):
    await bot.add_cog(Storage(bot))
