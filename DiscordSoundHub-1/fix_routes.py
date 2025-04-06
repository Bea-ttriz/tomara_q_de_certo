#!/usr/bin/env python3

def fix_routes():
    """
    Corrige as rotas no arquivo app.py, substituindo <n> por <name>
    nas definições de rotas para corresponder aos parâmetros das funções.
    """
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Substitui todas as ocorrências de <n> para <name> nas rotas
    content = content.replace('/audio/<n>', '/audio/<name>')
    content = content.replace('/audio/view/<n>', '/audio/view/<name>')
    content = content.replace('/audio/edit/<n>', '/audio/edit/<name>')
    content = content.replace('/audio/delete/<n>', '/audio/delete/<name>')
    
    with open('app.py', 'w') as file:
        file.write(content)
    
    print("Rotas corrigidas com sucesso!")

if __name__ == "__main__":
    fix_routes()