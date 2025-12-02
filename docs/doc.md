
A função create_solution() resolve o problema em 4 grandes blocos:

Ler o Excel e preparar os dados

Calcular a demanda de horas e a duração das OS

Criar a lógica de programação (alocação da OS em um dia)

Calcular métricas e montar o output_solution


1. Funções auxiliares
1.1 extrair_num_do_dia(nome_dia: str)
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


Função:

Entrada: algo como "Dia_3" ou 3.

Saída: o número do dia (3).

Por que isso existe?

No Excel os dias aparecem como "Dia_1", "Dia_2", etc.

Para comparar se uma OS pode ser agendada depois da predecessora, você precisa comparar números (ex.: dia 3 > dia 1).

Essa função padroniza tudo para um inteiro



.2 tem_predecessora(predecessora)
def tem_predecessora(predecessora) -> bool:
    '''
    retorna True se REALMENTE existe uma predecessora
    é  'sem predecessora' quando:
      - NaN (valor vazio do Excel)
      - string vazia ""
    '''
    if pd.isna(predecessora):
        return False
    
    if isinstance(predecessora, str) and predecessora.strip() == "":
        return False
    
    return True


Função:

Verifica se a OS realmente tem uma predecessora.

Retorna False se a célula estiver vazia (sem predecessora de verdade).

Por que isso é importante?

No Excel, OS sem predecessora aparecem com célula vazia.

Se você não tratar isso, o código poderia interpretar vazio como se fosse um ID válido de predecessora e jogar a OS como “não programável”.

Essa função garante que só OS com algo como "OS_4", "OS_10", etc sejam tratadas como dependentes.

2. Leitura das abas e preparação inicial
os_df = pd.read_excel(excel_path, sheet_name="OS")
tarefas_df = pd.read_excel(excel_path, sheet_name="Tarefas")
recursos_df = pd.read_excel(excel_path, sheet_name="Recursos")
paradas_df = pd.read_excel(excel_path, sheet_name="Paradas")


Você carrega os 4 conjuntos de informação necessários:

OS → quem são as ordens, prioridade, condição, predecessora

Tarefas → o que compõe cada OS (habilidades, duração, quantidade)

Recursos → quantas horas cada habilidade tem disponível em cada dia

Paradas → em quais dias há parada programada (manutenção de parada)

3. Cálculo da demanda de horas
3.1 Demanda de horas por tarefa
tarefas_df = tarefas_df.copy()
tarefas_df["Demanda_horas"] = tarefas_df["Duração"] * tarefas_df["Quantidade"]


Cada linha em Tarefas é uma tarefa com:

Duração = horas de 1 execução

Quantidade = quantas vezes ela é feita

Você cria Demanda_horas:

Demanda_horas = Duração × Quantidade

Exemplo:

OS_10, Habilidade Mecânico, Duração 2h, Quantidade 3 → Demanda_horas = 6h

3.2 Somar por OS e habilidade
demanda_os_hab_df = tarefas_df.groupby(["OS", "Habilidade"])["Demanda_horas"].sum().reset_index()


Agora você agrupa por:

OS

Habilidade

e soma as horas de todas as tarefas com aquela mesma combinação.

Exemplo:
Se a OS_10 tem duas tarefas de Mecânico, 2h cada, 3 repetições cada:

Tarefa 1 → 2×3 = 6h

Tarefa 2 → 2×3 = 6h

Soma do groupby => 12h de Mecânico para OS_10

3.3 Transformar em dicionário demanda_por_os
demanda_por_os = {}

for linha in demanda_os_hab_df.itertuples():
    os_id = linha.OS
    habilidade = linha.Habilidade
    horas = linha.Demanda_horas

    if os_id not in demanda_por_os:
        demanda_por_os[os_id] = {}

    demanda_por_os[os_id][habilidade] = horas


Você transforma o DataFrame em um dicionário mais fácil de usar no loop principal:

demanda_por_os = {
    "OS_10": {"Mecânico": 12, "Elétrico": 4},
    "OS_30": {"Soldador": 5},
    ...
}


Por que isso facilita?

Quando estiver avaliando se uma OS cabe em um certo dia, você precisa saber rapidamente:

“Quantas horas de Mecânico, Elétrico, etc essa OS usa?”

Com esse dicionário, basta fazer:

horas_p_habilidade = demanda_por_os.get(os_id, {})

