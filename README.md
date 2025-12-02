# Sistema de Programação Automática de Ordens de Serviço (PCM)

Este projeto implementa um sistema automatizado para programação semanal de Ordens de Serviço (OS), considerando:

* Prioridades operacionais (Z, A, B, C)
* Dias de parada e operação
* Dependências entre OS (predecessoras)
* Disponibilidade de recursos por habilidade

O algoritmo determina em qual dia cada OS deve ser alocada, respeitando as restrições operacionais. 

---

## Tecnologias usadas

- **Python 3.12+**
- **Pandas** (tratamento e agregação dos dados)
- **OpenPyXL** (leitura de arquivos Excel)

---

## Estrutura do projeto
```
desafio/
├── venv/ 
├── src/
│   └── solucao.py
├── data/
│   └── backlog_desafio_500.xlsx
├── docs/
|   └── fluxograma.bpm
|   └── fluxograma.png
│   └── doc.md
└── README.md
```


---

## Instalação e Configuração

### 1️. Criar o ambiente virtual

```bash
python -m venv .venv
```
### 2. Ativar o ambiente virtual 
#### Windows 
```bash
.venv\Scripts\activate
```
#### Linux ou macOS
```bash
source .venv/bin/activate
```

### 3. Instalar depedências 
```bash
pip install pandas openpyxl
```

#### Ou pode usar
```bash
pip install -r requirements.txt
```

## Visão Geral do Sistema
O algoritmo create_solution() processa as planilhas de backlog e executa automaticamente a programação das OS seguindo sete macroetapas:
1) Ler os dados do Excel
2) Calcular demanda de horas por OS e habilidade
3) Calcular duração contínua por OS
4) Ordenar por prioridade e tempo
5) Avaliar restrições da OS (parada e predecessor)
6) Verificar disponibilidade de recursos
7) Programar ou rejeitar a OS e calcular métricas finais


