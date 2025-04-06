# Bot de Áudios para Discord - rivoTRIO

Bot Discord para gerenciamento e reprodução de áudios personalizado para o servidor "rivoTRIO".

## Funcionalidades

O bot oferece diversas funcionalidades para gerenciar e reproduzir áudios no servidor Discord:

### 🎵 Comandos de Reprodução

- `!tocar <arquivo>` - Reproduz um arquivo de áudio
- `!pausar` - Pausa a reprodução atual
- `!continuar` - Continua uma reprodução pausada
- `!parar` - Para a reprodução e desconecta
- `!listar` - Mostra todos os áudios disponíveis em um menu interativo
- `!carousel` - Mostra um carrossel interativo de áudios
- `!tocando` - Mostra o que está tocando atualmente

### 📂 Comandos de Armazenamento

- `!upload` - Faz upload de um arquivo de áudio (anexe o arquivo ao comando)
- `!renomear <arquivo> <novo_nome>` - Renomeia um arquivo de áudio
- `!emoji <arquivo> <emoji>` - Associa um emoji ao arquivo
- `!excluir <arquivo>` - Remove um arquivo do sistema

### ✂️ Comandos de Edição

- `!cortar <arquivo> <inicio> <fim>` - Corta um arquivo de áudio (formato de tempo: HH:MM:SS)
- `!inverter <arquivo>` - Inverte um arquivo de áudio
- `!velocidade <arquivo> <fator>` - Altera a velocidade (0.5=lento, 2.0=rápido)

### 🔄 Sistema de Ativação

- `!ativar` - Ativa o bot pelo período configurado (agora 12 horas)
- `!desativar` - Desativa o bot manualmente
- `!status` - Verifica o status atual do bot (ativo/inativo)
- `!definir_duracao <horas>` - Define a duração da ativação (1-12 horas)

### Outros Comandos

- `!ajuda` - Exibe informações de ajuda sobre os comandos do bot

## Recursos Especiais

- **Reprodução por Emoji**: Você pode clicar em um emoji associado a um áudio para reproduzi-lo automaticamente
- **Interface Interativa**: O comando `!listar` mostra um menu dropdown com todos os áudios disponíveis
- **Carrossel de Áudios**: O comando `!carousel` mostra um carrossel interativo com botões para cada áudio

## Estrutura do Projeto

- `audios/originais` - Pasta onde são armazenados os áudios originais
- `audios/editados` - Pasta onde são armazenados os áudios editados
- `audios/audios_db.json` - Banco de dados dos áudios

## Requisitos

- Python 3.x
- Bibliotecas: discord.py, pydub, python-dotenv, ffmpeg
- Token do Discord (definido como variável de ambiente DISCORD_TOKEN)

## Como Usar

1. Convide o bot para o seu servidor Discord
2. Use o comando `!ajuda` para ver a lista de comandos disponíveis
3. Faça upload de áudios usando o comando `!upload` (anexe o arquivo ao comando)
4. Use `!listar` ou `!carousel` para ver os áudios disponíveis
5. Reproduza os áudios usando o comando `!tocar <nome>` ou clicando nos botões/emojis

## Hospedagem no Heroku

Este projeto está configurado para ser implantado facilmente no Heroku. Siga estas etapas:

1. **Crie uma conta no Heroku** (se ainda não tiver uma) em [heroku.com](https://heroku.com)

2. **Instale a CLI do Heroku** seguindo as instruções em [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)

3. **Faça login na CLI do Heroku**:
   ```
   heroku login
   ```

4. **Crie um novo app no Heroku**:
   ```
   heroku create nome-do-seu-bot
   ```

5. **Adicione o buildpack do Python**:
   ```
   heroku buildpacks:add heroku/python
   ```

6. **Adicione o buildpack do FFmpeg** (necessário para processamento de áudio):
   ```
   heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
   ```

7. **Configure as variáveis de ambiente**:
   ```
   heroku config:set DISCORD_TOKEN=seu_token_do_discord_aqui
   ```

8. **Implante o app**:
   ```
   git push heroku main
   ```

9. **Ative o worker** (para que o bot fique online):
   ```
   heroku ps:scale worker=1
   ```

10. **Para verificar os logs**:
    ```
    heroku logs --tail
    ```

## Hospedagem em outros serviços

Este projeto pode ser facilmente adaptado para outros serviços de hospedagem como:

1. **Railway** - [railway.app](https://railway.app/)
2. **Oracle Cloud Free Tier** - [oracle.com/cloud/free](https://www.oracle.com/cloud/free/)
3. **Google Cloud Platform** - [cloud.google.com](https://cloud.google.com/)

Todos esses serviços oferecem algum nível de uso gratuito que pode ser suficiente para manter o bot ativo.
