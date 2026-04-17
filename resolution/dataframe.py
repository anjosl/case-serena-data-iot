import pandas as pd
import streamlit as st
import os
from datetime import datetime

# ==============================
# 1. CONFIGURAÇÕES
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_PENDENCIAS = os.path.join(BASE_DIR, "..", "inputs", "pendencias_torres.csv")
PATH_TORRES = os.path.join(BASE_DIR, "..", "inputs", "torre_uso.csv")

#DATA_REFERENCIA = pd.to_datetime("today")
DATA_REFERENCIA = pd.to_datetime("2026-04-03") # data para teste dos prazos


# ==============================
# 2. LEITURA DOS DADOS
# ==============================

df_pendencias = pd.read_csv(
    PATH_PENDENCIAS,
    sep=";",
    encoding="utf-8",
    engine="python"
)

df_torres = pd.read_csv(
    PATH_TORRES,
    sep=",",
    encoding="utf-8",
    engine="python"
)

# ==============================
# 3. TRATAMENTO DE DATAS
# ==============================

# Converter datas
cols_datas = ["Identificação Falha", "Data Inicio", "Data Fim"]
for col in cols_datas:
    if col in df_pendencias.columns:
        df_pendencias[col] = pd.to_datetime(df_pendencias[col], errors="coerce", dayfirst=True)

df_torres["DATA_INSTALACAO"] = pd.to_datetime(
    df_torres["DATA_INSTALACAO"],
    errors="coerce"
)
print("--------------Pendências-------------------","\n")
print(df_pendencias.head())
print(df_pendencias.tail())
print("------------Torres---------------------","\n")
print(df_torres.head())
print(df_torres.tail())

print("===================================================","\n")

# ==============================
# 4. FILTRAR FALHAS ATIVAS
# ==============================

df_pendencias = df_pendencias[
    df_pendencias["Status Falha"] == "Falha Ativa"
].copy()

print("--------------Pendências Filtradas-------------------","\n")
print(df_pendencias.head())
print(df_pendencias.tail())
print("linhas com falhas ativas:",len(df_pendencias))

print("===================================================","\n")

# ==============================
# 5. CRIAR G (GRAU DE CRITICIDADE)
# ==============================

map_criticidade = {
    "Baixa": 1,
    "Media": 2,
    "Média": 2, #foi identificado apenas um único parâmetro assim, não foi feita a normalização por conta disso
    "Alta": 3,
    "Urgente": 4
}

df_pendencias["G"] = df_pendencias["Criticidade"].map(map_criticidade)

# ==============================
# 6. MERGE COM TORRES_USO
# ==============================

df = df_pendencias.merge(
    df_torres,
    on="TME COD.",
    how="left"
)

print("--------------Dataframe merged-------------------","\n")
print(df.head())
print(df.tail())
print("linhas com falhas ativas após merge:",len(df))

print("tamanho do df que contém 'rn' como uso_torre: ",len(
    df[
        (df["USO_TORRE"] == "rn")]))

df["USO_TORRE"] = df["USO_TORRE"].str.upper()

# rn é diferente de RN? assumi que não

print("===================================================","\n")

if len(df) == len(df_pendencias):
    print("Dataframe conservado, seguro para continuar as análises","\n")

    print("===================================================","\n")
else:
    print("Revisar dataframes")

    print("===================================================","\n")

# aqui a ideia é criar um endpoint para poder validar o tratamento até agora
# por enquanto foi apenas mencionado

# ==============================
# 7. CRIAR ANOS DE MEDIÇÃO
# ==============================

df["anos_medicao"] = (
    (DATA_REFERENCIA - df["DATA_INSTALACAO"]).dt.days / 365
)

print("--------------df anos de medição-------------------","\n")
print(df["anos_medicao"].head())
print(df["anos_medicao"].tail())

print("===================================================","\n")

# ==============================
# 8. CRIAR U (REGRA DE NEGÓCIO)
# ==============================