4. Duração contínua da OS e ordenação por prioridade
4.1 Duração contínua
duracao_os = tarefas_df.groupby("OS")["Duração"].sum().reset_index()
duracao_os = duracao_os.rename(columns={"Duração": "Duracao_continua"})

os_df = os_df.merge(duracao_os, on="OS", how="left")


Aqui você soma a duração total das tarefas de cada OS (sem considerar quantidade).

Isso serve como uma noção de “tamanho” da OS.

Você junta essa informação na tabela de OS (os_df) para poder ordenar, analisar, etc.

4.2 Transformar prioridade em número e ordenar
prioridade = {"Z": 1, "A": 2, "B": 3, "C": 4}
os_df["Prioridade_num"] = os_df["Prioridade"].map(prioridade)

os_ordenadas = os_df.sort_values(
    by=["Prioridade_num", "Duracao_continua"], ascending=[True, True]
)


Você mapeia prioridades textuais para números:

Z → 1 (mais crítica)

A → 2

B → 3

C → 4

Depois ordena:

primeiro pela prioridade numérica (Z antes de A, A antes de B...)

depois pela duração (OS menores primeiro dentro da mesma prioridade)

💡 Efeito prático:
O loop principal vai tentar programar primeiro as OS mais críticas e mais “leves”. Isso ajuda a encaixar mais OS dentro das limitações de recursos.

5. Capacidade dos recursos
capacidade = {}

for linha in recursos_df.itertuples():
    dia = linha.Dia
    habilidade = linha.Habilidade
    hora_disp = linha.HH_Disponivel
    capacidade[(dia, habilidade)] = hora_disp


Você monta um dicionário:

capacidade = {
    ("Dia_1", "Mecânico"): 16,
    ("Dia_1", "Elétrico"): 8,
    ("Dia_2", "Mecânico"): 12,
    ...
}


Isso representa quantas horas de cada habilidade existem em cada dia.

5.1 Estrutura uso
uso = {}


Conforme as OS são programadas, você atualiza:

uso[(dia, habilidade)] = horas_já_consumidas


No final, cada chave tem:

quantas horas daquela habilidade em tal dia já foram utilizadas pelas OS programadas.

Isso é essencial para garantir que não estoura a carga de trabalho dos recursos.

6. Identificação de dias disponíveis e de parada
dias_disponiveis = sorted(recursos_df["Dia"].unique())
dias_parada = paradas_df.loc[paradas_df["Parada"] == "Sim", "Dia"].tolist()


dias_disponiveis: todos os dias que aparecem na planilha de recursos.

dias_parada: subconjunto de dias onde Parada = "Sim".

Isso viabiliza a regra:

OS com Condição == "Parada" → só podem ser programadas em dias de parada.

OS com Condição == "Operando" → não podem ser programadas em dias de parada.

7. Loop principal de programação (for os_linha in os_ordenadas.itertuples())

Esse é o coração do algoritmo.
A cada iteração, você pega uma OS (já em ordem de prioridade) e tenta achar um dia que respeite todas as restrições.

7.1 Buscar a demanda da OS
horas_p_habilidade = demanda_por_os.get(os_id, {})


Exemplo de horas_p_habilidade:

{"Mecânico": 12, "Elétrico": 4}


Se a OS não tiver tarefas, isso vira {} e, na prática, ela não consome nada.

7.2 Definir dias possíveis conforme condição
if condicao == "Parada":
    dias_possiveis = list(dias_parada)
else:
    dias_possiveis = []
    for dia in dias_disponiveis:
        if dia not in dias_parada:
            dias_possiveis.append(dia)


Regra aplicada aqui:

Se a OS for de Parada, só pode ser feita em dias em que a planta está parada.

Se for Operando, não pode impactar os dias de parada → só dias comuns.

Se não existir nenhum dia possível, a OS vai para nao_programadas.

7.3 Tratar predecessora
dia_minimo = None

if tem_predecessora(predecessora):
    dia_predecessora = programacao.get(predecessora)
    
    if dia_predecessora is None:
        nao_programadas.append(os_id)
        continue
    else:
        dia_minimo = extrair_num_do_dia(dia_predecessora)


Se a OS possui predecessora válida:

Primeiro verifica se a predecessora já foi programada.

Se não foi, essa OS ainda não pode ser programada ⇒ entra em nao_programadas.

Se foi, pega o número do dia da predecessora e define dia_minimo.

Na hora de escolher o dia:

if dia_minimo is not None and numero_dia <= dia_minimo:
    continue


