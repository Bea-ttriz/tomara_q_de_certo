# Este arquivo importa a aplicação do app.py para o funcionamento do workflow "Start application"
from app import app

# Se este arquivo for executado diretamente, inicia o bot do Discord
if __name__ == "__main__":
    # Importação do código principal do bot
    import os
    import logging
    import asyncio
    import discord
    from discord.ext import commands
    from discord import Intents
    from dotenv import load_dotenv
    
    # Configuração de logging para o bot
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s - discord_bot.%(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    # Carregamento das variáveis de ambiente
    load_dotenv()
    
    # Função para garantir que os diretórios necessários existam
    def ensure_directories_exist():
        """Cria os diretórios necessários para armazenamento de áudios e cogs"""
        os.makedirs('audios/originais', exist_ok=True)
        os.makedirs('audios/editados', exist_ok=True)
        os.makedirs('audios/temp', exist_ok=True)
        os.makedirs('cogs', exist_ok=True)
    
    # Função para carregar a biblioteca Opus (necessária para reprodução de áudio)
    def load_opus():
        """Tenta carregar a biblioteca Opus necessária para reprodução de áudio"""
        try:
            if not discord.opus.is_loaded():
                opus_paths = [
                    '/usr/lib/x86_64-linux-gnu/opus.so.0',
                    '/usr/lib/x86_64-linux-gnu/libopus.so.0',
                    '/usr/lib/libopus.so.0',
                    '/usr/local/lib/libopus.so.0',
                    '/usr/local/lib/libopus.so',
                ]
                
                for path in opus_paths:
                    try:
                        discord.opus.load_opus(path)
                        if discord.opus.is_loaded():
                            logger.info(f"Biblioteca Opus carregada com sucesso de {path}")
                            break
                    except (OSError, TypeError):
                        continue
                
                if not discord.opus.is_loaded():
                    logger.warning("Não foi possível carregar a biblioteca Opus. A reprodução de áudio pode não funcionar corretamente.")
            else:
                logger.info("Biblioteca Opus já está carregada")
        except Exception as e:
            logger.error(f"Erro ao carregar a biblioteca Opus: {str(e)}")
    
    # Carregamento de todas as extensões (cogs) para o bot
    async def load_cogs(bot):
        """Carrega todas as extensões (cogs) para o bot"""
        # Carregar os cogs
        cogs = [
            'cogs.activation',
            'cogs.player',
            'cogs.storage',
            'cogs.editor',
            'cogs.ui'
        ]
        
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                logger.info(f"Cog {cog} carregado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao carregar cog {cog}: {str(e)}")
    
    # Função principal para inicializar o bot
    def bot_main():
        """Inicializa e configura o bot Discord"""
        # Garantir que os diretórios necessários existem
        ensure_directories_exist()
        
        # Carregar biblioteca Opus
        load_opus()
        
        # Configurar intents do bot
        intents = Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.reactions = True
        
        # Criar a instância do bot
        bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
        
        # Evento disparado quando o bot está pronto e conectado
        @bot.event
        async def on_ready():
            """Evento disparado quando o bot está pronto e conectado"""
            logger.info(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
            logger.info(f"Bot conectado a {len(bot.guilds)} servidores:")
            for guild in bot.guilds:
                logger.info(f"- {guild.name} (ID: {guild.id})")
            
            # Carregar todos os cogs
            await load_cogs(bot)
            
            # Status personalizado
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!ajuda para comandos"
            ))
        
        # Evento disparado quando o bot desconecta do Discord
        @bot.event
        async def on_disconnect():
            """Registra quando o bot desconecta do Discord"""
            logger.warning("Bot desconectado do Discord")
        
        # Evento disparado quando o bot reconecta ao Discord após uma desconexão
        @bot.event
        async def on_resumed():
            """Registra quando o bot reconecta ao Discord após uma desconexão"""
            logger.info("Bot reconectado ao Discord")
        
        # Comando de ajuda personalizado
        @bot.command(name="ajuda", aliases=["help", "comandos", "commands"])
        async def help_command(ctx, comando=None):
            """Exibe informações de ajuda sobre os comandos do bot"""
            if comando is None:
                embed = discord.Embed(
                    title="Comandos Disponíveis",
                    description="Aqui estão os comandos disponíveis. Use `!ajuda <comando>` para mais detalhes sobre um comando específico.",
                    color=discord.Color.blue()
                )
                
                # Obter o cog de ativação para acessar a duração configurada
                activation_cog = bot.get_cog('Activation')
                duracao_texto = "período configurado"
                if activation_cog:
                    duracao_texto = activation_cog.get_duration_display_text()
                
                # Comandos de ativação
                embed.add_field(
                    name="🔌 Ativação",
                    value=f"`!ativar` - Ativa o bot por {duracao_texto}\n`!desativar` - Desativa o bot\n`!status` - Verifica o status do bot\n`!definir_duracao <horas>` - Define a duração da ativação (administradores)",
                    inline=False
                )
                
                # Comandos de reprodução
                embed.add_field(
                    name="🔊 Reprodução",
                    value="`!tocar <nome>` - Toca um áudio\n`!pausar` - Pausa o áudio atual\n`!continuar` - Continua o áudio pausado\n`!parar` - Para a reprodução\n`!pular` - Pula para o próximo áudio\n`!fila` - Mostra a fila de reprodução\n`!limpar` - Limpa a fila\n`!loop` - Ativa/desativa repetição\n`!embaralhar` - Embaralha a fila\n`!adicionar <nomes>` - Adiciona áudios à fila\n`!remover <posição>` - Remove um áudio da fila\n`!tocando` - Mostra o que está tocando",
                    inline=False
                )
                
                # Comandos de gerenciamento
                embed.add_field(
                    name="📁 Gerenciamento",
                    value="`!listar` - Lista todos os áudios\n`!enviar` - Faz upload de um áudio\n`!renomear <antigo> <novo>` - Renomeia um áudio\n`!emoji <nome> <emoji>` - Associa um emoji a um áudio\n`!deletar <nome>` - Remove um áudio",
                    inline=False
                )
                
                # Comandos de edição
                embed.add_field(
                    name="✂️ Edição",
                    value="`!cortar <nome> <inicio> <fim>` - Corta um áudio\n`!inverter <nome>` - Inverte um áudio\n`!velocidade <nome> <fator>` - Altera a velocidade",
                    inline=False
                )
                
                # Comandos de UI
                embed.add_field(
                    name="🖼️ Interface",
                    value="`!menu` - Mostra menu interativo\n`!carrossel` - Mostra carrossel de áudios",
                    inline=False
                )
                
                embed.set_footer(text="Desenvolvido para o servidor rivoTRIO")
                
                await ctx.send(embed=embed)
            else:
                # Informações detalhadas sobre comandos específicos
                comando = comando.lower()
                
                if comando in ["ativar", "activate"]:
                    # Obter o cog de ativação para acessar a duração configurada
                    activation_cog = bot.get_cog('Activation')
                    duracao_texto = "tempo configurado"
                    if activation_cog:
                        duracao_texto = activation_cog.get_duration_display_text()
                    
                    embed = discord.Embed(
                        title="Comando: !ativar",
                        description=f"Ativa o bot por um período de {duracao_texto}.",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Uso", value="`!ativar`", inline=False)
                    embed.add_field(
                        name="Descrição", 
                        value=f"Quando ativado, o bot responderá a comandos por {duracao_texto}. Após esse período, o bot será desativado automaticamente.", 
                        inline=False
                    )
                    
                elif comando in ["desativar", "deactivate"]:
                    embed = discord.Embed(
                        title="Comando: !desativar",
                        description="Desativa o bot manualmente.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Uso", value="`!desativar`", inline=False)
                    embed.add_field(name="Descrição", value="Desativa o bot manualmente antes do período de ativação terminar.", inline=False)
                    
                elif comando in ["status"]:
                    embed = discord.Embed(
                        title="Comando: !status",
                        description="Verifica o status atual do bot.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Uso", value="`!status`", inline=False)
                    embed.add_field(name="Descrição", value="Mostra se o bot está ativo ou inativo e, se estiver ativo, quanto tempo resta.", inline=False)
                    
                elif comando in ["tocar", "play"]:
                    embed = discord.Embed(
                        title="Comando: !tocar",
                        description="Reproduz um arquivo de áudio pelo nome.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Uso", value="`!tocar <nome_do_audio>`", inline=False)
                    embed.add_field(name="Descrição", value="Reproduz o áudio especificado ou o adiciona à fila se algo já estiver tocando.", inline=False)
                    embed.add_field(name="Exemplo", value="`!tocar meu_audio`", inline=False)
                    
                elif comando in ["listar", "list"]:
                    embed = discord.Embed(
                        title="Comando: !listar",
                        description="Lista todos os áudios disponíveis.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Uso", value="`!listar`", inline=False)
                    embed.add_field(name="Descrição", value="Mostra uma lista de todos os áudios disponíveis para reprodução.", inline=False)
                
                elif comando in ["definir_duracao", "definirduracao", "set_duration"]:
                    embed = discord.Embed(
                        title="Comando: !definir_duracao",
                        description="Define a duração da ativação do bot.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Uso", value="`!definir_duracao <horas>`", inline=False)
                    embed.add_field(name="Descrição", value="Define o tempo que o bot permanecerá ativo ao ser ativado com !ativar. A duração deve ser um número inteiro de horas entre 1 e 12.", inline=False)
                    embed.add_field(name="Permissão", value="Este comando só pode ser usado por administradores do servidor.", inline=False)
                    embed.add_field(name="Exemplo", value="`!definir_duracao 3` - Define a duração para 3 horas", inline=False)
                    
                else:
                    embed = discord.Embed(
                        title="Comando não encontrado",
                        description=f"O comando `{comando}` não foi encontrado. Use `!ajuda` para ver a lista de comandos disponíveis.",
                        color=discord.Color.red()
                    )
                
                await ctx.send(embed=embed)
        
        # Gerenciamento de erros durante a execução de comandos
        @bot.event
        async def on_command_error(ctx, error):
            """Gerencia erros que ocorrem durante a execução de comandos"""
            if isinstance(error, commands.CommandNotFound):
                await ctx.send(f"Comando não encontrado. Use `!ajuda` para ver os comandos disponíveis.")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"Argumentos insuficientes para o comando. Use `!ajuda {ctx.command.name}` para mais informações.")
            elif isinstance(error, commands.BadArgument):
                await ctx.send(f"Argumento inválido. Use `!ajuda {ctx.command.name}` para mais informações.")
            elif isinstance(error, commands.CheckFailure):
                if hasattr(ctx.command, 'name') and ctx.command.name != 'ativar' and ctx.command.name != 'status':
                    # Obter o cog de ativação para acessar a duração configurada
                    activation_cog = bot.get_cog('Activation')
                    duracao_texto = "tempo configurado"
                    if activation_cog:
                        duracao_texto = activation_cog.get_duration_display_text()
                    
                    await ctx.send(f"O bot está desativado. Use `!ativar` para ativá-lo por {duracao_texto}.")
                else:
                    await ctx.send("Você não tem permissão para usar este comando.")
            else:
                logger.error(f"Erro não tratado: {error}")
                await ctx.send(f"Ocorreu um erro ao processar o comando: {error}")
        
        # Iniciar o bot com o token do Discord
        token = os.getenv('DISCORD_TOKEN')
        if token:
            bot.run(token, log_handler=None)
        else:
            logger.critical("Token do Discord não encontrado. Verifique o arquivo .env")
            print("Token do Discord não encontrado. Verifique o arquivo .env")
    
    # Executar o bot
    bot_main()