def calcular_U(row):
    candidatos = []

    # U1 - CHU
    if row["CLUSTER"] == "CHU":
        candidatos.append(1)

    # U2 - ONS
    if row["USO_TORRE"] in ["RN", "MO"] and pd.isna(row["NUMBER"]):
        candidatos.append(2)

    # U3 - DEVC
    if row["USO_TORRE"] == "DD" and row["anos_medicao"] > 3:
        candidatos.append(3)

    # U4 - EPE/Com multa
    if row["USO_TORRE"] in ["RN", "MO"] and pd.notna(row["NUMBER"]):
        candidatos.append(4)

    # U5 - DEVP
    if row["USO_TORRE"] == "DD" and row["anos_medicao"] <= 3:
        candidatos.append(5)

    # U6 - VT
    if row["USO_TORRE"] == "RN":
        candidatos.append(6)

    return max(candidatos) if candidatos else None


df["U"] = df.apply(calcular_U, axis=1)

print("--------------df com U categorizado-------------------","\n")
print(df.head())
print(df.tail())

#verificação de G e U
# print(
#     df[
#         (df["G"].isna()) | (df["U"].isna())]
#         [["TME COD.", "G", "U","\n")


print("===================================================","\n")

# ==============================
# 9. RESULTADO parcial
# ==============================

print("--------------df com validação parcial-------------------","\n")

print("Dataset parcial (amostra):","\n")
print(df.head())

print("Colunas disponíveis:","\n")
print(df.columns)

print("--------------validação df parcial-------------------","\n")

print("Resumo G x U:","\n")
print(df.groupby(["G", "U"]).size().reset_index(name="count"))
print(df.groupby(["Criticidade", "U"]).size().reset_index(name="count"),"\n")

print(
    df[
        (df["G"] == 2) & (df["U"] == 6)
    ][["TME COD.", "USO_TORRE", "G", "U", "Status Falha"]]
)

print("tamanho: ",len(
    df[
        (df["G"] == 2) & (df["U"] == 6)
    ][["TME COD.", "USO_TORRE", "G", "U", "Status Falha"]])
)

print(
    df[
        (df["Criticidade"] == "media") & (df["U"] == 6)
    ][["TME COD.", "USO_TORRE", "Criticidade", "U", "Status Falha"]]
)

print("tamanho: ",len(
    df[
        (df["Criticidade"] == "media") & (df["U"] == 6)
    ][["TME COD.", "USO_TORRE", "Criticidade", "U", "Status Falha"]])
)


print("===================================================","\n")

print("--------------validação das datas vazias do df parcial-------------------","\n")

print("tamanho inteiro do df: ",len(df))

print("tamanho do df com datas vazias: ",len(
    df[
        (df["Data Inicio"].isna()) & (df["Data Fim"].isna())])

,"\n")

print(
    df[
        (df["Data Inicio"].isna()) & (df["Data Fim"].isna())]
        [["TME COD.", "USO_TORRE", "Identificação Falha", "Data Inicio", "Data Fim"]],"\n")

print("--------------validação das datas preenchidas do df parcial-------------------","\n")

print(
    df[
        (df["Data Inicio"].notna()) & (df["Data Fim"].notna())]
        [["TME COD.", "USO_TORRE", "Identificação Falha", "Data Inicio", "Data Fim"]],"\n")

# Assumi que datas vazias e datas preenchidas não deveriam constar no relatorio final
# visto que datas vazias mostram dias de falha, porém não mostram inicio nem fim e
# datas preenchidas mostram inicio e fim, ou seja, deveriam estar normalizadas
print("===================================================","\n")

print("--------------Dados excluídos-------------------","\n")

print(df[
    ~df["Data Inicio"].isna() ^ df["Data Fim"].isna()
][["TME COD.", "USO_TORRE", "Identificação Falha", "Data Inicio", "Data Fim"]]

)

