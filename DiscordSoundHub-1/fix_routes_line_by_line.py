#!/usr/bin/env python3

def fix_routes():
    """
    Corrige as rotas no arquivo app.py, substituindo <n> por <name>
    nas definições de rotas para corresponder aos parâmetros das funções.
    Usa uma abordagem de leitura e escrita linha por linha.
    """
    # Lê as linhas do arquivo
    with open('app.py', 'r') as file:
        lines = file.readlines()
    
    # Faz as substituições linha por linha
    for i, line in enumerate(lines):
        if '@app.route(\'/audio/<n>\')' in line:
            lines[i] = '@app.route(\'/audio/<name>\')\n'
        elif '@app.route(\'/audio/view/<n>\')' in line:
            lines[i] = '@app.route(\'/audio/view/<name>\')\n'
        elif '@app.route(\'/audio/edit/<n>\'' in line:
            lines[i] = '@app.route(\'/audio/edit/<name>\', methods=[\'GET\', \'POST\'])\n'
        elif '@app.route(\'/audio/delete/<n>\'' in line:
            lines[i] = '@app.route(\'/audio/delete/<name>\', methods=[\'POST\'])\n'
    
    # Escreve as linhas modificadas de volta no arquivo
    with open('app.py', 'w') as file:
        file.writelines(lines)
    
    print("Rotas corrigidas com sucesso!")

if __name__ == "__main__":
    fix_routes()