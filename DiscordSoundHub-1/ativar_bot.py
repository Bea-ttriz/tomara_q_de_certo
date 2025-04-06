#!/usr/bin/env python3
"""
Script autônomo SOMENTE para ativar o bot Discord sem precisar usar o comando !ativar
"""

import os
import json
import logging
import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Função principal
def ativar_bot_manualmente():
    """Ativa o bot manualmente, definindo seu status como ativo pelo tempo configurado."""
    # Caminho para o arquivo de status e configurações
    status_dir = Path('cogs')
    status_file = status_dir / "activation_status.json"
    settings_file = status_dir / "activation_settings.json"
    
    # Verificar se o diretório existe
    if not status_dir.exists():
        logger.info(f"Criando diretório {status_dir}")
        status_dir.mkdir(parents=True, exist_ok=True)
    
    # Carregar a duração configurada (padrão: 2 horas)
    activation_duration = 7200  # 2 horas em segundos (padrão)
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                if 'duration' in settings:
                    activation_duration = settings['duration']
                    logger.info(f"Carregada duração personalizada: {activation_duration} segundos")
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
    
    # Converter segundos para horas para cálculo
    hours = activation_duration / 3600
    
    # Calcular tempo de ativação a partir de agora
    now = datetime.datetime.now()
    expiration_time = now + datetime.timedelta(seconds=activation_duration)
    
    # Criar ou atualizar o arquivo de status
    status_data = {
        "is_active": True,
        "activated_by": "Ativação Manual",
        "activation_time": now.isoformat(),
        "expiration_time": expiration_time.isoformat()
    }
    
    # Salvar o status no arquivo
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=4)
    
    # Informar sobre o sucesso da operação
    logger.info(f"Bot ativado manualmente até {expiration_time.strftime('%H:%M:%S')}")
    
    # Calcular a duração em horas para exibição
    horas = round(activation_duration / 3600)
    print(f"\n✅ Bot ativado com sucesso!")
    print(f"⏱️ Duração da ativação: {horas} hora{'s' if horas != 1 else ''}")
    print(f"⏰ O bot permanecerá ativo até: {expiration_time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    ativar_bot_manualmente()