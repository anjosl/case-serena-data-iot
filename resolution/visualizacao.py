import pandas as pd
import os
import streamlit as st
import altair as alt

st.set_page_config(layout="wide")

# ==========================
# 1. CARREGAR DADOS
# ==========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df_final = pd.read_csv(
    os.path.join(BASE_DIR, "saida_final.csv"),
    sep="\t",
    encoding="utf-8-sig"
)

df_detail = pd.read_csv(
    os.path.join(BASE_DIR, "saida_prazos.csv"),
    sep="\t",
    encoding="utf-8-sig"
)

ordem_status = {
    "Atrasado": 3,
    "Próximo do vencimento": 2,
    "No prazo": 1
}

df_detail["prioridade_status"] = df_detail["status_prazo"].map(ordem_status)

df_detail["score"] = (
    df_detail["prioridade_status"] * 100 +
    df_detail["G"] * 10 -
    df_detail["prazo_dias"]
)

# garantir datas

for col in ["Data Inicio", "data_limite"]:
    if col in df_final.columns:
        df_final[col] = pd.to_datetime(df_final[col], errors="coerce")

for col in ["Data Inicio", "Data Fim"]:
    if col in df_detail.columns:
        df_detail[col] = pd.to_datetime(df_detail[col], errors="coerce")

# ==========================
# 2. TÍTULO
# ==========================

st.title("📉 Painel de Falhas Ativas")

# ==========================
# 3. FILTROS
# ==========================

st.sidebar.header("🔎 Filtros")

f_cluster = st.sidebar.multiselect(
    "Cluster",
    options=sorted(df_detail["CLUSTER"].dropna().unique())
)

f_uso = st.sidebar.multiselect(
    "Uso Torre",
    options=sorted(df_detail["USO_TORRE"].dropna().unique())
)

f_g = st.sidebar.multiselect(
    "G",
    options=sorted(df_detail["G"].dropna().unique())
)

f_u = st.sidebar.multiselect(
    "U",
    options=sorted(df_detail["U"].dropna().unique())
)

f_status = st.sidebar.multiselect(
    "Status Prazo",
    options=sorted(df_detail["status_prazo"].dropna().unique())
)

f_categoria = st.sidebar.multiselect(
    "Categoria Pendência",
    options=sorted(df_detail["Categoria Pendência"].dropna().unique())
)

# ==========================
# 3.1 FILTROS
# ==========================

df_filtered = df_final.copy()
df_detail_filtered = df_detail.copy()

if f_cluster:
    df_filtered = df_filtered[df_filtered["CLUSTER"].isin(f_cluster)]
    df_detail_filtered = df_detail_filtered[df_detail_filtered["CLUSTER"].isin(f_cluster)]

if f_uso:
    df_filtered = df_filtered[df_filtered["USO_TORRE"].isin(f_uso)]
    df_detail_filtered = df_detail_filtered[df_detail_filtered["USO_TORRE"].isin(f_uso)]

if f_g:
    df_filtered = df_filtered[df_filtered["G"].isin(f_g)]
    df_detail_filtered = df_detail_filtered[df_detail_filtered["G"].isin(f_g)]

if f_u:
    df_filtered = df_filtered[df_filtered["U"].isin(f_u)]
    df_detail_filtered = df_detail_filtered[df_detail_filtered["U"].isin(f_u)]

if f_status:
    df_filtered = df_filtered[df_filtered["status_prazo"].isin(f_status)]
    df_detail_filtered = df_detail_filtered[df_detail_filtered["status_prazo"].isin(f_status)]

if f_categoria:
    df_filtered = df_filtered[df_filtered["Categoria Pendência"].isin(f_categoria)]
    df_detail_filtered = df_detail_filtered[df_detail_filtered["Categoria Pendência"].isin(f_categoria)]

# ==========================
# 4. GRÁFICOS
# ==========================

st.subheader("📊 Qtd de Torres em Falha")

col1, col2, col3 = st.columns(3)
HEIGHT = 250

