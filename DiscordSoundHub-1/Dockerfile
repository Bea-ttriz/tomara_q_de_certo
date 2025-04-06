FROM python:3.11-slim

# Instalar FFmpeg e outras dependências
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar os arquivos do projeto
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir discord.py pynacl pydub flask flask-sqlalchemy gunicorn python-dotenv cffi psycopg2-binary werkzeug email-validator

# Criar pastas necessárias
RUN mkdir -p audios/originais audios/editados audios/temp

# Comando para iniciar o bot
CMD ["python", "main.py"]