import os
import re
import logging
from pathlib import Path
from pydub import AudioSegment
import tempfile
import asyncio
import discord

# Configuração do logger
logger = logging.getLogger('discord_bot.utils')

# Funções auxiliares para processamento de áudio
def sanitize_filename(filename):
    """Remove caracteres inválidos de nomes de arquivo"""
    # Remove a extensão se houver
    name = os.path.splitext(filename)[0]
    # Substitui caracteres inválidos por underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    # Remove espaços extras e limita o tamanho
    return sanitized.strip().replace(" ", "_")[:50]

def format_duration(duration_ms):
    """Formata a duração em ms para o formato MM:SS"""
    total_seconds = int(duration_ms / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def parse_time(time_str):
    """Converte uma string de tempo (HH:MM:SS ou MM:SS ou SS) para milissegundos"""
    parts = time_str.split(':')
    
    if len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = map(int, parts)
        return (hours * 3600 + minutes * 60 + seconds) * 1000
    elif len(parts) == 2:  # MM:SS
        minutes, seconds = map(int, parts)
        return (minutes * 60 + seconds) * 1000
    elif len(parts) == 1:  # SS
        seconds = int(parts[0])
        return seconds * 1000
    else:
        raise ValueError("Formato de tempo inválido. Use HH:MM:SS, MM:SS ou SS")

def get_audio_paths():
    """Retorna caminhos para os diretórios de áudio"""
    originals_dir = Path('audios/originais')
    edited_dir = Path('audios/editados')
    return originals_dir, edited_dir

def get_audio_duration(file_path):
    """Obtém a duração de um arquivo de áudio em milissegundos"""
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio)
    except Exception as e:
        logger.error(f"Erro ao obter duração do áudio {file_path}: {e}")
        return 0

def cut_audio(input_path, output_path, start_time, end_time):
    """Corta um trecho de um arquivo de áudio e salva no caminho de saída"""
    try:
        # Converter tempos para milissegundos se forem strings
        if isinstance(start_time, str):
            start_time = parse_time(start_time)
        if isinstance(end_time, str):
            end_time = parse_time(end_time)
            
        # Carregar o áudio
        audio = AudioSegment.from_file(input_path)
        
        # Verificar limites
        if start_time < 0:
            start_time = 0
        if end_time > len(audio):
            end_time = len(audio)
        if start_time >= end_time:
            raise ValueError("O tempo inicial deve ser menor que o tempo final")
        
        # Cortar o áudio
        audio_cut = audio[start_time:end_time]
        
        # Salvar o áudio cortado
        audio_cut.export(output_path, format="mp3")
        
        return True, output_path
    except Exception as e:
        logger.error(f"Erro ao cortar áudio: {e}")
        return False, str(e)

def reverse_audio(input_path, output_path):
    """Inverte um arquivo de áudio"""
    try:
        # Carregar o áudio
        audio = AudioSegment.from_file(input_path)
        
        # Inverter o áudio
        audio_reversed = audio.reverse()
        
        # Salvar o áudio invertido
        audio_reversed.export(output_path, format="mp3")
        
        return True, output_path
    except Exception as e:
        logger.error(f"Erro ao inverter áudio: {e}")
        return False, str(e)

def change_speed(input_path, output_path, speed_factor):
    """Altera a velocidade de um arquivo de áudio (versão síncrona para uso web)"""
    try:
        # Converter para float se for string
        if isinstance(speed_factor, str):
            speed_factor = float(speed_factor)
        
        # Verificar limites do fator de velocidade
        if speed_factor <= 0:
            raise ValueError("O fator de velocidade deve ser maior que zero")
        
        # Como o pydub não tem um método direto para alterar a velocidade,
        # usamos FFmpeg diretamente via subprocess
        import subprocess
        
        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-filter:a", f"atempo={speed_factor}",
            "-vn", output_path
        ]
        
        # Executar o comando de forma síncrona
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"Erro FFmpeg: {process.stderr}")
            return False, f"Erro ao processar áudio: {process.stderr}"
        
        return True, output_path
    except Exception as e:
        logger.error(f"Erro ao alterar velocidade do áudio: {e}")
        return False, str(e)

