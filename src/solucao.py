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

def tem_predecessora(predecessora) -> bool:
    '''
    retorna True se REALMENTE existe uma predecessora
    é  'sem predecessora' quando:
      - NaN (valor vazio do Excel)
      - string vazia ""
    '''
    # Caso comum: célula vazia no Excel -> NaN
    if pd.isna(predecessora):
        return False
    
    # Se for string, pode estar vazia ou só com espaços
    if isinstance(predecessora, str) and predecessora.strip() == "":
        return False
    
    # Qualquer outra coisa (ex.: "OS_4") a gente considera que tem predecessora
    return True


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

        # 8.4 tratar as predecessoras - de outra forma 

        dia_minimo = None # começa vazio

        if tem_predecessora(predecessora):
            dia_predecessora = programacao.get(predecessora)
            
            # se a predecessora não foi programada, não consigo rodar a OS

            if dia_predecessora is None:
                nao_programadas.append(os_id)
                continue
            else:
                dia_minimo = extrair_num_do_dia(dia_predecessora)

        # 8.5 procurar algum dia_escolhido dentre os possíveis 

        dia_escolhido = None # começa vazio 

        for dia in dias_possiveis:
            numero_dia = extrair_num_do_dia(dia)

            # verificar se atende a restrição da predecessora
            if dia_minimo is not None and numero_dia <= dia_minimo:
                continue

            # verificar se ha capacidade disponivel para todas as habilidades
            cabe_no_dia = True

            for habilidade, horas_necessarias in horas_p_habilidade.items():
                capacidade_atual = capacidade.get((dia, habilidade), 0)
                uso_atual = uso.get((dia, habilidade), 0)
                horas_restantes = capacidade_atual - uso_atual

                if horas_restantes < horas_necessarias:
                    # poica a capidade da habilidade no dia x 
                    cabe_no_dia = False
                    break
            
            # se achou um dia bom para
            if cabe_no_dia: 
                dia_escolhido = dia
                break
        # 8.6 se NÃO achou nenhum dia bom, adiciona como na lista de não programada
        if dia_escolhido is None:
            nao_programadas.append(os_id)
            continue

        # 8.7 achando o dia bom atualiza a programação e o uso de horas
        for habilidade, horas_necessarias in horas_p_habilidade.items():
            chave = (dia_escolhido, habilidade)
            uso[chave] = uso.get(chave, 0) + horas_necessarias
        
        # 8.8 atualizar a programação da OS
        programacao[os_id] = dia_escolhido


    # 9. calculo das metricas

    # 9.1) Quantidade total de OS programadas
    os_programadas = os_df[os_df["OS"].isin(programacao.keys())]
    n_os = len(os_programadas)

    # 9.2) Quantidade de OS programadas por prioridade
    contagens_prioridade = os_programadas["Prioridade"].value_counts()

    n_Z = int(contagens_prioridade.get("Z", 0))
    n_A = int(contagens_prioridade.get("A", 0))
    n_B = int(contagens_prioridade.get("B", 0))
    n_C = int(contagens_prioridade.get("C", 0))

    # 9.3) Utilização dos recursos (por habilidade)
    # soma capacidade total por habilidade
    capacidade_por_hab = {}
    for (dia, habilidade), horas_cap in capacidade.items():
        capacidade_por_hab[habilidade] = capacidade_por_hab.get(habilidade, 0) + horas_cap

    # soma horas usadas por habilidade
    uso_por_hab = {}
    for (dia, habilidade), horas_usadas in uso.items():
        uso_por_hab[habilidade] = uso_por_hab.get(habilidade, 0) + horas_usadas

    # calcula percentual de utilização por habilidade
    utilizacao = {}
    for habilidade, cap_total in capacidade_por_hab.items():
        usado = uso_por_hab.get(habilidade, 0)
        if cap_total > 0:
            perc = (usado / cap_total) * 100
        else:
            perc = 0.0
        utilizacao[habilidade] = f"{round(perc, 2)}%"  # ex.: "85.32%"

    # --------------------------------------------------
    # 10) Montar o output no formato pedido
    # --------------------------------------------------

    # solution: OS -> número do dia (string), ex.: "1", "3"...
    solution_dict = {}
    for os_id, dia in programacao.items():
        numero_dia = extrair_num_do_dia(dia)  # "Dia_3" -> 3
        solution_dict[os_id] = str(numero_dia)

    output_solution = {
        "solution": solution_dict,
        "metrics": {
            "n_os": n_os,
            "n_Z": n_Z,
            "n_A": n_A,
            "n_B": n_B,
            "n_C": n_C,
            "utilization": utilizacao
        },
        "extras": {
            "observations": "Programação gerada automaticamente respeitando prioridades, paradas, predecessoras e capacidade de recursos.",
            "plots": None,
            "any_additional_information": None
        }
    }

    return output_solution






if __name__ == "__main__":
    caminho_arquivo = r"C:\Users\isaca\Desktop\desafio\data\backlog_desafio_500.xlsx"
    resultado = create_solution(caminho_arquivo)

    print("\n=== OUTPUT SOLUTION ===")
    print(resultado)

