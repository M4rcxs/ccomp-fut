import pandas as pd
import streamlit as st
import plotly.express as px

# ⏬ Carregar dados diretamente do Google Sheets publicado
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHUpdCQrBoNnKWaPsk312y9TxqQLPcOzQ2mP3ab0gDJKzgUxuAaEyK4NpzXf04iYdjkYiA2hO5788y/pub?gid=1274934329&single=true&output=csv"
    return pd.read_csv(url)

df = load_data()

# Limpeza e formatação
df.columns = [col.strip() for col in df.columns]
df["Escanteios Previstos"] = df["Escanteios Previstos"].astype(str).str.replace(",", ".").astype(float)
df["Odd Over (Betano)"] = df["Odd Over (Betano)"].astype(str).str.replace(",", ".").astype(float)
df["Odd Under (Betano)"] = df["Odd Under (Betano)"].astype(str).str.replace(",", ".").astype(float)
df["Resultado da Aposta (Green/Red)"] = df["Resultado da Aposta (Green/Red)"].str.upper().str.strip()

# Título
st.title("📊 Análise de Apostas em Escanteios")

# Filtros
with st.sidebar:
    st.header("Filtros")
    resultado_filter = st.multiselect("Resultado da Aposta", options=df["Resultado da Aposta (Green/Red)"].unique(), default=df["Resultado da Aposta (Green/Red)"].unique())
    mercado_filter = st.multiselect("Mercado Indicado", options=df["Mercado Indicado"].dropna().unique(), default=df["Mercado Indicado"].dropna().unique())

# Aplicar filtros
filtered_df = df[
    (df["Resultado da Aposta (Green/Red)"].isin(resultado_filter)) &
    (df["Mercado Indicado"].isin(mercado_filter))
]

# KPIs
green_count = (filtered_df["Resultado da Aposta (Green/Red)"] == "GREEN").sum()
red_count = (filtered_df["Resultado da Aposta (Green/Red)"] == "RED").sum()
total_bets = len(filtered_df)
green_rate = (green_count / total_bets * 100) if total_bets > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("✅ Greens", green_count)
col2.metric("❌ Reds", red_count)
col3.metric("🎯 Taxa de Acerto", f"{green_rate:.1f}%")

# Gráfico 1: Escanteios Totais vs Previstos
st.subheader("📈 Escanteios Totais vs Previstos")
fig1 = px.scatter(
    filtered_df,
    x="Escanteios Previstos",
    y="Escanteios Totais",
    color="Resultado da Aposta (Green/Red)",
    color_discrete_map={"GREEN": "green", "RED": "red"},
    hover_data=["Time Casa x Time Visitante"],
    title="Dispersão de Escanteios"
)
st.plotly_chart(fig1)

# Gráfico 2: Resultado por Mercado
st.subheader("📊 Resultado por Mercado")
market_stats = filtered_df.groupby(["Mercado Indicado", "Resultado da Aposta (Green/Red)"]).size().reset_index(name="Contagem")
fig2 = px.bar(
    market_stats,
    x="Mercado Indicado",
    y="Contagem",
    color="Resultado da Aposta (Green/Red)",
    color_discrete_map={"GREEN": "green", "RED": "red"},
    barmode="group",
    title="Resultado por Mercado"
)
st.plotly_chart(fig2)


# Tabela com formatação de cor por resultado
st.subheader("📋 Tabela de Apostas")

def color_result(val):
    if val == "GREEN":
        return "color: green; font-weight: bold;"
    elif val == "RED":
        return "color: red; font-weight: bold;"
    return ""

styled_df = filtered_df.reset_index(drop=True).style.map(color_result, subset="Resultado da Aposta (Green/Red)")
st.dataframe(styled_df)