#utilizando XOR para calcular melhor o que precisa estar aparente
print("===================================================","\n")

df = df[
    df["Data Inicio"].isna() ^ df["Data Fim"].isna()
]

print("tamanho df limpo: ",len(df))


print("===================================================","\n")

# ==============================
# 10. CÁLCULO ATENDIMENTO
# ==============================

print("--------------Cálculo do Atendimento-------------------","\n")

matriz = pd.DataFrame({
    1: [60, 30, 21, 15],
    2: [60, 30, 21, 15],
    3: [60, 30, 21, 15],
    4: [60, 30, 15, 7],
    5: [60, 21, 15, 7],
    6: [60, 21, 15, 7],
}, index=[1, 2, 3, 4])  # G

# lookup vetorizado
df["prazo_dias"] = df.apply(
    lambda row: matriz.loc[row["G"], row["U"]],
    axis=1
)

df["data_limite"] = df["Data Inicio"] + pd.to_timedelta(df["prazo_dias"], unit="D")

df["status_prazo"] = "No prazo"

df.loc[df["data_limite"] < DATA_REFERENCIA, "status_prazo"] = "Atrasado"

df.loc[
    (df["data_limite"] >= DATA_REFERENCIA) &
    (df["data_limite"] <= DATA_REFERENCIA + pd.Timedelta(days=3)),
    "status_prazo"
] = "Próximo do vencimento"

print(df[["TME COD.", "Data Inicio", "data_limite","prazo_dias","status_prazo"]])

df\
    .sort_values(by="data_limite", ascending=False)\
    .to_csv(os.path.join(BASE_DIR,"saida_prazos.csv"), index=False, sep="\t", encoding="utf-8-sig")

print("===================================================","\n")

# ==========================================
# 11. CLASSIFICAÇÃO DE TORRE PRIORITÁRIA
# ==========================================

print("--------------Priorização de torres-------------------","\n")

ordem_status = {
    "Atrasado": 3,
    "Próximo do vencimento": 2,
    "No prazo": 1
}

# ==============================
# 11.1 PRIORIDADE POR LINHA
# ==============================

df["prioridade_status"] = df["status_prazo"].map(ordem_status)

df["score"] = (
    df["prioridade_status"] * 100 +
    df["G"] * 10 - 
    df["prazo_dias"]
)

# ==============================
# 11.2 ORDENAR (CRITÉRIO PRINCIPAL)
# ==============================

df_sorted = df.sort_values(
    by=["TME COD.", "prioridade_status", "G", "prazo_dias", "Data Inicio"],
    ascending=[True, False, False, True, True]
)

# ==============================
# 11.3 CONSOLIDAR (1 LINHA POR TORRE)
# ==============================

df_final = df_sorted.drop_duplicates(subset="TME COD.", keep="first")

# o código ainda não verifica tipo de sensor impactado para ordenar criticidade por sensor impactado
# daria ainda para verificar se é um anm/wv ou outros sensores, trazendo mais alertas
# então pares de mesmo G x U são considerados iguais, então apenas um deles aparecerá, nesse caso o primeiro

# ==============================
# 11.4 SCORE AGREGADO POR TORRE
# ==============================

df_score_torre = df.groupby("TME COD.")["score"].sum().reset_index()

df_score_torre = df_score_torre.rename(columns={"score": "score_torre"})

# ==============================
# 11.5 MERGE FINAL
# ==============================

df_final = df_final.merge(df_score_torre, on="TME COD.", how="left")

# ==============================
# 12 EXPORT FINAL
# ==============================

df_final\
.sort_values(by="score_torre", ascending=False)\
.to_csv(os.path.join(BASE_DIR, "saida_final.csv"),
        index=False, sep="\t", encoding="utf-8-sig")

print("Arquivo final gerado com sucesso.")



print("===================================================","\n")
print("===================================================","\n")
print("===================================================","\n")
print("===================================================","\n")

print("==============STREAMLIT=====================","\n")



