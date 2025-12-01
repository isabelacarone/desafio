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
    
    # >> 3 sum  Demanda_horas por OS e Habilidades
    ''' quantas horas de cada habilidade essa OS precisa?
        lembrar de usar grouby'''
    
    # demanda por OS e habilidades 
    demanda_OS_habilidade_df = tarefas_df.groupby(['OS_ID', 'Habilidade'])['Demanda_horas'].sum().reset_index()
    
    # estrutura p ver melhor 

    demanda_OS_habilidade_dicionario = {}
    for _, linha in demanda_OS_habilidade_df.iterrows():
        # avaliar uso do iterrows depois 
        os_id = linha['OS_ID']
        habilidade = linha['Habilidade']
        demanda_horas = linha['Demanda_horas']
        
        if os_id not in demanda_OS_habilidade_dicionario:
            demanda_OS_habilidade_dicionario[os_id] = {}
        
        demanda_OS_habilidade_dicionario[os_id][habilidade] = demanda_horas

    # >> 4 calcular a duração contínua por OS
    ''' somar a duração das tarefas, quantas vão dar em 1d?'''
    duracao_continua_por_OS = tarefas_df.groupby('OS_ID')['Duração'].sum().reset_index()
    duracao_continua_por_OS_dict = duracao_continua_por_OS.rename(columns={'Duração': 'Duracao_Continua'}).set_index('OS_ID')['Duracao_continua'].to_dict()

    # >> 5 juntar infos na OS
    os_df = os_df.merge(duracao_continua_por_OS, on='OS_ID', how='left')
    
    # >> 6 colocando as prioridades como nr 
    prioridade = {"Z": 1, "A": 2, "B": 2, "C": 3}
    os_df["Prioridade_num"] = os_df["Prioridade"].map(prioridade)