# ----- G -----
with col1:
    st.markdown("**Por G**")

    chart_g = (
        df_filtered.groupby("G")["TME COD."]
        .nunique()
        .reset_index(name="qtd_torres")
    )

    chart = alt.Chart(chart_g).mark_bar(color="#FF5246").encode(
        x=alt.X("G:O", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("qtd_torres:Q", title="Qtd")
    ).properties(height=HEIGHT)

    st.altair_chart(chart, use_container_width=True)

# ----- Categoria -----
with col2:
    st.markdown("**Por Categoria**")

    chart_cat = (
        df_filtered.groupby("Categoria Pendência")["TME COD."]
        .nunique()
        .reset_index(name="qtd_torres")
        .sort_values("qtd_torres", ascending=False)
    )

    chart = alt.Chart(chart_cat).mark_bar(color="#FF5246").encode(
        x=alt.X(
            "Categoria Pendência:N",
            axis=alt.Axis(labelAngle=0, labelFontSize=10, labelLimit=200)
        ),
        y=alt.Y("qtd_torres:Q", title="Qtd")
    ).properties(height=HEIGHT)

    st.altair_chart(chart, use_container_width=True)

# ----- Status -----
with col3:
    st.markdown("**Por Status**")

    chart_status = (
        df_filtered.groupby("status_prazo")["TME COD."]
        .nunique()
        .reset_index(name="qtd_torres")
    )

    chart = alt.Chart(chart_status).mark_bar().encode(
        x=alt.X(
            "status_prazo:N",
            sort=["Atrasado", "Próximo do vencimento", "No prazo"],
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y("qtd_torres:Q", title="Qtd"),
        color=alt.Color(
            "status_prazo:N",
            scale=alt.Scale(
                domain=["Atrasado", "Próximo do vencimento", "No prazo"],
                range=["#D23532", "#F3EADF", "#32CAA0"]
            ),
            legend=None
        )
    ).properties(height=HEIGHT)

    st.altair_chart(chart, use_container_width=True)

# ==========================
# 4.2 FALHAS
# ==========================

st.subheader("📊 Qtd de Falhas totais")

col4, col5, col6 = st.columns(3)

# ----- G -----
with col4:
    st.markdown("**Falhas por G**")

    chart_g = (
        df_detail_filtered.groupby("G")
        .size()
        .reset_index(name="qtd_falhas")
    )

    chart = alt.Chart(chart_g).mark_bar(color="#FF5246").encode(
        x=alt.X("G:O", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("qtd_falhas:Q", title="Falhas")
    ).properties(height=HEIGHT)

    st.altair_chart(chart, use_container_width=True)

# ----- Categoria -----
with col5:
    st.markdown("**Falhas por Categoria**")

    chart_cat = (
        df_detail_filtered.groupby("Categoria Pendência")
        .size()
        .reset_index(name="qtd_falhas")
        .sort_values("qtd_falhas", ascending=False)
    )

    chart = alt.Chart(chart_cat).mark_bar(color="#FF5246").encode(
        x=alt.X(
            "Categoria Pendência:N",
            axis=alt.Axis(labelAngle=0, labelFontSize=10, labelLimit=200)
        ),
        y=alt.Y("qtd_falhas:Q", title="Falhas")
    ).properties(height=HEIGHT)

    st.altair_chart(chart, use_container_width=True)

# ----- Status -----
with col6:
    st.markdown("**Falhas por Status**")

    chart_status = (
        df_detail_filtered.groupby("status_prazo")
        .size()
        .reset_index(name="qtd_falhas")
    )

    chart = alt.Chart(chart_status).mark_bar().encode(
        x=alt.X(
            "status_prazo:N",
            sort=["Atrasado", "Próximo do vencimento", "No prazo"],
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y("qtd_falhas:Q", title="Falhas"),
        color=alt.Color(
            "status_prazo:N",
            scale=alt.Scale(
                domain=["Atrasado", "Próximo do vencimento", "No prazo"],
                range=["#D23532", "#F3EADF", "#32CAA0"]
            ),
            legend=None
        )
    ).properties(height=HEIGHT)

    st.altair_chart(chart, use_container_width=True)

# ==========================
# 5. MASTER TABLE
# ==========================

st.subheader("Ordem de Prioridade por Torre")

COLS_MASTER = [
    "TME COD.", "CLUSTER", "USO_TORRE", "Descrição Falha",
    "score_torre", "G", "U", "Data Inicio", "data_limite", "prazo_dias"
]

COLS_DETAIL = [
    "TME COD.", "CLUSTER", "USO_TORRE", "Descrição Falha",
    "score", "G", "U", "Data Inicio", "data_limite", "prazo_dias"
]

df_master_view = df_filtered.sort_values("score_torre", ascending=False).copy()

for col in ["Data Inicio", "Data Fim", "data_limite"]:
    if col in df_master_view.columns:
        df_master_view[col] = pd.to_datetime(df_master_view[col], errors="coerce").dt.strftime("%Y-%m-%d")

df_master_view = df_master_view[COLS_MASTER]

selected_torre = st.dataframe(
    df_master_view,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row"
)

# ==========================
# 6. DRILL-DOWN
# ==========================

if len(selected_torre.selection.rows) > 0:
    idx = selected_torre.selection.rows[0]
    tme_cod = df_master_view.iloc[idx]["TME COD."]

    st.divider()
    st.subheader(f"🔍 Detalhamento da Torre: {tme_cod}")

    df_drill = df_detail_filtered[
        df_detail_filtered["TME COD."] == tme_cod
    ].copy()

    df_drill = df_drill.sort_values(
        by=["status_prazo", "G", "U", "prazo_dias"],
        ascending=[False, False, False, True]
    )

    st.dataframe(
        df_drill[COLS_DETAIL],
        use_container_width=True,
        hide_index=True
    )

# ==========================
# 7. VISÃO GLOBAL
# ==========================

st.divider()
st.subheader("Ordem de Prioridade por Falha")

df_detail_filtered = df_detail_filtered.sort_values("score", ascending=False)

for col in ["Data Inicio", "Data Fim", "data_limite"]:
    if col in df_detail_filtered.columns:
        df_detail_filtered[col] = pd.to_datetime(
            df_detail_filtered[col],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")

st.dataframe(
    df_detail_filtered[COLS_DETAIL],
    use_container_width=True,
    hide_index=True
)