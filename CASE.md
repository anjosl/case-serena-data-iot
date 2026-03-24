# Case técnico — Priorização de pendências e prazo de atendimento

Repositório do case para vaga de **engenharia de dados**. O enunciado está neste arquivo; os dados e a imagem da matriz estão na pasta [`inputs/`](inputs/).

## Estrutura do repositório (pacote ao candidato)

```
.
├── CASE.md                          ← você está aqui (enunciado completo)
└── inputs/
    ├── pendencias_torres.csv
    ├── torre_uso.csv
    └── matriz_prazo_atendimento.png   ← matriz oficial G × U (prazos em dias)
```

Na **sua entrega**, espera-se também um arquivo **`docs/pipeline.md`** com a descrição do fluxo de dados — ver *Entregáveis*.

## Contexto (alinhamento com a área de dados)

Este case é um **cenário simplificado** de **dados operacionais de ativos** (telemetria): pendências de campo, cadastro de uso da torre e regras de priorização ligadas à operação. No dia a dia da companhia, o desafio é fazer o **elo entre o dado físico (sensores, comunicação, cadastro)** e o **uso estratégico e operacional** da informação — com **consistência, rastreabilidade e confiabilidade** para priorizar o que atende primeiro. Aqui, isso se traduz em **integração sólida entre fontes**, **tratamento de qualidade**, **lógica analítica clara** e **visualização** que comuniquem prioridade e prazo de forma transparente.

## Objetivo

Construir uma **visualização interativa** que apoie a priorização **das torres com pendência em aberto** (**`Status Falha` = `Falha Ativa`**). O resultado principal deve mostrar **no máximo uma linha por `TME COD.`**, com o par **G × U** da pendência que você considerar **mais prioritária** nessa torre — **documente** no README da entrega como escolheu e como integrou pendências ao cadastro (`torre_uso`). Pendências **`Normalizada`** são **opcionais** (histórico); **não** entram no núcleo da priorização.

A solução deve integrar:

- a lista de pendências com prazo de atendimento;
- Critérios que possam ser usados para ajudar na priorização
- status das pendencias do que está **no prazo**, **próximo do vencimento** ou **atrasado**.

Além disso, a entrega deve incluir uma **descrição simples do pipeline** (em texto, em poucos passos) de como essas informações poderiam chegar com recorrência das fontes até o uso no dia a dia analítico — ver seção *Pipeline de dados*.

---

## O que você vai receber

| Caminho | Descrição |
|--------|-----------|
| `inputs/pendencias_torres.csv` | Pendências por torre |
| `inputs/torre_uso.csv` | Cadastro de torre|
| `inputs/matriz_prazo_atendimento.png` | Matriz oficial de **prazo de atendimento em dias** por **G × U** |

> **Importante:** não há acesso a ambientes internos nem bancos corporativos. Use **apenas** esses arquivos e a imagem.

---

## Dicionário de dados

### `inputs/pendencias_torres.csv`

| Coluna | Descrição |
|--------|-----------|
| `TME COD.`| Identificador da torre (código TME).
| `Criticidade` | Nível de criticidade da pendência |
| `Identificação Falha` | Data em que a falha foi identificada |
| `Categoria Pendência` | Agrupamento técnico da pendência. |
| `Descrição Falha` | Detalhamento do problema ou ação esperada. |
| `Data Inicio` | Início da falha. |
| `Data Fim` | Data de encerramento ou normalização da falha|
| `Dias Em Falha` | Contagem de dias em que a falha permanece ativa. |
| `Status Falha` | Situação atual da falha. |

**Mapeamento a usar neste case:**

| Texto em `Criticidade` | Valor de **G** a usar na matriz |
|------------------------|----------------------------------|
| `Baixa` | **1** |
| `Media` | **2** |
| `Alta` | **3** |
| `Urgente` | **4** |

### `inputs/torre_uso.csv`

| Coluna | Tipo | Obrigatório | Descrição |
|--------|------|-------------|-----------|
| `CLUSTER` | Agrupamento regional / centro. |
| `TME COD.` | Código TME da torre |
| `USO_TORRE` | Código de **uso operacional** da torre. |
| `NUMBER` | Identificador numérico associado à **multa**  |
| `DATA_INSTALACAO` | Data de instalação no formato `YYYY-MM-DD` |

Nas regras **DEVP** e **DEVC**, **`anos_medicao`** é o tempo em anos entre `DATA_INSTALACAO` e a **data de referência** do case (a mesma usada para “no prazo” / “atrasado”, por exemplo a data de hoje). Documente na sua entrega se usa anos completos ou fração decimal de anos.

