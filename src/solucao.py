import pandas as pd
from pprint import pprint

def extrair_num_do_dia(nome_dia: str) -> int:
    '''
    retira o Dia_ e deixa só o número 'Dia_3' 
    se não der certo retorna false
    '''
    try:
        # divide a string pelo caractere "_"
        partes = str(nome_dia).split("_")  

        # pega a última parte (que deve ser o número) e converte para inteiro
        numero = int(partes[-1])           
        return numero
    except:
    
        # retorna false se a conversão falhar (ex: "Dia_X")
        return False


def tem_predecessora(predecessora) -> bool:
    '''
    retorna True se existe uma predecessora
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
    # calcula a demanda total de horas de trabalho para cada tarefa
    tarefas_df["Demanda_horas"] = tarefas_df["Duração"] * tarefas_df["Quantidade"]

    
    # 3. sum() Demanda_horas por OS e habilidade

    # agrupa e soma a Demanda_horas para obter o total por OS e Habilidade
    demanda_os_hab_df = tarefas_df.groupby(["OS", "Habilidade"]) ["Demanda_horas"].sum().reset_index()
    
    # criar estrutura de demanda por OS e habilidade
    # estrutura: {OS_ID: {Habilidade: Horas_Necessárias}}
    demanda_por_os = {}

    # uso de lista de tuplas para melhorar a agilidade 
    for linha in demanda_os_hab_df.itertuples():
        os_id = linha.OS
        habilidade = linha.Habilidade
        horas = linha.Demanda_horas

        if os_id not in demanda_por_os:
            # inicializa o dicionário de habilidades para a nova OS
            demanda_por_os[os_id] = {}

        # armazena a demanda de horas para a habilidade específica
        demanda_por_os[os_id][habilidade] = horas


    # 4. cálculo da duração contínua por OS

    # soma a duração (tempo de ocupação do equipamento) por OS
    duracao_os = tarefas_df.groupby("OS")["Duração"].sum().reset_index()
    duracao_os = duracao_os.rename(columns={"Duração": "Duracao_continua"})


    # junta a duração contínua à tabela principal de OS
    os_df = os_df.merge(duracao_os, on="OS", how="left")
    

    # 5. Ordenar por prioridade e duração contínua e transofmrar prioridade em números!!
    prioridade = {"Z": 1, "A": 2, "B": 3, "C": 4}
    os_df["Prioridade_num"] = os_df["Prioridade"].map(prioridade)

    # ordenadas por Prioridade_num e Duracao_continua, respectivamente Z, A, B e C e OS com menor duração 1° 

    os_ordenadas = os_df.sort_values(
        by=["Prioridade_num", "Duracao_continua"], ascending=[True, True]
    )

    # 6. Criar estrutura de capacidade por dia e habilidade
    # estrutura: (dia, habilidade) ==> HH_Disponivel
    capacidade = {}

    for linha in recursos_df.itertuples():
        capacidade[(linha.Dia, linha.Habilidade)] = linha.HH_Disponivel

    # acompanhamento do uso de horas por dia/habilidade
    # estrutura: (dia, habilidade) ==> HH_Utilizadas
    uso = {}

    # dias disponíveis no backlog
    # lista dos dias no cronograma, ordenada (Dia_1, Dia_2, ...)
    dias_disponiveis = sorted(recursos_df["Dia"].unique())

    # 7. encontrando os dias de parada
    # filtra e obtém a lista de dias marcados como "Sim" para Parada
    dias_parada = paradas_df.loc[paradas_df["Parada"] == "Sim", "Dia"].tolist()

    # 8. Loop principal para programar as OS
    programacao = {}     # OS ==> Dia em que foi programada
    nao_programadas = [] # OS que não deram para nenhum dia


    # itera sobre as OS na ordem de prioridade
    for os_linha in os_ordenadas.itertuples():
        os_id = os_linha.OS
        condicao = os_linha.Condição
        predecessora = os_linha.Predecessora

        # 8.1 quanto horas essa OS precisa de cada habilidade?
        horas_p_habilidade = demanda_por_os.get(os_id, {})

        # 8.2 quais dias são possíveis para essa OS?
        if condicao == "Parada":
            # OS de parada só pode ser alocada em dias de parada
            dias_possiveis = list(dias_parada)
        else:
            # OS "Operando" só pode em dias que NÃO são de parada
            dias_possiveis = []
            for dia in dias_disponiveis:
                if dia not in dias_parada:
                    dias_possiveis.append(dia)

        # 8.3 se não existe nenhum dia disponível adiciona na lista de não programadas
        if not dias_possiveis:
            nao_programadas.append(os_id)
            continue

        # 8.4 tratar as predecessoras

        dia_minimo = None # começa vazio

        if tem_predecessora(predecessora):
            # verifica em que dia a predecessora foi programada
            dia_predecessora = programacao.get(predecessora)
            
            # se a predecessora não foi programada, não consigo rodar a OS
            if dia_predecessora is None:
                nao_programadas.append(os_id)
                continue
            else:
                # o dia mínimo para esta OS é o dia seguinte ao da predecessora (por convenção, extrai o número)
                dia_minimo = extrair_num_do_dia(dia_predecessora)

        # 8.5 procurar algum dia_escolhido dentre os possíveis 

        dia_escolhido = None  # começa vazio 
        for dia in dias_possiveis:
            numero_dia = extrair_num_do_dia(dia)

            # verificar se atende a restrição da predecessora
            # a OS só pode ser programada DEPOIS do dia da predecessora
            if dia_minimo is not None and numero_dia <= dia_minimo:
                continue

            # verificar se ha capacidade disponivel para todas as habilidades
            cabe_no_dia = True

            for habilidade, horas_necessarias in horas_p_habilidade.items():
                # capacidade total de HH para o dia/habilidade
                capacidade_atual = capacidade.get((dia, habilidade), 0)
                # horas já utilizadas (comprometidas)
                uso_atual = uso.get((dia, habilidade), 0)
                # capacidade restante
                horas_restantes = capacidade_atual - uso_atual

                if horas_restantes < horas_necessarias:
                    # falta capacidade dessa habilidade no dia X
                    cabe_no_dia = False
                    break
            
            # se achou um dia bom
            if cabe_no_dia: 
                dia_escolhido = dia
                break

        # 8.6 se NÃO achou nenhum dia bom, adiciona como não programada
        if dia_escolhido is None:
            nao_programadas.append(os_id)
            continue

        # 8.7 achando o dia bom atualiza a programação e o uso de horas
        for habilidade, horas_necessarias in horas_p_habilidade.items():
            chave = (dia_escolhido, habilidade)
            # adiciona as horas necessárias ao uso total daquele dia/habilidade
            uso[chave] = uso.get(chave, 0) + horas_necessarias
        
        # 8.8 atualizar a programação da OS
        programacao[os_id] = dia_escolhido

    # 9. calculo das metricas
    
    # 9.1. contagem de OS programadas
    # filtra o DataFrame original de OS para apenas as que foram programadas
    os_programadas = os_df[os_df["OS"].isin(programacao.keys())]

    # conta o número total de OS programadas
    n_os = len(os_programadas)

    # 9.2. contagem de OS por prioridade
    # conta a distribuição de OS programadas por Prioridade
    contagens = os_programadas["Prioridade"].value_counts()
    n_Z = int(contagens.get("Z", 0))
    n_A = int(contagens.get("A", 0))
    n_B = int(contagens.get("B", 0))
    n_C = int(contagens.get("C", 0))


    # 9.3. capacidade total por habilidade
    # calcula a capacidade total de horas por Habilidade (soma de todos os dias)
    capacidade_por_hab = {}
    for (_, hab), horas in capacidade.items():
        capacidade_por_hab[hab] = capacidade_por_hab.get(hab, 0) + horas


    # 9.4. uso total por habilidade
    # calcula o uso total de horas por Habilidade (soma de todos os dias)
    uso_por_hab = {}
    for (_, hab), horas in uso.items():
        uso_por_hab[hab] = uso_por_hab.get(hab, 0) + horas


    # 9.5. utilização percentual
    # calcula a utilização percentual para cada Habilidade
    utilizacao = {}
    for hab, cap_total in capacidade_por_hab.items():
        usado = uso_por_hab.get(hab, 0)
        # utilização = (usado / Capacidade Total) * 100
        perc = (usado / cap_total) * 100 if cap_total else 0
        # formata a porcentagem com duas casas decimais
        utilizacao[hab] = f"{round(perc, 2)}%"

    # 9.6. formatação da solução de programação
    # cria o dicionário de solução no formato de saída
    solution_dict = {}
    for os_id, dia in programacao.items():
        # extrai o número do dia para o formato final
        numero_dia = extrair_num_do_dia(dia)
        solution_dict[os_id] = str(numero_dia)


    # 9.7. estrutura de saída final
    # estrutura de saída final, contendo a programação e as métricas
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



