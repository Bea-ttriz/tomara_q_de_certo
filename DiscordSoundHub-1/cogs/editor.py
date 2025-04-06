import os
import logging
import tempfile
import discord
from discord.ext import commands
import database
import utils
from pathlib import Path

class Editor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('discord_bot.editor')
        self.originals_dir, self.edited_dir = utils.get_audio_paths()
    
    @commands.command(name="cortar")
    async def cut_audio(self, ctx, audio_name: str, inicio: str, fim: str):
        """Corta um arquivo de áudio (formato de tempo: HH:MM:SS)"""
        # Buscar o áudio no banco de dados
        audio = database.get_audio_by_name(audio_name)
        if not audio:
            await ctx.send(f"❌ Áudio '{audio_name}' não encontrado. Use !listar para ver os áudios disponíveis.")
            return
        
        # Verificar se o arquivo existe
        if not os.path.isfile(audio['caminho']):
            await ctx.send(f"❌ Arquivo de áudio não encontrado em '{audio['caminho']}'.")
            return
        
        # Iniciar processo de corte
        await ctx.send(f"✂️ Cortando áudio '{audio_name}' de {inicio} até {fim}...")
        
        try:
            # Determinar novo nome de arquivo
            new_filename = f"{audio_name}_cortado_{inicio.replace(':', '')}_{fim.replace(':', '')}.mp3"
            new_filepath = self.edited_dir / new_filename
            
            # Cortar o áudio
            success, result = utils.cut_audio(audio['caminho'], new_filepath, inicio, fim)
            
            if not success:
                await ctx.send(f"❌ Erro ao cortar áudio: {result}")
                return
            
            # Obter duração do novo áudio
            duracao = utils.get_audio_duration(new_filepath)
            
            # Adicionar ao banco de dados
            success, db_result = database.add_audio(
                nome=new_filename.split('.')[0],  # Nome sem extensão
                caminho=str(new_filepath),
                tipo='editado',
                duracao=duracao
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Áudio cortado com sucesso!",
                    description=f"**Nome:** {new_filename.split('.')[0]}\n**Duração:** {utils.format_duration(duracao)}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Corte", value=f"De {inicio} até {fim}", inline=False)
                embed.set_footer(text=f"Use !tocar {new_filename.split('.')[0]} para reproduzir este áudio")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Erro ao registrar áudio no banco de dados: {db_result}")
                
                # Remover o arquivo se houve erro no registro
                os.remove(new_filepath)
        
        except Exception as e:
            self.logger.error(f"Erro ao cortar áudio: {e}")
            await ctx.send(f"❌ Erro ao cortar áudio: {e}")
    
    @commands.command(name="inverter")
    async def reverse_audio(self, ctx, audio_name: str):
        """Inverte um arquivo de áudio"""
        # Buscar o áudio no banco de dados
        audio = database.get_audio_by_name(audio_name)
        if not audio:
            await ctx.send(f"❌ Áudio '{audio_name}' não encontrado. Use !listar para ver os áudios disponíveis.")
            return
        
        # Verificar se o arquivo existe
        if not os.path.isfile(audio['caminho']):
            await ctx.send(f"❌ Arquivo de áudio não encontrado em '{audio['caminho']}'.")
            return
        
        # Iniciar processo de inversão
        await ctx.send(f"🔄 Invertendo áudio '{audio_name}'...")
        
        try:
            # Determinar novo nome de arquivo
            new_filename = f"{audio_name}_invertido.mp3"
            new_filepath = self.edited_dir / new_filename
            
            # Inverter o áudio
            success, result = utils.reverse_audio(audio['caminho'], new_filepath)
            
            if not success:
                await ctx.send(f"❌ Erro ao inverter áudio: {result}")
                return
            
            # Obter duração do novo áudio
            duracao = utils.get_audio_duration(new_filepath)
            
            # Adicionar ao banco de dados
            success, db_result = database.add_audio(
                nome=new_filename.split('.')[0],  # Nome sem extensão
                caminho=str(new_filepath),
                tipo='editado',
                duracao=duracao
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Áudio invertido com sucesso!",
                    description=f"**Nome:** {new_filename.split('.')[0]}\n**Duração:** {utils.format_duration(duracao)}",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Use !tocar {new_filename.split('.')[0]} para reproduzir este áudio")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Erro ao registrar áudio no banco de dados: {db_result}")
                
                # Remover o arquivo se houve erro no registro
                os.remove(new_filepath)
        
        except Exception as e:
            self.logger.error(f"Erro ao inverter áudio: {e}")
            await ctx.send(f"❌ Erro ao inverter áudio: {e}")
    
    @commands.command(name="velocidade")
    async def change_speed(self, ctx, audio_name: str, speed_factor: float):
        """Altera a velocidade de um arquivo de áudio (0.5=lento, 2.0=rápido)"""
        # Verificar limites do fator de velocidade
        if speed_factor <= 0:
            await ctx.send("❌ O fator de velocidade deve ser maior que zero.")
            return
        
        # Buscar o áudio no banco de dados
        audio = database.get_audio_by_name(audio_name)
        if not audio:
            await ctx.send(f"❌ Áudio '{audio_name}' não encontrado. Use !listar para ver os áudios disponíveis.")
            return
        
        # Verificar se o arquivo existe
        if not os.path.isfile(audio['caminho']):
            await ctx.send(f"❌ Arquivo de áudio não encontrado em '{audio['caminho']}'.")
            return
        
        # Iniciar processo de alteração de velocidade
        await ctx.send(f"⏩ Alterando velocidade do áudio '{audio_name}' (fator: {speed_factor})...")
        
        try:
            # Determinar novo nome de arquivo
            speed_text = "rapido" if speed_factor > 1 else "lento"
            new_filename = f"{audio_name}_{speed_text}_{str(speed_factor).replace('.', '_')}.mp3"
            new_filepath = self.edited_dir / new_filename
            
            # Usar a função assíncrona do utils para alterar a velocidade
            success, result = await utils.change_speed_async(audio['caminho'], new_filepath, speed_factor)
            
            if not success:
                await ctx.send(f"❌ Erro ao alterar velocidade do áudio: {result}")
                return
            
            # Obter duração do novo áudio
            duracao = utils.get_audio_duration(new_filepath)
            
            # Adicionar ao banco de dados
            success, db_result = database.add_audio(
                nome=new_filename.split('.')[0],  # Nome sem extensão
                caminho=str(new_filepath),
                tipo='editado',
                duracao=duracao
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Velocidade alterada com sucesso!",
                    description=f"**Nome:** {new_filename.split('.')[0]}\n**Duração:** {utils.format_duration(duracao)}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Fator de velocidade", value=str(speed_factor), inline=False)
                embed.set_footer(text=f"Use !tocar {new_filename.split('.')[0]} para reproduzir este áudio")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Erro ao registrar áudio no banco de dados: {db_result}")
                
                # Remover o arquivo se houve erro no registro
                os.remove(new_filepath)
        
        except Exception as e:
            self.logger.error(f"Erro ao alterar velocidade do áudio: {e}")
            await ctx.send(f"❌ Erro ao alterar velocidade do áudio: {e}")

async def setup(bot):
    await bot.add_cog(Editor(bot))
