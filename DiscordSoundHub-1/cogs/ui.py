import discord
from discord.ext import commands
import asyncio
import logging
import database
import utils
from discord.ui import Button, View, Select

class ShareButton(Button):
    def __init__(self, audio, cog):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="Compartilhar",
            emoji="🔗"
        )
        self.audio = audio
        self.cog = cog
    
    async def callback(self, interaction):
        # Criar um embed com informações sobre o áudio e como compartilhá-lo
        embed = discord.Embed(
            title=f"🔗 Compartilhar: {self.audio['nome']}",
            description=f"Compartilhe este áudio com outros membros do servidor!",
            color=discord.Color.green()
        )
        
        # Adicionar informações do áudio
        embed.add_field(name="Nome", value=self.audio['nome'], inline=True)
        embed.add_field(name="Tipo", value=self.audio['tipo'].capitalize(), inline=True)
        
        if self.audio.get('duracao'):
            embed.add_field(
                name="Duração",
                value=utils.format_duration(self.audio['duracao']),
                inline=True
            )
        
        # Adicionar emoji se existir
        if self.audio.get('emoji') and len(self.audio.get('emoji').strip()) > 0:
            embed.add_field(name="Emoji", value=self.audio['emoji'], inline=True)
        
        # Adicionar instruções para usar
        embed.add_field(
            name="Como usar",
            value=f"📋 Copie o comando abaixo para tocar este áudio:\n```!tocar {self.audio['nome']}```",
            inline=False
        )
        
        # Adicionar dica para compartilhar
        embed.set_footer(text=f"Clique no botão abaixo para enviar este áudio para o canal atual.")
        
        # Criar botão para compartilhar no canal atual
        send_button = Button(
            style=discord.ButtonStyle.primary,
            label="Enviar para este canal",
            emoji="📢"
        )
        
        # Definir callback para o botão de envio
        async def send_to_channel(interaction):
            # Criar um embed simplificado para compartilhar no canal
            share_embed = discord.Embed(
                title=f"{self.audio.get('emoji', '🎵')} {self.audio['nome']}",
                description=f"Áudio compartilhado por {interaction.user.display_name}",
                color=discord.Color.blue()
            )
            
            if self.audio.get('duracao'):
                share_embed.add_field(
                    name="Duração",
                    value=utils.format_duration(self.audio['duracao']),
                    inline=True
                )
            
            share_embed.add_field(
                name="Comando",
                value=f"`!tocar {self.audio['nome']}`",
                inline=True
            )
            
            # Criar botão para tocar diretamente
            play_button = Button(
                style=discord.ButtonStyle.success,
                label="Tocar agora",
                emoji="▶️",
                custom_id=f"play_{self.audio['nome']}"
            )
            
            # View para o botão de tocar
            view = View(timeout=600)  # 10 minutos de timeout
            view.add_item(play_button)
            
            # Enviar mensagem no canal
            await interaction.response.send_message(embed=share_embed, view=view)
        
        # Configurar o callback do botão
        send_button.callback = send_to_channel
        
        # Criar view e adicionar o botão
        view = View(timeout=180)  # 3 minutos de timeout
        view.add_item(send_button)
        
        # Responder à interação original
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class AudioButton(Button):
    def __init__(self, audio, cog):
        emoji_value = None
        if audio.get('emoji') and len(audio.get('emoji').strip()) > 0:
            try:
                # Verificar se o emoji é válido
                emoji_value = audio.get('emoji').strip()
                # Se o emoji for uma string vazia ou None, não usaremos emoji
                if not emoji_value:
                    emoji_value = None
            except Exception:
                emoji_value = None
        
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=audio['nome'],
            emoji=emoji_value if emoji_value else "🎵"
        )
        self.audio = audio
        self.cog = cog
    
    async def callback(self, interaction):
        # Criar um contexto fake para usar as funções existentes
        ctx = type('obj', (object,), {
            'guild': interaction.guild,
            'send': interaction.channel.send,
            'author': interaction.user
        })
        
        # Obter o cog de player
        player_cog = self.cog.bot.get_cog('Player')
        if player_cog:
            await player_cog.play_audio(ctx, audio_name=self.audio['nome'])
            await interaction.response.defer()
        else:
            await interaction.response.send_message("❌ Sistema de player não disponível.", ephemeral=True)

