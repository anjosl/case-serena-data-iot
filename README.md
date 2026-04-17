# 📊 Case Dados – Serena

## Visão Geral

Este projeto implementa um pipeline completo de dados para priorização de falhas ativas em torres meteorológicas, incluindo:

-	ingestão e tratamento de dados
-	aplicação de regras de negócio (G e U)
-	cálculo de prazos e status
-	consolidação por torre (1 linha por TME COD.)
-	visualização interativa com filtros e drill-down

O objetivo é permitir tomada de decisão orientada a risco e prazo, destacando as torres mais críticas.

________________________________________
## Tecnologias Utilizadas

-	Python 3.x
-	Pandas
-	Streamlit
-	Altair
________________________________________

## Como executar o projeto

**1. Clonar o repositório**

- git clone < repositório >
- cd < repositorio >

**2. Criar ambiente virtual (opcional, recomendado)**
   
- python -m venv venv
- .\venv\Scripts\activate   # Windows

**3. Instalar dependências**

- pip install -r requirements.txt

**4. Executar o dataframe de dados**

- python resolution/dataframe.py

Isso irá gerar:
-	saida_prazos.csv → todas as falhas ativas com cálculo de prazo
-	saida_final.csv → consolidado (1 linha por torre)
________________________________________
5. Executar a visualização

- streamlit run resolution/visualizacao.py
________________________________________
# Lógica de Negócio

🔹 G – Criticidade

Mapeamento direto da coluna Criticidade:

|Criticidade|	G    |
|-----------|--------|
|Baixa      |	1    |
|Média      |	2    |
|Alta       |	3    |
|Urgente    |	4    |
________________________________________
**🔹 U – Regra de Negócio**

A classificação U é baseada em regras condicionais envolvendo:

-	CLUSTER
-	USO_TORRE
-	presença de NUMBER
-	tempo desde instalação (anos_medicao)
  
Aqui são considerados anos de medição totais em valor float, não foram considerados anos de medição completos pois, isso depende da qualidade dos dados apresentados pelos sensores principais (informação não disponibilizada).

Caso múltiplas regras sejam atendidas, é utilizado:

U = maior valor aplicável
________________________________________
**⏱️ Prazo de atendimento**

Definido por matriz G x U:

-	quanto maior o risco → menor o prazo
  
A data limite é calculada como: 

data_limite = Data Inicio + prazo_dias
________________________________________
**🚦 Classificação de Status**

Definida em relação à data de referência:

-	**Atrasado**
    -	data_limite < data_referencia
-	**Próximo do vencimento**
    -	data_limite <= data_referencia + 3 dias
-	**No prazo**
    -	demais casos
________________________________________
# **🧮 Priorização das Torres**

Cada falha recebe um **score ponderado**:

**score = (status * 100) + (G * 10) - prazo_dias**

Onde Status recebe:

-	Atrasado = 3
-	Próximo = 2
-	No prazo = 1

## Cenários comparativos

**🟢 Caso 1 — Urgente, mas no prazo**

-	G = 4 (urgente) 
-	status = No prazo → 1 
-	prazo = 60

score = 1x100 + 4x10 - 60
score = 100 + 40 - 60 = 80

**🔴 Caso 2 — Média, mas atrasado**

-	G = 2 (média) 
-	status = Atrasado → 3 
-	prazo = 30 

score = 3x100 + 2x10 - 30
score = 300 + 20 - 30 = 290

**🟡 Caso 3 — Alta, próximo do vencimento**

-	G = 3 
-	status = Próximo → 2 
-	prazo = 21 

score = 2x100 + 3x10 - 21
score = 200 + 30 - 21 = 209

**🔵 Caso 4 — Baixa, atrasado**

-	G = 1 
-	status = Atrasado → 3 
- prazo = 60 

score = 3x100 + 1x10 - 60
score = 300 + 10 - 60 = 250

## Comparação geral ordenada por score:

|Caso|Descrição|Score|
|----|---------|-----|
|2|	Média atrasada	|290|
|4|	Baixa atrasada	|250|
|3|	Alta próxima	|209|
|1|	Urgente no prazo	|80|