# Versão assíncrona para uso no Discord
async def change_speed_async(input_path, output_path, speed_factor):
    """Altera a velocidade de um arquivo de áudio (versão assíncrona para uso no Discord)"""
    try:
        # Converter para float se for string
        if isinstance(speed_factor, str):
            speed_factor = float(speed_factor)
        
        # Verificar limites do fator de velocidade
        if speed_factor <= 0:
            raise ValueError("O fator de velocidade deve ser maior que zero")
        
        # Como o pydub não tem um método direto para alterar a velocidade,
        # usamos FFmpeg diretamente via subprocess
        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-filter:a", f"atempo={speed_factor}",
            "-vn", output_path
        ]
        
        # Executar o comando
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Aguardar a conclusão do processo
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Erro FFmpeg: {stderr.decode()}")
            return False, f"Erro ao processar áudio: {stderr.decode()}"
        
        return True, output_path
    except Exception as e:
        logger.error(f"Erro ao alterar velocidade do áudio: {e}")
        return False, str(e)

async def ensure_voice_client(ctx):
    """Garante que o bot esteja conectado ao canal de voz do autor"""
    # Verificar se o autor está em um canal de voz
    if ctx.author.voice is None:
        await ctx.send("❌ Você precisa estar em um canal de voz para usar este comando!")
        return None
    
    voice_channel = ctx.author.voice.channel
    logger.info(f"Tentando conectar ao canal: {voice_channel.name} (ID: {voice_channel.id})")
    
    # Obter o cliente de voz para o servidor atual
    voice_client = ctx.guild.voice_client
    
    # Se o bot já estiver conectado ao canal correto, apenas retornar o cliente
    if voice_client and voice_client.channel.id == voice_channel.id:
        logger.info(f"Já conectado ao canal correto: {voice_channel.name}")
        # Se estiver reproduzindo, interromper
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            logger.info(f"Áudio anterior interrompido para nova reprodução")
        return voice_client
    
    # Se o bot estiver conectado a um canal diferente, desconectar primeiro
    if voice_client:
        # Se estiver reproduzindo, interromper
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        
        # Desconectar do canal atual para evitar problemas de conexão persistente
        logger.info(f"Desconectando do canal {voice_client.channel.name} para reconexão")
        await voice_client.disconnect(force=True)
        
        # Aguardar um pouco para garantir que a desconexão foi concluída
        await asyncio.sleep(1)
        voice_client = None
    
    # Tentar conectar com várias tentativas, se necessário
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Tentativa {attempt} de conectar ao canal {voice_channel.name}")
            voice_client = await voice_channel.connect(timeout=10.0, reconnect=True)
            logger.info(f"Conectado com sucesso ao canal de voz: {voice_channel.name}")
            
            # Se chegamos aqui, a conexão foi bem-sucedida
            return voice_client
            
        except discord.ClientException as ce:
            logger.error(f"Erro de cliente Discord ao conectar: {ce}")
            if "already connected" in str(ce).lower():
                # Tenta obter a conexão existente e retorná-la
                for vc in ctx.bot.voice_clients:
                    if vc.guild.id == ctx.guild.id:
                        logger.info(f"Encontrada conexão existente, usando-a em vez de criar nova")
                        return vc
            
            # Se não é o último retry, aguardar antes de tentar novamente
            if attempt < max_retries:
                logger.info(f"Aguardando antes de tentar novamente...")
                await asyncio.sleep(2)
            else:
                await ctx.send(f"❌ Erro ao conectar ao canal (problema de cliente): {ce}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao conectar ao canal de voz: {e}")
            
            # Se não é o último retry, aguardar antes de tentar novamente
            if attempt < max_retries:
                logger.info(f"Aguardando antes de tentar novamente...")
                await asyncio.sleep(2)
            else:
                await ctx.send(f"❌ Erro ao conectar ao canal de voz após {max_retries} tentativas: {e}")
                return None
    
    # Se chegamos aqui, todas as tentativas falharam
    return None

def create_embed_for_audio(audio, is_playing=False):
    """Cria um embed para exibir informações de um áudio"""
    status = "🔊 Tocando agora" if is_playing else "📀 Disponível"
    emoji = audio.get('emoji', '🎵')
    
    embed = discord.Embed(
        title=f"{emoji} {audio['nome']}",
        description=f"**Status:** {status}\n**Tipo:** {audio['tipo'].capitalize()}",
        color=discord.Color.green() if is_playing else discord.Color.blue()
    )
    
    # Adiciona duração se disponível
    if audio.get('duracao'):
        embed.add_field(
            name="Duração",
            value=format_duration(audio['duracao']),
            inline=True
        )
    
    embed.set_footer(text=f"Caminho: {audio['caminho']}")
    
    return embed