class AudioSelect(Select):
    def __init__(self, audios, cog):
        options = []
        
        # Agrupar por tipo
        originals = [a for a in audios if a['tipo'] == 'original']
        edited = [a for a in audios if a['tipo'] == 'editado']
        
        # Limitar a 25 opções (limite do Discord)
        all_audios = (originals + edited)[:25]
        
        for audio in all_audios:
            emoji_value = None
            if audio.get('emoji') and len(audio.get('emoji').strip()) > 0:
                try:
                    # Verificar se o emoji é válido
                    emoji_value = audio.get('emoji').strip()
                    # Se o emoji for uma string vazia ou None, não usaremos emoji
                    if not emoji_value:
                        emoji_value = None
                except Exception:
                    emoji_value = None
            
            option = discord.SelectOption(
                label=audio['nome'][:100],  # Discord limita a 100 caracteres
                value=audio['nome'],
                description=f"Tipo: {audio['tipo'].capitalize()}"
            )
            
            # Apenas adicionar emoji se for válido
            if emoji_value:
                try:
                    option.emoji = emoji_value
                except Exception:
                    pass  # Ignorar emojis inválidos
            
            options.append(option)
        
        super().__init__(
            placeholder="Selecione um áudio para tocar...",
            options=options
        )
        self.cog = cog
    
    async def callback(self, interaction):
        selected_audio_name = self.values[0]
        
        # Criar um contexto fake para usar as funções existentes
        ctx = type('obj', (object,), {
            'guild': interaction.guild,
            'send': interaction.channel.send,
            'author': interaction.user
        })
        
        # Obter o cog de player
        player_cog = self.cog.bot.get_cog('Player')
        if player_cog:
            await player_cog.play_audio(ctx, audio_name=selected_audio_name)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("❌ Sistema de player não disponível.", ephemeral=True)

