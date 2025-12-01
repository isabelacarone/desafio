import pandas as pd 
import numpy as np

# ctrl z enter p sair do terminal


def create_solution(excel_path: str) -> dict:
    # a função recebe o caminho de um arquivo excel e retorna um dicionário com a solução do pcm 

    # lendo o arquivo excel
    # df = data frame 
    os_df = pd.read_excel(excel_path, sheet_name='OS')
    tarefas_df = pd.read_excel(excel_path, sheet_name='Tarefas')
    recursos_df = pd.read_excel(excel_path, sheet_name='Recursos')
    paradas_df = pd.read_excel(excel_path, sheet_name='Paradas')


    # 1. quantas horas cada OS precisa de cada habilidade?

    tarefas_df = tarefas_df.copy()  # por segurança
    tarefas_df["Demanda_horas"] = tarefas_df["Duração"] * tarefas_df["Quantidade"]

    # soma horas por OS e por habilidade
    hora_por_OS_habilidade = tarefas_df.groupby(["OS", "Habilidade"])["Demanda_horas"].sum().reset_index()

    print("\nHoras por OS e Habilidade:")
    print(hora_por_OS_habilidade.head(10)) # saída

    # 2. uma OS cabe em 1 dia (8hrs)? -> duração sequencial
    duracao_os = tarefas_df.groupby("OS")["Duração"].sum().reset_index()
    duracao_os.rename(columns={"Duração": "Duracao_continua"}, inplace=True)

    print("\nDuração sequencial por OS:")
    print(duracao_os.head(10)) # saída

    # 3. juntar a duração contínua na tabela de OS
    os_df = os_df.merge(duracao_os, on="OS", how="left")

    print("\nOS com duração contínua:")
    print(os_df[["OS", "Prioridade", "Condição", "Predecessora", "Duracao_continua"]].head(10)) # saída

    # 4. colocando a prioridade como numérica p ordenar as OS 
    prioridades = {"Z": 1, "A": 2, "B": 3, "C": 4, "D": 5}
    os_df["Prioridade_num"] = os_df["Prioridade"].map(prioridades)

    # saída ordenada 
    os_ordenados = os_df.sort_values(by=["Prioridade_num", "Duracao_continua"], ascending=[True, True])
    print("\nOS ordenadas por prioridade e duração contínua:")
    print(os_ordenados[["OS", "Prioridade", "Duracao_continua"]].head(10)) # saída


    return {}

if __name__ == "__main__":
    caminho_arquivo = r"C:\Users\isaca\Desktop\desafio\data\backlog_desafio_500.xlsx"
    create_solution(caminho_arquivo)