import pandas as pd

def extrair_num_do_dia(nome_dia: str) -> int:
    '''
    retira o dia_ e deixa só o número 'dia_3' 
    se não der certo retorna false
    '''
    try:
        # divide a string pelo caractere "_"
        partes = str(nome_dia).split("_")
        # pega a última parte (que deve ser o número) e converte para inteiro
        numero = int(partes[-1])
        return numero
    except:
        # retorna false se a conversão falhar (ex: "dia_x")
        return False

def tem_predecessora(predecessora) -> bool:
    '''
    retorna true se realmente existe uma predecessora
    é 'sem predecessora' quando:
      - nan (valor vazio do excel)
      - string vazia ""
    '''
    # caso comum: célula vazia no excel -> nan
    if pd.isna(predecessora):
        return False
    
    # se for string, pode estar vazia ou só com espaços
    if isinstance(predecessora, str) and predecessora.strip() == "":
        return false
    
    # qualquer outra coisa (ex.: "os_4") a gente considera que tem predecessora
    return true


def create_solution(excel_path: str) -> dict:
    '''
    le o arquivo excel do desafio e realiza a programação semanal da os,
    tedno em vista os critérios:
      1 prioridade (z a b c)
      2 parada? sim ou não
      3 predecessora
      4 disponibilidade de horas por habilidade
    '''

    print(f"realizando a leitura dos arquivos excel em: {excel_path}")

    # 1. leitura das abas 

    # lê a aba de ordens de serviço (os)
    os_df = pd.read_excel(excel_path, sheet_name="os")
    # lê a aba de tarefas detalhadas por os
    tarefas_df = pd.read_excel(excel_path, sheet_name="tarefas")
    # lê a aba de recursos (capacidade de horas por dia/habilidade)
    recursos_df = pd.read_excel(excel_path, sheet_name="recursos")
    # lê a aba de paradas (dias em que o equipamento pode parar)
    paradas_df = pd.read_excel(excel_path, sheet_name="paradas")

    # 2. calcular demanda_horas por tarefa (duração * quantidade) 
    # se mudar o nome da erro por causa do excel 

    tarefas_df = tarefas_df.copy()
    # calcula a demanda total de horas de trabalho para cada tarefa
    tarefas_df["demanda_horas"] = tarefas_df["duração"] * tarefas_df["quantidade"]

    
    # 3. sum() demanda_horas por os e habilidade

    # agrupa e soma a demanda_horas para obter o total por os e habilidade
    demanda_os_hab_df = tarefas_df.groupby(["os", "habilidade"]) ["demanda_horas"].sum().reset_index()
    
    # criar estrutura de demanda por os e habilidade
    # estrutura: {os_id: {habilidade: horas_necessárias}}
    demanda_por_os = {}

    # uso de lista de tuplas para melhorar a agilidade 
    for linha in demanda_os_hab_df.itertuples():
        os_id = linha.os
        habilidade = linha.habilidade
        horas = linha.demanda_horas

        if os_id not in demanda_por_os:
            # inicializa o dicionário de habilidades para a nova os
            demanda_por_os[os_id] = {}

        # armazena a demanda de horas para a habilidade específica
        demanda_por_os[os_id][habilidade] = horas


    # 4. cálculo da duração contínua por os

    # soma a duração (tempo de ocupação do equipamento) por os
    duracao_os = tarefas_df.groupby("os")["duração"].sum().reset_index()
    # renomeia a coluna para refletir o cálculo
    duracao_os = duracao_os.rename(columns={"duração": "duracao_continua"})

    # junta a duração contínua à tabela principal de os
    os_df = os_df.merge(duracao_os, on="os", how="left")

  
    # 5. ordenar por prioridade e duração contínua e transofmrar prioridade em números!!

    # mapeamento da prioridade textual para numérica (z=1, a=2, etc.)
    prioridade = {"z": 1, "a": 2, "b": 3, "c": 4}
    os_df["prioridade_num"] = os_df["prioridade"].map(prioridade)

    # ordenadas por prioridade_num e duracao_continua, respectivamente z, a, b e c e os com menor duração 1° 
    # ordena as os: primeiro pela prioridade (ascendente), depois pela duração contínua (ascendente)
    os_ordenadas = os_df.sort_values(
        by=["prioridade_num", "duracao_continua"], ascending=[true, true]
    )

    # 6. criar estrutura de capacidade por dia e habilidade
    # estrutura: (dia, habilidade) ==> hh_disponivel
    
    capacidade = {}

    for linha in recursos_df.itertuples():
        dia = linha.dia
        habilidade = linha.habilidade
        hora_disp = linha.hh_disponivel
        # preenche o dicionário de capacidade
        capacidade[(dia, habilidade)] = hora_disp

    # acompanhamento do uso de horas por dia/habilidade
    # estrutura: (dia, habilidade) ==> hh_utilizadas
    uso = {}

    # dias disponíveis no backlog
    # lista dos dias no cronograma, ordenada (dia_1, dia_2, ...)
    dias_disponiveis = sorted(recursos_df["dia"].unique())

    # 7. encontrando os dias de parada
    # filtra e obtém a lista de dias marcados como "sim" para parada
    dias_parada = paradas_df.loc[paradas_df["parada"] == "sim", "dia"].tolist()

    # 8. loop principal para programar as os
    
    programacao = {}      # os ==> dia em que foi programada
    nao_programadas = []  # os que não deram para nenhum dia

    # itera sobre as os na ordem de prioridade
    for os_linha in os_ordenadas.itertuples():
        os_id = os_linha.os
        condicao = os_linha.condição
        predecessora = os_linha.predecessora

        # 8.1 quanto horas essa os precisa de cada habilidade?
        horas_p_habilidade = demanda_por_os.get(os_id, {})

        # 8.2 quais dias são possíveis para essa os?
        if condicao == "parada":
            # os de parada só pode ser alocada em dias de parada
            dias_possiveis = list(dias_parada)
        else:
            # os "operando" só pode em dias que não são de parada
            dias_possiveis = []
            for dia in dias_disponiveis:
                if dia not in dias_parada:
                    dias_possiveis.append(dia)

        # 8.3 se não existe nenhum dia disponível adiciona na lista de não programadas
        if not dias_possiveis:
            nao_programadas.append(os_id)
            continue

        # 8.4 tratar as predecessoras

        dia_minimo = None  # começa vazio

        if tem_predecessora(predecessora):
            # verifica em que dia a predecessora foi programada
            dia_predecessora = programacao.get(predecessora)
            
            # se a predecessora não foi programada, não consigo rodar a os
            if dia_predecessora is None:
                nao_programadas.append(os_id)
                continue
            else:
                # o dia mínimo para esta os é o dia seguinte ao da predecessora (por convenção, extrai o número)
                dia_minimo = extrair_num_do_dia(dia_predecessora)

        # 8.5 procurar algum dia_escolhido dentre os possíveis 
        dia_escolhido = None  # começa vazio 

        for dia in dias_possiveis:
            numero_dia = extrair_num_do_dia(dia)

            # verificar se atende a restrição da predecessora
            # a os só pode ser programada depois do dia da predecessora
            if dia_minimo is not None and numero_dia <= dia_minimo:
                continue

            # verificar se ha capacidade disponivel para todas as habilidades
            cabe_no_dia = True

            for habilidade, horas_necessarias in horas_p_habilidade.items():
                # capacidade total de hh para o dia/habilidade
                capacidade_atual = capacidade.get((dia, habilidade), 0)
                # horas já utilizadas (comprometidas)
                uso_atual = uso.get((dia, habilidade), 0)
                # capacidade restante
                horas_restantes = capacidade_atual - uso_atual

                if horas_restantes < horas_necessarias:
                    # falta capacidade dessa habilidade no dia x
                    cabe_no_dia = False
                    break
            
            # se achou um dia bom
            if cabe_no_dia: 
                dia_escolhido = dia
                break

        # 8.6 se não achou nenhum dia bom, adiciona como não programada
        if dia_escolhido is None:
            nao_programadas.append(os_id)
            continue

        # 8.7 achando o dia bom atualiza a programação e o uso de horas
        for habilidade, horas_necessarias in horas_p_habilidade.items():
            chave = (dia_escolhido, habilidade)
            # adiciona as horas necessárias ao uso total daquele dia/habilidade
            uso[chave] = uso.get(chave, 0) + horas_necessarias
        
        # 8.8 atualizar a programação da os
        programacao[os_id] = dia_escolhido


    # 9. calculo das metricas

    # 9.1. contagem de os programadas
    # filtra o dataframe original de os para apenas as que foram programadas
    os_programadas = os_df[os_df["os"].isin(programacao.keys())]
    # conta o número total de os programadas
    n_os = len(os_programadas)

    # 9.2. contagem de os por prioridade
    # conta a distribuição de os programadas por prioridade
    contagens_prioridade = os_programadas["prioridade"].value_counts()
    n_z = int(contagens_prioridade.get("z", 0))
    n_a = int(contagens_prioridade.get("a", 0))
    n_b = int(contagens_prioridade.get("b", 0))
    n_c = int(contagens_prioridade.get("c", 0))

    # 9.3. capacidade total por habilidade
    # calcula a capacidade total de horas por habilidade (soma de todos os dias)
    capacidade_por_hab = {}
    for (dia, habilidade), horas_cap in capacidade.items():
        capacidade_por_hab[habilidade] = capacidade_por_hab.get(habilidade, 0) + horas_cap

    # 9.4. uso total por habilidade
    # calcula o uso total de horas por habilidade (soma de todos os dias)
    uso_por_hab = {}
    for (dia, habilidade), horas_usadas in uso.items():
        uso_por_hab[habilidade] = uso_por_hab.get(habilidade, 0) + horas_usadas

    # 9.5. utilização percentual
    # calcula a utilização percentual para cada habilidade
    utilizacao = {}
    for habilidade, cap_total in capacidade_por_hab.items():
        usado = uso_por_hab.get(habilidade, 0)
        if cap_total > 0:
            # utilização = (usado / capacidade total) * 100
            perc = (usado / cap_total) * 100
        else:
            perc = 0.0
        # formata a porcentagem com duas casas decimais
        utilizacao[habilidade] = f"{round(perc, 2)}%"

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
            "n_z": n_z,
            "n_a": n_a,
            "n_b": n_b,
            "n_c": n_c,
            "utilization": utilizacao
        }
    }

    return output_solution


# execução direta
if __name__ == "__main__":
    # define o caminho do arquivo excel
    caminho_arquivo = r"c:\users\isaca\desktop\desafio\data\backlog_desafio_500.xlsx"
    # chama a função principal para gerar a solução
    resultado = create_solution(caminho_arquivo)

    print("\n=== output solution ===")
    from pprint import pprint
    # imprime o dicionário de resultados de forma formatada
    pprint(resultado)