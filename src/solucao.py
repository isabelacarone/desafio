import pandas as pd 
import numpy as np

def create_solution(excel_path: str) -> dict:
    # a função recebe o caminho de um arquivo excel e retorna um dicionário com a solução do pcm 

    # lendo o arquivo excel
    # df = data frame 
    os_df = pd.read_excel(excel_path, sheet_name='OS')
    tarefas_df = pd.read_excel(excel_path, sheet_name='Tarefas')
    recursos_df = pd.read_excel(excel_path, sheet_name='Recursos')
    paradas_df = pd.read_excel(excel_path, sheet_name='Paradas')



    tarefas_df = tarefas_df.copy()  # por segurança só 
    tarefas_df['duração da demanda'] = tarefas_df['duração'] * tarefas_df['quantidade']

    # soma hrs por OS e habilidades 
    hora_por_OS_habilidade = tarefas_df.groupby(['OS', 'habilidade'])['duração da demanda'].sum().reset_index()
    print(hora_por_OS_habilidade)
    
    return {}


if __name__ == "__main__":
    caminho_arquivo = r"C:\Users\isaca\Desktop\desafio\data\backlog_desafio_500.xlsx"
    create_solution(caminho_arquivo)