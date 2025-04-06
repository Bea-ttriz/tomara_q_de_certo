#!/usr/bin/env python3
import os
import logging
from pathlib import Path
import database
import utils
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('web_server')

# Garantir que os diretórios de áudio existam
def ensure_directories_exist():
    Path('audios/originais').mkdir(parents=True, exist_ok=True)
    Path('audios/editados').mkdir(parents=True, exist_ok=True)

def main():
    # Garantir diretórios
    ensure_directories_exist()
    
    # Inicializar banco de dados
    database.init_db()
    
    # Iniciar o servidor web
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    print("Iniciando o servidor web para gerenciamento de áudios no endereço http://0.0.0.0:5000")
    main()