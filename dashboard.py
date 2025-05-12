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

# Criar colunas de time casa e visitante para filtros e análises
df[["Time Casa", "Time Visitante"]] = df["Time Casa x Time Visitante"].str.split(" x ", expand=True)

# Título
st.title("📊 Análise de Apostas em Escanteios")

# Filtros
with st.sidebar:
    st.header("Filtros")
    resultado_filter = st.multiselect(
        "Resultado da Aposta",
        options=df["Resultado da Aposta (Green/Red)"].unique(),
        default=df["Resultado da Aposta (Green/Red)"].unique()
    )

    mercado_filter = st.multiselect(
        "Mercado Indicado",
        options=df["Mercado Indicado"].dropna().unique(),
        default=df["Mercado Indicado"].dropna().unique()
    )

    # Obter lista única de times (casa e visitante)
    equipes = pd.concat([df["Time Casa"], df["Time Visitante"]]).dropna().unique()
    equipes.sort()
    time_selecionado = st.selectbox("Filtrar por Equipe", options=["Todos"] + list(equipes))

    # Filtro por equipe

# Aplicar filtros
if time_selecionado != "Todos":
    filtered_df = filtered_df[
        (filtered_df["Time Casa"] == time_selecionado) |
        (filtered_df["Time Visitante"] == time_selecionado)
    ]
filtered_df = df[
    (df["Resultado da Aposta (Green/Red)"].isin(resultado_filter)) &
    (df["Mercado Indicado"].isin(mercado_filter))
]

# Aplicar filtro por equipe, se necessário

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
fig1.update_layout(showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

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
fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)


# Análise dos times mais recorrentes por resultado
st.subheader("Relação de Times que mais deram Greens e Reds")

times_df = filtered_df.copy()
times_df[["Time Casa", "Time Visitante"]] = times_df["Time Casa x Time Visitante"].str.split(" x ", expand=True)

def contar_times_por_resultado(df, resultado):
    df_resultado = df[df["Resultado da Aposta (Green/Red)"] == resultado]
    times = pd.concat([df_resultado["Time Casa"], df_resultado["Time Visitante"]])
    return times.value_counts().reset_index().rename(columns={"index": "Time", "Time Casa": "Ocorrências"})

green_teams = contar_times_por_resultado(times_df, "GREEN").head(10)
red_teams = contar_times_por_resultado(times_df, "RED").head(10)

col1, col2 = st.columns(2)
with col1:
    st.markdown("### ✅ Equipes")
    st.dataframe(green_teams, use_container_width=True)

with col2:
    st.markdown("### ❌ Equipes")
    st.dataframe(red_teams, use_container_width=True)

# 📈 Gráfico de Lucro Acumulado
st.subheader("💰 Lucro Acumulado por Aposta")

# Função para calcular lucro com base no mercado escolhido
def calcular_lucro(row):
    aposta = 100  # valor fixo por aposta
    resultado = row["Resultado da Aposta (Green/Red)"]
    mercado = row["Mercado Indicado"].lower()
    
    # Verifica se mercado está relacionado a over ou under
    if "over" in mercado:
        odd = row["Odd Over (Betano)"]
    elif "under" in mercado:
        odd = row["Odd Under (Betano)"]
    else:
        return 0  # Se mercado não reconhecido, ignora
    
    if resultado == "GREEN":
        return (odd - 1) * aposta
    elif resultado == "RED":
        return -aposta
    return 0

# Aplicar a função ao DataFrame filtrado
filtered_df = filtered_df.copy()  # evitar SettingWithCopyWarning
filtered_df["Lucro"] = filtered_df.apply(calcular_lucro, axis=1)
filtered_df["Lucro Acumulado"] = filtered_df["Lucro"].cumsum()
filtered_df["Aposta #"] = range(1, len(filtered_df) + 1)

# Gráfico de linha do lucro acumulado
fig_lucro = px.line(
    filtered_df,
    x="Aposta #",
    y="Lucro Acumulado",
    markers=True,
    title="Lucro Acumulado ao Longo das Apostas",
)
fig_lucro.update_layout(yaxis_title="Lucro (R$)", xaxis_title="Número da Aposta")
st.plotly_chart(fig_lucro, use_container_width=True)

# 📊 Taxa de Acerto por Faixa de Escanteios Previstos
st.subheader("🎯 Taxa de Acerto por Faixa de Escanteios Previstos")

# Categorizar faixas
bins = [0, 8, 9.5, 11.5, float("inf")]
labels = ["0–8", "8.5–9.5", "10–11.5", "12+"]

filtered_df["Faixa de Previsão"] = pd.cut(filtered_df["Escanteios Previstos"], bins=bins, labels=labels, include_lowest=True)

# Agrupar e calcular taxa de acerto por faixa
faixa_stats = (
    filtered_df.groupby("Faixa de Previsão")["Resultado da Aposta (Green/Red)"]
    .value_counts()
    .unstack(fill_value=0)
    .reset_index()
)

faixa_stats["Total"] = faixa_stats.get("GREEN", 0) + faixa_stats.get("RED", 0)
faixa_stats["Taxa de Acerto (%)"] = (faixa_stats.get("GREEN", 0) / faixa_stats["Total"]) * 100

# Gráfico de barras horizontal com taxa de acerto por faixa
fig_faixa = px.bar(
    faixa_stats.sort_values("Taxa de Acerto (%)", ascending=True),
    x="Taxa de Acerto (%)",
    y="Faixa de Previsão",
    orientation="h",
    text="Taxa de Acerto (%)",
    title="Taxa de Acerto por Faixa de Escanteios Previstos",
    color="Taxa de Acerto (%)",
    color_continuous_scale="Greens"
)
fig_faixa.update_layout(yaxis_title="Faixa de Previsão", xaxis_title="Taxa de Acerto (%)")
st.plotly_chart(fig_faixa, use_container_width=True)



st.subheader("📋 Tabela de Apostas")

def color_result(val):
    if val == "GREEN":
        return "color: green; font-weight: bold;"
    elif val == "RED":
        return "color: red; font-weight: bold;"
    return ""

styled_df = filtered_df.reset_index(drop=True).style.map(color_result, subset="Resultado da Aposta (Green/Red)")
st.dataframe(styled_df)
if st.button("🔄 Recarregar Dados"):
    st.cache_data.clear()
    st.rerun()


