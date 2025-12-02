# Sistema de Programação Automática de Ordens de Serviço (PCM)

Este projeto implementa um algoritmo de programação semanal de Ordens de Serviço (OS), levando em consideração prioridades, restrições operacionais, predecessoras e a disponibilidade de recursos por habilidade.

O objetivo é determinar **em qual dia cada OS deve ser realizada**.

---

## Tecnologias usadas

- **Python 3.12+**
- **Pandas** (tratamento e agregação dos dados)
- **OpenPyXL** (leitura de arquivos Excel)

---

## Estrutura do projeto
```
desafio/
├── src/
│   └── solucao.py
├── data/
│   └── backlog_desafio_500.xlsx
├── docs/
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