### Classificação das torres → **U** (1 a 6)

A matriz **G × U** usa **U ∈ {1,…,6}**, alinhados aos rótulos da imagem `inputs/matriz_prazo_atendimento.png`:

| U | Rótulo (coluna da matriz) | Regra de negócio |
|---|---------------------------|------------------|
| **1** | **EPE/Sem** | Operação do **cluster CHU**: `CLUSTER = CHU`. |
| **2** | **ONS** | Operação para ONS: (`USO_TORRE = RN` **ou** `USO_TORRE = MO`) **e** `NUMBER` vazio/nulo. |
| **3** | **DEVC** | Desenvolvimento em campanha: `USO_TORRE = DD` **e** `anos_medicao > 3`. |
| **4** | **EPE/Com** | Operação **com multa**: (`USO_TORRE = RN` **ou** `USO_TORRE = MO`) **e** `NUMBER` preenchido. |
| **5** | **DEVP** | Desenvolvimento prioritário: `USO_TORRE = DD` **e** `anos_medicao <= 3`. |
| **6** | **VT** | Operação para **vento turbinado**: `USO_TORRE = RN`. |


Várias regras podem ser **verdadeiras ao mesmo tempo**, por isto use o **maior** valor entre os candidatos.

O **prazo em dias** por par **G × U** está na imagem `inputs/matriz_prazo_atendimento.png`.

---

## Pipeline de dados (descrição simples)

Explique em **`docs/pipeline.md`**, de forma **objetiva e em linguagem acessível**, o **caminho dos dados** de ponta a ponta: de onde vêm as pendências e o cadastro de torres, como chegam (ex.: exportação, sistema, planilha), o que seria feito para **organizar e atualizar** essas informações com frequência, e como alguém **consome** isso no dia a dia (relatório ou painel). **Não** é necessário diagrama de arquitetura, nome de ferramentas em nuvem nem detalhe técnico de orquestração — basta **sequência clara de passos** e **por que** cada etapa importa para confiar no que aparece na visualização.

---

## Entregáveis

1. **Repositório Git privado** na sua conta pessoal do GitHub contendo:
   - **`docs/pipeline.md`** com a **descrição simples do pipeline**, conforme a seção *Pipeline de dados*;
   - código que carrega, valida e integra os dados (ex.: **Python** com pandas, ou outra stack acordada na convocação);
   - cálculo de prazo e data-alvo conforme as regras deste enunciado;
   - **visualização interativa** (ferramenta acordada na convocação: ex. Streamlit, Dash, Power BI).
2. **`README.md` na raiz do seu repositório** com:
   - como instalar dependências e executar o projeto;
   - premissas, limitações e decisões (incluindo casos de borda);
   - como definir “atrasado” / “próximo do prazo”.
3. Na **visualização**:
   - **tabela principal** com **no máximo uma linha por `TME COD.`**, referente à pendência **falha ativa** mais prioritária (segundo o critério que documentar); colunas essenciais: torre / `TME COD.`, texto ou resumo da pendência escolhida, `Status Falha`, `CLUSTER`, `USO_TORRE`, rótulo de classificação se houver, G, U, prazo em dias, datas, situação;
   - **pelo menos um gráfico** que apoie priorização **nesse conjunto consolidado** (ex.: volume por **U** ou por situação; opcional: `CLUSTER` ou idade a partir de `DATA_INSTALACAO`);
   - **filtros** (ex.: G, U, `CLUSTER`, situação; opcional: visão “todas as falhas ativas” **sem** consolidação ou incluir `Normalizada` para histórico — deixe claro qual é a visão **padrão**).
4. **Acesso e envio**:
   - Conceda acesso de **leitura** ao repositório para os usuários GitHub **`ettoreaquino`** e **`EdsonAPSantos`**;
   - Envie o link do repositório por **e-mail** para `ettore.aquino@srna.co`, `edson.santos@srna.co` e `gustavo.oliveira@srna.co` com o assunto **`Case dados Serena`**.

---

## Prazo e contato

| Item | Valor |
|------|--------|
| **Prazo de entrega** | **27/03/2026** — repositório com acesso concedido e e-mail enviado até esta data |
| **Dúvidas** | `edson.santos@srna.co` |

Perguntas objetivas sobre o enunciado são bem-vindas.

---

## Licença e confidencialidade

Os dados fornecidos são **fictícios ou anonimizados** para fins de avaliação. Não redistribua os arquivos fora do processo seletivo.

---

*Enunciado — versão: `[2026-03-24 / v0.1]`* 