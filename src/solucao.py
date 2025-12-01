import pandas as pd

def extrair_num_do_dia(nome_dia: str) -> int:
    '''
    retira o Dia_ e deixa só o número 'Dia_3' 
    se não der certo retorna False
    '''
    try:
        partes = str(nome_dia).split("_")
        numero = int(partes[-1])
        return numero
    except:
        return False


def create_solution(excel_path: str) -> dict:
    '''
    le o arquivo Excel do desafio e realiza a programação semanal da OS,
    tedno em vista os critérios:
      1 prioridade (Z A B C)
      2 Parada? Sim ou Não
      3 predecessora
      4 disponibilidade de horas por habilidade
    '''

    print(f"Realizando a leitura dos arquivos Excel em: {excel_path}")

    # 1. leitura das abas 

    os_df = pd.read_excel(excel_path, sheet_name="OS")
    tarefas_df = pd.read_excel(excel_path, sheet_name="Tarefas")
    recursos_df = pd.read_excel(excel_path, sheet_name="Recursos")
    paradas_df = pd.read_excel(excel_path, sheet_name="Paradas")

    # 2. calcular demanda_horas por tarefa (Duração * Quantidade) 
    # se mudar o nome da erro por causa do excel 

    tarefas_df = tarefas_df.copy()
    tarefas_df["Demanda_horas"] = tarefas_df["Duração"] * tarefas_df["Quantidade"]

    
    # 3. sum() Demanda_horas por OS e habilidade

    demanda_os_hab_df = tarefas_df.groupby(["OS", "Habilidade"]) ["Demanda_horas"].sum().reset_index()
    
    # criar estrutura de demanda por OS e habilidade
    demanda_por_os = {}

    # uso de lista de tuplas para melhorar a agilidade 
    for linha in demanda_os_hab_df.itertuples():
        os_id = linha.OS
        habilidade = linha.Habilidade
        horas = linha.Demanda_horas

        if os_id not in demanda_por_os:
            demanda_por_os[os_id] = {}

        demanda_por_os[os_id][habilidade] = horas


    # 4. cálculo da duração contínua por OS

    duracao_os = tarefas_df.groupby("OS")["Duração"].sum().reset_index()
    duracao_os = duracao_os.rename(columns={"Duração": "Duracao_continua"})

    os_df = os_df.merge(duracao_os, on="OS", how="left")

  
    # 5. Ordenar por prioridade e duração contínua e transofmrar prioridade em números!!

    prioridade = {"Z": 1, "A": 2, "B": 3, "C": 4}
    os_df["Prioridade_num"] = os_df["Prioridade"].map(prioridade)

    # ordenadas por Prioridade_num e Duracao_continua, respectivamente Z, A, B e C e OS com menor duração 1° 
    os_ordenadas = os_df.sort_values(
        by=["Prioridade_num", "Duracao_continua"], ascending=[True, True]
    )

    # 6. Criar estrutura de capacidade por dia e habilidade
    # dia, habilidade) ==> HH_Disponivel
    
    capacidade = {}

    for linha in recursos_df.itertuples():
        dia = linha.Dia
        habilidade = linha.Habilidade
        hora_disp = linha.HH_Disponivel
        capacidade[(dia, habilidade)] = hora_disp

    # acompanhamento do uso de horas por dia/habilidade
    uso = {}

    # dias disponíveis no backlog
    dias_disponiveis = sorted(recursos_df["Dia"].unique())

    # 7. encontrando os dias de parada
    dias_parada = paradas_df.loc[paradas_df["Parada"] == "Sim", "Dia"].tolist()

    # 8. Loop principal para programar as OS
    
    programacao = {}      # OS ==> Dia
    nao_programadas = []  # OS que não deram para nenhum dia

    for os_linha in os_ordenadas.itertuples():
        os_id = os_linha.OS
        condicao = os_linha.Condição
        predecessora = os_linha.Predecessora

        # 8.1 quanto horas essa OS precisa de cada habilidade?
        horas_p_habilidade = demanda_por_os.get(os_id, {})

        # 8.2 quais dias são possíveis para essa OS?
        if condicao == "Parada":
            dias_possiveis = dias_parada
        else: 
            dias_candidatos = []
            for dia in dias_disponiveis:
                if dia not in dias_parada:
                    dias_candidatos.append(dia)

        # 8.3 se não existe nenhum dia disponível adiciona na lista de não programadas
        if not dias_possiveis:
            nao_programadas.append(os_id)
            continue

        # 8.4 tratar as predecessoras
        dia_minimo = None
        if pd.notna(predecessora):
            dia_predecessora = programacao.get(predecessora)
            
            # se a predecessora não foi programada, não consigo rodar a OS

            if dia_predecessora is None:
                nao_programadas.append(os_id)
                continue
            else:
                dia_minimo = extrair_num_do_dia(dia_predecessora)

            