________________________________________
# 🏆 Consolidação (1 linha por torre)

A falha representativa da torre é definida pela ordenação:

1.	Status (mais crítico primeiro)
2.	G (maior primeiro)
3.	Prazo (menor primeiro)
4.	Data de início (mais antiga como critério de desempate)
   
Ou seja:

A seleção prioriza risco e urgência, não necessariamente a falha mais antiga.
________________________________________
# 📊 Visualização

A aplicação Streamlit contém:

🔹 Tabela principal

-	1 linha por TME COD.
-	falha mais prioritária por torre

🔹 Drill-down

-	seleção de uma torre exibe todas as falhas associadas àquela torre

🔹 Gráficos (por Torre)

-	quantidade de torres por G;
-	por categoria de pendência;
-	por status de prazo.

🔹 Gráficos (por Falha)

-	volume total de falhas por G;
-	por categoria;
-	por status.

🔹 Filtros

-	Cluster
-	Uso da torre
-	G
-	U
-	Status de prazo
-	Categoria de pendência
________________________________________
# ⚠️ Premissas e Decisões

-	Apenas falhas ativas são consideradas (por isso o status falha não aparece nas tabelas)
-	Registros com inconsistência de datas foram removidos:
    -	casos onde início e fim estão simultaneamente preenchidos ou vazios

Para os casos onde estão simultaneamente vazios, identificou-se dias em falha = 0 e > 0. Considerando que a identificação das falhas ocorre em uma mediana de +2 dias de diferença da data de início, basicamente a torre sofre falha -> envia os dados no dia seguinte (ou não) -> falha identificada.

Partindo desse pressuposto, ao menos a data de início deveria ter sido preenchida pois, ela sempre será retroativa.

Para os casos que possuem dias em falha > 0, indicam que a falha já foi identificada e deveriam ter data de início preenchida, existem casos mais antigos que se somadas as datas de identificação + dias em falha o problema já deveria constar como sanado, assim como existe um caso mais específico para a torre ASU5 que consta 1002 dias de falha a partir de 06/05/2025, porém isso seria impossível seguindo a lógica da identificação no dia seguinte, então a data de início deveria ter sido preenchida ou esse é um provável erro na base.

Para os casos que possuem dias em falha = 0, seguindo a lógica da falha identificada no dia posterior, ao menos 1 dia em falha deveria constar, o que não ocorrerá caso a base tenha sido feita em cima de valores horários ou em base de 10 min.

Para os casos onde as datas de início e fim possuem valores preenchidos, entendeu-se que o status da falha seria "normalizado" e, não "ativo"

-	rn e RN foram tratados como equivalentes (uso_torre)
-	Não foi feita normalização completa de criticidade por baixa ocorrência de inconsistência, apenas um valor apareceu como divergente ([Média] com acento agudo), caso outras divergências fossem encontradas seria recomendada a normalização dos valores, com ou sem acento, tudo maiúsculo ou minúsculo ou primeira letra maiúscula.
-	A priorização privilegia impacto operacional (SLA + criticidade)
________________________________________
# 🚧 Limitações

-	Dependência de consistência nas colunas de entrada
-	Regras de U são determinísticas (não adaptativas)
-	Prazo fixo por matriz (não dinâmico)
-	*Não há uma priorização de falha vs falha visto sensor impactado, a nota máxima por score de cada falha é 333, falhas com mesma nota são consideradas com mesma prioridade (nesse caso, se houver uma priorização de falhas visto um determinado budget, será necessário um olhar mais criterioso e manual)
________________________________________
# 📁 Estrutura do Projeto

```
├── inputs/
│   ├── pendencias_torres.csv
│   └── torre_uso.csv
│   └── matriz_prazo_atendimento.png
│
├── resolution/
│     >venv
│   ├── dataframe.py
│   ├── visualizacao.py
│   └── requirements.txt
│   ├── saida_prazos.csv – Será gerado no processo
│   └── saida_final.csv – Será gerado no processo
│
│
└── README.md
```
