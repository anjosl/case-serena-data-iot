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

# DATA_REFERENCIA = pd.to_datetime("today")
DATA_REFERENCIA = pd.to_datetime("2026-04-03")  # data para teste dos prazos

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

cols_datas = ["Identificação Falha", "Data Inicio", "Data Fim"]

for col in cols_datas:
    if col in df_pendencias.columns:
        df_pendencias[col] = pd.to_datetime(
            df_pendencias[col],
            errors="coerce",
            dayfirst=True
        )

df_torres["DATA_INSTALACAO"] = pd.to_datetime(
    df_torres["DATA_INSTALACAO"],
    errors="coerce"
)

print("--------------Pendências-------------------\n")
print(df_pendencias.head())
print(df_pendencias.tail())

print("------------Torres---------------------\n")
print(df_torres.head())
print(df_torres.tail())

print("===================================================\n")

# ==============================
# 4. FILTRAR FALHAS ATIVAS
# ==============================

df_pendencias = df_pendencias[
    df_pendencias["Status Falha"] == "Falha Ativa"
].copy()

print("--------------Pendências Filtradas-------------------\n")
print(df_pendencias.head())
print(df_pendencias.tail())
print("linhas com falhas ativas:", len(df_pendencias))

print("===================================================\n")

# ==============================
# 5. CRIAR G
# ==============================

map_criticidade = {
    "Baixa": 1,
    "Media": 2,
    "Média": 2,
    "Alta": 3,
    "Urgente": 4
}

df_pendencias["G"] = df_pendencias["Criticidade"].map(map_criticidade)

# ==============================
# 6. MERGE
# ==============================

df = df_pendencias.merge(
    df_torres,
    on="TME COD.",
    how="left"
)

print("--------------Dataframe merged-------------------\n")
print(df.head())
print(df.tail())
print("linhas com falhas após merge:", len(df))

print(
    "tamanho com 'rn':",
    len(df[df["USO_TORRE"] == "rn"])
)

df["USO_TORRE"] = df["USO_TORRE"].str.upper()

print("===================================================\n")

if len(df) == len(df_pendencias):
    print("Dataframe conservado\n")
else:
    print("Revisar dataframes\n")

print("===================================================\n")

# ==============================
# 7. ANOS DE MEDIÇÃO
# ==============================

df["anos_medicao"] = (
    (DATA_REFERENCIA - df["DATA_INSTALACAO"]).dt.days / 365
)

print("--------------anos_medicao-------------------\n")
print(df["anos_medicao"].head())

print("===================================================\n")

# ==============================
# 8. CRIAR U
# ==============================

def calcular_U(row):
    candidatos = []

    if row["CLUSTER"] == "CHU":
        candidatos.append(1)

    if row["USO_TORRE"] in ["RN", "MO"] and pd.isna(row["NUMBER"]):
        candidatos.append(2)

    if row["USO_TORRE"] == "DD" and row["anos_medicao"] > 3:
        candidatos.append(3)

    if row["USO_TORRE"] in ["RN", "MO"] and pd.notna(row["NUMBER"]):
        candidatos.append(4)

    if row["USO_TORRE"] == "DD" and row["anos_medicao"] <= 3:
        candidatos.append(5)

    if row["USO_TORRE"] == "RN":
        candidatos.append(6)

    return max(candidatos) if candidatos else None


df["U"] = df.apply(calcular_U, axis=1)

print("--------------df com U-------------------\n")
print(df.head())

print("===================================================\n")

# ==============================
# 9. VALIDAÇÃO
# ==============================

print("Resumo G x U:\n")
print(df.groupby(["G", "U"]).size().reset_index(name="count"))

print("===================================================\n")

# ==============================
# 10. LIMPEZA DE DATAS
# ==============================

df = df[
    df["Data Inicio"].isna() ^ df["Data Fim"].isna()
]

print("tamanho df limpo:", len(df))

print("===================================================\n")

# ==============================
# 11. CÁLCULO PRAZO
# ==============================

matriz = pd.DataFrame(
    {
        1: [60, 30, 21, 15],
        2: [60, 30, 21, 15],
        3: [60, 30, 21, 15],
        4: [60, 30, 15, 7],
        5: [60, 21, 15, 7],
        6: [60, 21, 15, 7],
    },
    index=[1, 2, 3, 4]
)

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

df.sort_values("data_limite", ascending=False).to_csv(
    os.path.join(BASE_DIR, "saida_prazos.csv"),
    index=False,
    sep="\t",
    encoding="utf-8-sig"
)

print("===================================================\n")

# ==============================
# 12. PRIORIZAÇÃO
# ==============================

ordem_status = {
    "Atrasado": 3,
    "Próximo do vencimento": 2,
    "No prazo": 1
}

df["prioridade_status"] = df["status_prazo"].map(ordem_status)

df["score"] = (
    df["prioridade_status"] * 100 +
    df["G"] * 10 -
    df["prazo_dias"]
)

df_sorted = df.sort_values(
    by=["TME COD.", "prioridade_status", "G", "prazo_dias", "Data Inicio"],
    ascending=[True, False, False, True, True]
)

df_final = df_sorted.drop_duplicates(subset="TME COD.", keep="first")

df_score_torre = (
    df.groupby("TME COD.")["score"]
    .sum()
    .reset_index()
    .rename(columns={"score": "score_torre"})
)

df_final = df_final.merge(df_score_torre, on="TME COD.", how="left")

df_final.sort_values("score_torre", ascending=False).to_csv(
    os.path.join(BASE_DIR, "saida_final.csv"),
    index=False,
    sep="\t",
    encoding="utf-8-sig"
)

print("Arquivo final gerado com sucesso.")

print("==============STREAMLIT=====================","\n")