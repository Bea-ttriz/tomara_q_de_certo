# Como hospedar o Bot de Áudios no Heroku

Este guia fornece instruções detalhadas para hospedar o Bot de Áudios no Heroku, permitindo que ele fique online 24/7.

## Pré-requisitos

1. Uma conta no [Heroku](https://heroku.com) (o plano gratuito foi descontinuado, mas o plano básico tem preço acessível)
2. [Git](https://git-scm.com/) instalado em seu computador
3. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalada
4. Token do seu bot Discord

## Passos para implantação

### 1. Clone o repositório

```bash
git clone URL_DO_SEU_REPOSITORIO
cd nome-da-pasta
```

### 2. Faça login no Heroku via CLI

```bash
heroku login
```

### 3. Crie um novo aplicativo no Heroku

```bash
heroku create nome-do-seu-bot
```

### 4. Adicione buildpacks necessários

O bot precisa do Python e do FFmpeg para funcionar corretamente:

```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
```

### 5. Configure as variáveis de ambiente

Configure o token do seu bot Discord:

```bash
heroku config:set DISCORD_TOKEN=seu_token_do_discord_aqui
```

### 6. Implante o código no Heroku

```bash
git push heroku main
```

### 7. Verifique se os arquivos Procfile e runtime.txt estão corretos

- **Procfile** (já incluído no projeto):
  ```
  worker: python main.py
  web: gunicorn --bind 0.0.0.0:$PORT --reuse-port --reload app:app
  ```

- **runtime.txt** (já incluído no projeto):
  ```
  python-3.11.7
  ```

### 8. Ative o worker para o bot Discord

```bash
heroku ps:scale worker=1
```

### 9. Verifique os logs para garantir que tudo está funcionando

```bash
heroku logs --tail
```

## Estrutura de diretórios

Certifique-se de que a estrutura de diretórios do projeto está correta quando você implantá-lo:

```
/
├── audios/
│   ├── originais/
│   ├── editados/
│   └── audios_db.json
├── cogs/
│   ├── activation.py
│   ├── editor.py
│   ├── player.py
│   ├── storage.py
│   └── ui.py
├── templates/
├── static/
├── main.py
├── app.py
├── utils.py
├── Procfile
├── runtime.txt
└── README.md
```

## Solução de problemas comuns

### O bot não conecta após a implantação

- Verifique se o worker está ativo: `heroku ps`
- Verifique os logs: `heroku logs --tail`
- Verifique se o token do Discord está configurado corretamente

### Erro de "H14 - No web processes running"

Este é normal se você estiver usando apenas o worker. O Heroku espera um processo web, mas nosso bot usa o processo worker.

### Os áudios não são reproduzidos

- Verifique se o FFmpeg foi instalado corretamente
- Verifique se as pastas de áudio existem e têm as permissões corretas

## Como transferir seus áudios

Para transferir seus áudios do Replit para o Heroku:

1. Faça backup da pasta `audios/` e do arquivo `audios/audios_db.json`
2. Clone seu repositório localmente
3. Adicione os arquivos de áudio ao repositório local
4. Faça commit e push para o Heroku

## Manutenção contínua

O Heroku reinicia os dynos (servidores) periodicamente. O bot foi projetado para lidar com isso e reconectar automaticamente.

Para atualizações futuras:

1. Faça as alterações localmente
2. Teste o bot
3. Faça commit das alterações
4. Implante com `git push heroku main`

## Recursos adicionais

- [Documentação do Heroku para Python](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Guia de implantação do Discord.py](https://discordpy.readthedocs.io/en/stable/deploying.html)
- [Suporte FFmpeg no Heroku](https://elements.heroku.com/buildpacks/jonathanong/heroku-buildpack-ffmpeg-latest)
