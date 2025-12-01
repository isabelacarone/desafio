import pandas as pd
import numpy as np

def extrair_nr_dias(nome_dia: str) -> int:
    ''' retira o Dia_ e deixa só o numero referente ao dia 
        ex: Dia_15 -> 15
    '''
    try: 
        partes = str(nome_dia).split('_')
        numero = int(partes[-1])
        return numero
    except:
        return 0 



# função pedida create_solution
def create_solution(excel_path: str) -> dict:
    '''realiza a leitura do arquivo excel e cria o dicionario com a solucao
        levando em consideração as regras de:
        - prioridade (z, a, b e c)
        - condição (operando ou parada)
        - capacidade de recursos
        - predecessoras
    '''


    # >> 1 leitura do arquivo excel
    os_df = pd.read_excel(excel_path, sheet_name='OS')
    tarefas_df = pd.read_excel(excel_path, sheet_name='Tarefas')
    recursos_df = pd.read_excel(excel_path, sheet_name='Recursos')
    paradas_df = pd.read_excel(excel_path, sheet_name='Paradas')

    # >> 2 calculo de duração por quantidade POR OS 

    tarefas_df["Demanda_horas"] = tarefas_df["Duração"] * tarefas_df["Quantidade"]
    