class UI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('discord_bot.ui')
        # Registrar listener para interações com botões de ID personalizado
        bot.add_listener(self.on_interaction, name='on_interaction')
    
    @commands.command(name="listar")
    async def list_audios(self, ctx):
        """Mostra todos os áudios disponíveis em um menu interativo"""
        audios = database.get_all_audios()
        
        if not audios:
            await ctx.send("📂 Não há áudios cadastrados. Use !upload para adicionar áudios.")
            return
        
        # Criar embed informativo
        embed = discord.Embed(
            title="🎵 Biblioteca de Áudios - rivoTRIO",
            description=f"**{len(audios)}** áudios disponíveis\n\nEscolha uma das opções abaixo para explorar os áudios.",
            color=discord.Color.blue()
        )
        
        # Contar por tipo
        originals_count = sum(1 for a in audios if a['tipo'] == 'original')
        edited_count = sum(1 for a in audios if a['tipo'] == 'editado')
        
        embed.add_field(name="📁 Originais", value=str(originals_count), inline=True)
        embed.add_field(name="✂️ Editados", value=str(edited_count), inline=True)
        
        # Criar view com opções
        view = View(timeout=180)
        
        # Botão para ver carrossel com todos os áudios
        carousel_btn = Button(
            style=discord.ButtonStyle.primary,
            label="Carrossel de Áudios",
            emoji="🎵"
        )
        carousel_btn.callback = lambda i: self.carousel(ctx)
        
        # Botão para listar áudios originais
        originals_btn = Button(
            style=discord.ButtonStyle.secondary,
            label="Ver Originais",
            emoji="📁"
        )
        
        # Botão para listar áudios editados
        edited_btn = Button(
            style=discord.ButtonStyle.secondary,
            label="Ver Editados",
            emoji="✂️"
        )
        
        # Botão para listar todos os áudios
        all_btn = Button(
            style=discord.ButtonStyle.secondary,
            label="Ver Todos",
            emoji="🔍"
        )
        
        async def show_originals(interaction):
            originals = [a for a in audios if a['tipo'] == 'original']
            if not originals:
                await interaction.response.send_message("📂 Não há áudios originais cadastrados.", ephemeral=True)
                return
            
            embed = self.create_audio_list_embed("Áudios Originais", originals)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        async def show_edited(interaction):
            edited = [a for a in audios if a['tipo'] == 'editado']
            if not edited:
                await interaction.response.send_message("📂 Não há áudios editados cadastrados.", ephemeral=True)
                return
            
            embed = self.create_audio_list_embed("Áudios Editados", edited)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        async def show_all(interaction):
            embed = self.create_audio_list_embed("Todos os Áudios", audios)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        originals_btn.callback = show_originals
        edited_btn.callback = show_edited
        all_btn.callback = show_all
        
        # Adicionar botões à view
        view.add_item(carousel_btn)
        view.add_item(originals_btn)
        view.add_item(edited_btn)
        view.add_item(all_btn)
        
        embed.set_footer(text="Use !carousel para abrir diretamente o carrossel de áudios | !ajuda para ver todos os comandos")
        await ctx.send(embed=embed, view=view)
    
    def create_audio_list_embed(self, title, audios):
        """Cria um embed com uma lista de áudios"""
        embed = discord.Embed(
            title=f"📋 {title}",
            description=f"**{len(audios)}** áudios encontrados",
            color=discord.Color.blue()
        )
        
        # Agrupar por tipo se for lista completa
        if title == "Todos os Áudios":
            originals = [a for a in audios if a['tipo'] == 'original']
            edited = [a for a in audios if a['tipo'] == 'editado']
            
            if originals:
                safe_emojis = []
                for a in originals[:10]:
                    emoji = "🎵"
                    if a.get('emoji') and len(a.get('emoji').strip()) > 0:
                        emoji = a.get('emoji').strip()
                    safe_emojis.append(f"{emoji} `{a['nome']}`")
                    
                originals_text = "\n".join(safe_emojis)
                if len(originals) > 10:
                    originals_text += f"\n... e mais {len(originals) - 10} áudios."
                embed.add_field(name="📁 Originais", value=originals_text, inline=False)
            
            if edited:
                safe_emojis = []
                for a in edited[:10]:
                    emoji = "✂️" 
                    if a.get('emoji') and len(a.get('emoji').strip()) > 0:
                        emoji = a.get('emoji').strip()
                    safe_emojis.append(f"{emoji} `{a['nome']}`")
                    
                edited_text = "\n".join(safe_emojis)
                if len(edited) > 10:
                    edited_text += f"\n... e mais {len(edited) - 10} áudios."
                embed.add_field(name="✂️ Editados", value=edited_text, inline=False)
        else:
            # Lista simples para um tipo específico
            audio_list = []
            for a in audios[:20]:
                emoji = "🎵" 
                if a.get('emoji') and len(a.get('emoji').strip()) > 0:
                    emoji = a.get('emoji').strip()
                audio_list.append(f"{emoji} `{a['nome']}`")
                
            if len(audios) > 20:
                audio_list.append(f"... e mais {len(audios) - 20} áudios.")
            
            embed.description += "\n\n" + "\n".join(audio_list)
        
        embed.set_footer(text="Use !tocar <nome> para reproduzir um áudio")
        return embed
    
    @commands.command(name="carousel")
    async def carousel(self, ctx):
        """Mostra um carrossel interativo de áudios"""
        audios = database.get_all_audios()
        
        if not audios:
            await ctx.send("📂 Não há áudios cadastrados. Use !upload para adicionar áudios.")
            return
        
        # Dividir em páginas de 3 áudios (para permitir 6 botões por página: 3 botões de reprodução + 3 de compartilhamento)
        page_size = 3
        pages = [audios[i:i+page_size] for i in range(0, len(audios), page_size)]
        current_page = 0
        
        # Função para atualizar o carrossel
        async def update_carousel(page_num, interaction=None):
            nonlocal current_page
            current_page = page_num
            
            # Atualizar view e embed
            new_view = self.create_carousel_view(pages[page_num], page_num, len(pages), update_carousel)
            new_embed = self.create_carousel_embed(pages[page_num], page_num, len(pages), audios)
            
            if interaction:
                await interaction.response.edit_message(embed=new_embed, view=new_view)
            else:
                await message.edit(embed=new_embed, view=new_view)
        
        # Criar view inicial
        view = self.create_carousel_view(pages[current_page], current_page, len(pages), update_carousel)
        
        # Mensagem inicial
        embed = self.create_carousel_embed(pages[current_page], current_page, len(pages), audios)
        message = await ctx.send(embed=embed, view=view)
    
    def create_carousel_view(self, page_audios, page_num, total_pages, update_callback=None):
        """Cria uma view para o carrossel de áudios"""
        view = View(timeout=180)
        
        # Adicionar botões para cada áudio da página
        for audio in page_audios:
            try:
                # Adicionar botão para reproduzir o áudio
                button = AudioButton(audio, self)
                view.add_item(button)
                
                # Adicionar botão para compartilhar o áudio
                share_button = ShareButton(audio, self)
                view.add_item(share_button)
            except Exception as e:
                self.logger.error(f"Erro ao criar botão para áudio {audio['nome']}: {e}")
                # Continuar com os próximos botões mesmo se um falhar
        
        # Adicionar botões de navegação se houver mais de uma página
        if total_pages > 1:
            nav_row = []
            
            # Botão Anterior
            prev_button = Button(
                style=discord.ButtonStyle.secondary,
                emoji="⬅️",
                disabled=(page_num == 0)
            )
            if update_callback:
                prev_button.callback = lambda i: update_callback(page_num - 1, i)
            nav_row.append(prev_button)
            
            # Indicador de página
            page_indicator = Button(
                style=discord.ButtonStyle.secondary,
                label=f"Página {page_num + 1}/{total_pages}",
                disabled=True
            )
            nav_row.append(page_indicator)
            
            # Botão Próximo
            next_button = Button(
                style=discord.ButtonStyle.secondary,
                emoji="➡️",
                disabled=(page_num == total_pages - 1)
            )
            if update_callback:
                next_button.callback = lambda i: update_callback(page_num + 1, i)
            nav_row.append(next_button)
            
            # Adicionar botões de navegação
            for button in nav_row:
                view.add_item(button)
        
        return view
    
    def create_carousel_embed(self, page_audios, page_num, total_pages, all_audios):
        """Cria um embed para o carrossel de áudios"""
        embed = discord.Embed(
            title="🎵 Carrossel de Áudios - rivoTRIO",
            description=f"Clique nos botões abaixo para reproduzir os áudios. Página {page_num + 1} de {total_pages}.",
            color=discord.Color.blue()
        )
        
        # Adicionar informações sobre navegação
        total_audios = len(all_audios)  # Obter o total real de áudios
        page_size = 3  # Tamanho da página definido anteriormente
        current_range = f"{page_num * page_size + 1}-{min((page_num + 1) * page_size, total_audios)}"
        embed.add_field(
            name="📊 Navegação",
            value=f"Mostrando áudios {current_range} de {total_audios}",
            inline=False
        )
        
        # Listagem dos áudios na página atual
        for i, audio in enumerate(page_audios):
            emoji = "🎵"
            if audio.get('emoji') and len(audio.get('emoji').strip()) > 0:
                emoji = audio.get('emoji').strip()
                
            duration = utils.format_duration(audio.get('duracao', 0))
            embed.add_field(
                name=f"{i+1+page_num*3}. {emoji} {audio['nome']}",
                value=f"Tipo: {audio['tipo'].capitalize()} • Duração: {duration}",
                inline=False
            )
        
        # Adicionar dica sobre como usar os botões
        tip = "▶️ = Reproduzir áudio | 🔗 = Compartilhar"
        if total_pages > 1:
            tip += " | ⬅️ ➡️ = Navegar entre páginas"
            
        embed.set_footer(text=tip)
        return embed
    
    async def on_interaction(self, interaction):
        """Gerencia interações com componentes personalizados"""
        # Verificar se é uma interação de componente (botão, select, etc)
        if not interaction.data or 'custom_id' not in interaction.data:
            return
            
        custom_id = interaction.data['custom_id']
        
        # Verificar se é um botão de reprodução rápida com custom_id play_NOME_DO_AUDIO
        if custom_id.startswith('play_'):
            # Extrair o nome do áudio da custom_id
            audio_name = custom_id[5:]  # Remove 'play_' do início
            
            # Verificar se o áudio existe
            audio = database.get_audio_by_name(audio_name)
            if not audio:
                await interaction.response.send_message(
                    f"❌ Áudio `{audio_name}` não encontrado.", 
                    ephemeral=True
                )
                return
                
            # Criar um contexto fake para usar as funções existentes
            ctx = type('obj', (object,), {
                'guild': interaction.guild,
                'send': interaction.channel.send,
                'author': interaction.user
            })
            
            # Reproduzir o áudio
            player_cog = self.bot.get_cog('Player')
            if player_cog:
                try:
                    # Adicionar verificação de ativação do bot
                    activation_cog = self.bot.get_cog('Activation')
                    if activation_cog and not activation_cog.is_bot_active():
                        # Bot está inativo, precisamos ativá-lo primeiro
                        await activation_cog.activate_bot(ctx)
                        # Adicionar um pequeno delay para garantir que o bot esteja ativo
                        await asyncio.sleep(1)
                    
                    # Tocar o áudio
                    await player_cog.play_audio(ctx, audio_name=audio_name)
                    await interaction.response.send_message(
                        f"▶️ Tocando `{audio_name}`...",
                        ephemeral=True
                    )
                except Exception as e:
                    self.logger.error(f"Erro ao reproduzir áudio via botão: {e}")
                    await interaction.response.send_message(
                        f"❌ Erro ao reproduzir áudio: {e}",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "❌ Sistema de player não disponível.",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(UI(bot))