# Documentação - Sistema de Programação de Ordens de Serviço (OS)

### Visão Geral

A função `create_solution()` automatiza a programação semanal das Ordens de Serviço (OS), considerando múltiplas restrições operacionais, tais como:

* Prioridade das OS (Z, A, B, C)
* Condição de execução (Operando / Parada)
* Dependência de predecessoras
* Capacidade de horas disponíveis por habilidade

A solução final devolve:

* O dia programado de execução para cada OS
* Métricas de atendimento por prioridade
* Percentual de utilização dos recursos

---

## 🔁 Estrutura Geral da Solução

A função está dividida em **4 grandes blocos lógicos**:

```
1) Ler o Excel e preparar os dados
2) Calcular demanda de horas e duração das OS
3) Executar a lógica de programação (alocar OS em dias possíveis)
4) Gerar métricas e montar o objeto output_solution
```

---

## 🔧 1. Funções Auxiliares

### 1.1 `extrair_num_do_dia(nome_dia: str) -> int`

```python
def extrair_num_do_dia(nome_dia: str) -> int:
    try:
        partes = str(nome_dia).split("_")
        numero = int(partes[-1])
        return numero
    except:
        return False
```

#### Finalidade

* Converte strings como `"Dia_3"` em `3`.
* Garante comparações numéricas corretas entre datas.

📌 **Exemplo de uso:**

```
'Dia_5' → 5
```

---

### 1.2 `tem_predecessora(predecessora) -> bool`

```python
def tem_predecessora(predecessora) -> bool:
    if pd.isna(predecessora):
        return False
    if isinstance(predecessora, str) and predecessora.strip() == "":
        return False
    return True
```

#### Finalidade

* Identifica corretamente se uma OS possui predecessora válida.
* Evita que valores vazios sejam tratados como dependências.

---

## 🗂️ 2. Leitura e Preparação dos Dados

São carregadas as 4 abas do Excel:

* **OS** → identificação, prioridade, condição e predecessora
* **Tarefas** → tarefas por OS, habilidades e duração
* **Recursos** → disponibilidade por habilidade/dia
* **Paradas** → define em quais dias a planta estará parada

```python
os_df = pd.read_excel(..., sheet_name="OS")
tarefas_df = pd.read_excel(..., sheet_name="Tarefas")
recursos_df = pd.read_excel(..., sheet_name="Recursos")
paradas_df = pd.read_excel(..., sheet_name="Paradas")
```

---

## ⏱️ 3. Demanda de Horas por OS

### 3.1 Cálculo base

```python
tarefas_df["Demanda_horas"] = tarefas_df["Duração"] * tarefas_df["Quantidade"]
```

Cada tarefa passa a ter o total de horas necessárias.

### 3.2 Agrupamento por OS e habilidade

```python
demanda_os_hab_df = tarefas_df.groupby(["OS", "Habilidade"])["Demanda_horas"].sum().reset_index()
```

Resultado esperado:

```
OS_10 → Mecânico: 12h | Elétrico: 4h
```

### 3.3 Conversão em dicionário

```python
demanda_por_os = { ... }
```

Fica assim:

```python
{
  "OS_10": {"Mecânico": 12, "Elétrico": 4},
  "OS_51": {"Soldador": 6}
}
```

Esse formato acelera as verificações no loop principal.

---

## 🎯 4. Ordenação das OS

Prioridades textuais são convertidas em números:

```
Z = 1  |  A = 2  |  B = 3  |  C = 4
```

Assim, as OS são processadas nesta ordem:

1. Maior criticidade
2. Menor duração contínua

```python
os_ordenadas = os_df.sort_values(by=["Prioridade_num", "Duracao_continua"])
```

---

## 🧠 5. Programação Principal das OS

O algoritmo percorre cada OS e tenta encaixá‑la em um dia que respeite:

* Regras de parada/operando
* Dependência de predecessoras
* Disponibilidade de horas por habilidade

### 5.1 Seleção de dias possíveis

```python
if condicao == "Parada":
    dias_possiveis = dias_parada
else:
    dias_possiveis = dias_sem_parada
```

### 5.2 Validação de predecessora

Se a predecessora não foi programada antes → a OS é descartada nesta etapa.

### 5.3 Verificação de capacidade

```python
horas_restantes = capacidade[(dia, habilidade)] - uso[(dia, habilidade)]
```

Se qualquer habilidade estourar, o dia é rejeitado.

A primeira combinação válida é escolhida.

---

## 📊 6. Métricas e Resultado Final

A saída segue o modelo solicitado:

```python
{
  "solution": { "OS_10": "1", ... },
  "metrics": {
      "n_os": 32,
      "n_Z": 10,
      "utilization": {"Elétrico": "86.51%", ...}
  },
  "extras": { ... }
}
```

### Métricas calculadas

| Métrica               | Significado                 |
| --------------------- | --------------------------- |
| n_os                  | Nº total de OS programadas  |
| n_Z / n_A / n_B / n_C | Quantidade por prioridade   |
| utilization           | % de uso de cada habilidade |

---

## ✅ Conclusão

A função `create_solution()` implementa um **agendador determinístico** que respeita todas as regras operacionais e produz uma solução estruturada, auditável e facilmente integrável a outros sistemas.

Essa documentação pode ser incluída diretamente em um **notebook Jupyter**, servindo como referência técnica oficial do projeto.

---

📌 *Fim do documento.*
