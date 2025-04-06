import json
import os
import logging
from pathlib import Path

# Configuração do logger
logger = logging.getLogger('discord_bot.database')

# Caminho do arquivo de database (json)
DB_FILE = 'audios/audios_db.json'

# Estrutura do DB
DB_STRUCTURE = {
    'audios': []  # Lista de objetos de áudio
}

def init_db():
    """Inicializa o banco de dados se não existir"""
    if os.path.exists(DB_FILE):
        logger.info(f"Banco de dados encontrado em {DB_FILE}")
        return
    
    # Garante que o diretório exista
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    # Cria o arquivo de banco de dados com a estrutura inicial
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(DB_STRUCTURE, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Banco de dados inicializado em {DB_FILE}")

def get_all_audios():
    """Retorna todos os áudios cadastrados no sistema"""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
            return db.get('audios', [])
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Erro ao ler banco de dados: {e}")
        return []

def get_audio_by_name(name):
    """Procura um áudio pelo nome"""
    audios = get_all_audios()
    for audio in audios:
        if audio['nome'].lower() == name.lower():
            return audio
    return None

def get_audio_by_emoji(emoji):
    """Procura um áudio pelo emoji associado"""
    audios = get_all_audios()
    for audio in audios:
        if audio.get('emoji') == emoji:
            return audio
    return None

def add_audio(nome, caminho, tipo, emoji=None, duracao=None):
    """Adiciona um novo áudio ao banco de dados"""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Verificar se o áudio já existe
        for audio in db['audios']:
            if audio['nome'].lower() == nome.lower():
                return False, "Um áudio com este nome já existe"
        
        # Criar novo registro de áudio
        novo_audio = {
            'nome': nome,
            'caminho': caminho,
            'tipo': tipo,  # 'original' ou 'editado'
            'emoji': emoji,
            'duracao': duracao
        }
        
        db['audios'].append(novo_audio)
        
        # Salvar no banco de dados
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        
        return True, novo_audio
    
    except Exception as e:
        logger.error(f"Erro ao adicionar áudio: {e}")
        return False, f"Erro ao adicionar áudio: {str(e)}"

def update_audio(nome, updates):
    """Atualiza as informações de um áudio existente"""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        updated = False
        for i, audio in enumerate(db['audios']):
            if audio['nome'].lower() == nome.lower():
                # Atualizar campos
                for key, value in updates.items():
                    db['audios'][i][key] = value
                updated = True
                break
        
        if not updated:
            return False, "Áudio não encontrado"
        
        # Salvar no banco de dados
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        
        return True, "Áudio atualizado com sucesso"
    
    except Exception as e:
        logger.error(f"Erro ao atualizar áudio: {e}")
        return False, f"Erro ao atualizar áudio: {str(e)}"

def remove_audio(nome):
    """Remove um áudio do banco de dados"""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Verificar se o áudio existe
        index_to_remove = None
        for i, audio in enumerate(db['audios']):
            if audio['nome'].lower() == nome.lower():
                index_to_remove = i
                break
        
        if index_to_remove is None:
            return False, "Áudio não encontrado"
        
        # Remover o áudio
        audio_removed = db['audios'].pop(index_to_remove)
        
        # Salvar no banco de dados
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        
        return True, audio_removed
    
    except Exception as e:
        logger.error(f"Erro ao remover áudio: {e}")
        return False, f"Erro ao remover áudio: {str(e)}"
