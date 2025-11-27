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

