import pandas as pd

def extrair_num_do_dia(nome_dia: str) -> int:
    '''
    retira o Dia_ e deixa só o número 'Dia_3' 
    se não der certo retorna false
    '''
    try:
        partes = str(nome_dia).split("_")  # divide a string
        numero = int(partes[-1])           # pega o último elemento e converte
        return numero
    except:
        return False


def tem_predecessora(predecessora) -> bool:
    '''
    retorna True se REALMENTE existe uma predecessora
    é 'sem predecessora' quando:
      - NaN
      - string vazia ""
    '''
    if pd.isna(predecessora):
        return False

    if isinstance(predecessora, str) and predecessora.strip() == "":
        return False

    return True


def create_solution(excel_path: str) -> dict:
    print(f"Realizando a leitura dos arquivos Excel em: {excel_path}")

    # ---------------- 1. leitura das abas ----------------
    os_df = pd.read_excel(excel_path, sheet_name="OS")
    tarefas_df = pd.read_excel(excel_path, sheet_name="Tarefas")
    recursos_df = pd.read_excel(excel_path, sheet_name="Recursos")
    paradas_df = pd.read_excel(excel_path, sheet_name="Paradas")

    # ---------------- 2. calcular demanda por tarefa ----------------
    tarefas_df = tarefas_df.copy()
    tarefas_df["Demanda_horas"] = tarefas_df["Duração"] * tarefas_df["Quantidade"]

    # ---------------- 3. soma da demanda por OS / Habilidade ----------------
    demanda_os_hab_df = tarefas_df.groupby(["OS", "Habilidade"])["Demanda_horas"].sum().reset_index()
    demanda_por_os = {}

    for linha in demanda_os_hab_df.itertuples():
        os_id = linha.OS
        habilidade = linha.Habilidade
        horas = linha.Demanda_horas

        if os_id not in demanda_por_os:
            demanda_por_os[os_id] = {}

        demanda_por_os[os_id][habilidade] = horas

    # ---------------- 4. cálculo da duração contínua ----------------
    duracao_os = tarefas_df.groupby("OS")["Duração"].sum().reset_index()
    duracao_os = duracao_os.rename(columns={"Duração": "Duracao_continua"})
    os_df = os_df.merge(duracao_os, on="OS", how="left")

    # ---------------- 5. ordenar por prioridade + duração ----------------
    prioridade = {"Z": 1, "A": 2, "B": 3, "C": 4}
    os_df["Prioridade_num"] = os_df["Prioridade"].map(prioridade)

    os_ordenadas = os_df.sort_values(
        by=["Prioridade_num", "Duracao_continua"], ascending=[True, True]
    )

    # ---------------- 6. capacidade por dia + habilidade ----------------
    capacidade = {}
    for linha in recursos_df.itertuples():
        capacidade[(linha.Dia, linha.Habilidade)] = linha.HH_Disponivel

    uso = {}
    dias_disponiveis = sorted(recursos_df["Dia"].unique())

    # ---------------- 7. dias de parada ----------------
    dias_parada = paradas_df.loc[paradas_df["Parada"] == "Sim", "Dia"].tolist()

    # ---------------- 8. programação das OS ----------------
    programacao = {}
    nao_programadas = []

    for os_linha in os_ordenadas.itertuples():
        os_id = os_linha.OS
        condicao = os_linha.Condição
        predecessora = os_linha.Predecessora
        horas_p_habilidade = demanda_por_os.get(os_id, {})

        if condicao == "Parada":
            dias_possiveis = list(dias_parada)
        else:
            dias_possiveis = [d for d in dias_disponiveis if d not in dias_parada]

        if not dias_possiveis:
            nao_programadas.append(os_id)
            continue

        dia_minimo = None

        if tem_predecessora(predecessora):
            dia_predecessora = programacao.get(predecessora)
            if dia_predecessora is None:
                nao_programadas.append(os_id)
                continue
            dia_minimo = extrair_num_do_dia(dia_predecessora)

        dia_escolhido = None
        for dia in dias_possiveis:
            numero_dia = extrair_num_do_dia(dia)

            if dia_minimo is not None and numero_dia <= dia_minimo:
                continue

            cabe_no_dia = True
            for hab, horas in horas_p_habilidade.items():
                cap = capacidade.get((dia, hab), 0)
                usado = uso.get((dia, hab), 0)
                if (cap - usado) < horas:
                    cabe_no_dia = False
                    break

            if cabe_no_dia:
                dia_escolhido = dia
                break

        if dia_escolhido is None:
            nao_programadas.append(os_id)
            continue

        for hab, horas in horas_p_habilidade.items():
            uso[(dia_escolhido, hab)] = uso.get((dia_escolhido, hab), 0) + horas

        programacao[os_id] = dia_escolhido

    # ---------------- 9. métricas ----------------
    os_programadas = os_df[os_df["OS"].isin(programacao.keys())]
    n_os = len(os_programadas)

    contagens = os_programadas["Prioridade"].value_counts()
    n_Z = int(contagens.get("Z", 0))
    n_A = int(contagens.get("A", 0))
    n_B = int(contagens.get("B", 0))
    n_C = int(contagens.get("C", 0))

    capacidade_por_hab = {}
    for (_, hab), horas in capacidade.items():
        capacidade_por_hab[hab] = capacidade_por_hab.get(hab, 0) + horas

    uso_por_hab = {}
    for (_, hab), horas in uso.items():
        uso_por_hab[hab] = uso_por_hab.get(hab, 0) + horas

    utilizacao = {}
    for hab, cap_total in capacidade_por_hab.items():
        usado = uso_por_hab.get(hab, 0)
        perc = (usado / cap_total) * 100 if cap_total else 0
        utilizacao[hab] = f"{round(perc, 2)}%"

    solution_dict = {}
    for os_id, dia in programacao.items():
        solution_dict[os_id] = str(extrair_num_do_dia(dia))

    output_solution = {
        "solution": solution_dict,
        "metrics": {
            "n_os": n_os,
            "n_Z": n_Z,
            "n_A": n_A,
            "n_B": n_B,
            "n_C": n_C,
            "utilization": utilizacao
        }
    }

    return output_solution


# execução direta
if __name__ == "__main__":
    caminho_arquivo = r"C:\Users\isaca\Desktop\desafio\data\backlog_desafio_500.xlsx"
    resultado = create_solution(caminho_arquivo)

    print("\n=== OUTPUT SOLUTION ===")
    from pprint import pprint
    pprint(resultado)