Ou seja:

“se existe predecessora, essa OS só pode rodar em dias depois dela”.

7.4 Verificar capacidade e escolher o dia
dia_escolhido = None

for dia in dias_possiveis:
    numero_dia = extrair_num_do_dia(dia)

    if dia_minimo is not None and numero_dia <= dia_minimo:
        continue

    cabe_no_dia = True

    for habilidade, horas_necessarias in horas_p_habilidade.items():
        capacidade_atual = capacidade.get((dia, habilidade), 0)
        uso_atual = uso.get((dia, habilidade), 0)
        horas_restantes = capacidade_atual - uso_atual

        if horas_restantes < horas_necessarias:
            cabe_no_dia = False
            break
    
    if cabe_no_dia:
        dia_escolhido = dia
        break


Ideia:

Para cada dia possível:

Verifica se respeita a regra da predecessora.

Para cada habilidade necessária da OS:

pega capacidade_atual

pega uso_atual

calcula horas_restantes = capacidade_atual - uso_atual

se faltar hora em qualquer habilidade → dia reprovado

O primeiro dia que passa em todas as checagens vira dia_escolhido.

Se no final nenhum dia foi encontrado:

if dia_escolhido is None:
    nao_programadas.append(os_id)
    continue

7.5 Atualizar uso de horas e registrar a programação
for habilidade, horas_necessarias in horas_p_habilidade.items():
    chave = (dia_escolhido, habilidade)
    uso[chave] = uso.get(chave, 0) + horas_necessarias

programacao[os_id] = dia_escolhido


Aqui você:

Debita as horas das capacidades daquele dia/habilidade.

Registra que a OS X será executada no dia Y.

Ao final do loop, programacao está assim, por exemplo:

{
    "OS_10": "Dia_1",
    "OS_51": "Dia_1",
    "OS_172": "Dia_2",
    ...
}

8. Cálculo das métricas
8.1 Filtrar OS programadas e contar quantidades
os_programadas = os_df[os_df["OS"].isin(programacao.keys())]
n_os = len(os_programadas)

contagens_prioridade = os_programadas["Prioridade"].value_counts()
n_Z = int(contagens_prioridade.get("Z", 0))
n_A = int(contagens_prioridade.get("A", 0))
n_B = int(contagens_prioridade.get("B", 0))
n_C = int(contagens_prioridade.get("C", 0))


Você:

Filtra só as OS que efetivamente foram programadas.

Conta:

Total (n_os)

Por prioridade (n_Z, n_A, n_B, n_C)

Isso é justamente o que o enunciado pede como métrica de resultado.

8.2 Utilização dos recursos
capacidade_por_hab = {}
for (dia, habilidade), horas_cap in capacidade.items():
    capacidade_por_hab[habilidade] = capacidade_por_hab.get(habilidade, 0) + horas_cap

uso_por_hab = {}
for (dia, habilidade), horas_usadas in uso.items():
    uso_por_hab[habilidade] = uso_por_hab.get(habilidade, 0) + horas_usadas

utilizacao = {}
for habilidade, cap_total in capacidade_por_hab.items():
    usado = uso_por_hab.get(habilidade, 0)
    if cap_total > 0:
        perc = (usado / cap_total) * 100
    else:
        perc = 0.0
    utilizacao[habilidade] = f"{round(perc, 2)}%"


Você:

Soma toda a capacidade daquela habilidade em todos os dias.

Soma tudo o que foi usado daquela habilidade.

Calcula o percentual de utilização.

Exemplo:

Mecânico:

capacidade total na semana: 100h

horas usadas: 86h

utilização: 86%

Esses números aparecem no seu output como:

'utilization': {
   'Elétrico': '86.51%',
   'Lubrificador': '93.38%',
   'Mecânico': '86.46%',
   'Soldador': '92.86%'
}

9. Montagem do output_solution
solution_dict = {}
for os_id, dia in programacao.items():
    numero_dia = extrair_num_do_dia(dia)
    solution_dict[os_id] = str(numero_dia)


Aqui você transforma Dia_1 → "1", Dia_5 → "5", para ficar exatamente no formato pedido.

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
        "observations": "Programação gerada automaticamente respeitando prioridades, dias de parada, predecessoras e capacidade de recursos.",
        "plots": None,
        "any_additional_information": None
    }
}


Esse é o formato fechado bonitinho, pronto para:

salvar em JSON,

mandar para outra API,

ou só exibir em relatório.