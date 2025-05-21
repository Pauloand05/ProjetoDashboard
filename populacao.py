import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Países e indicador
paises = {
    "BR": "Brasil",
    "AR": "Argentina",
    "CL": "Chile",
    "CO": "Colômbia",
    "PE": "Peru",
    "MX": "México",
    "VE": "Venezuela",
    "USA": "Estados Unidos",
    "ZAF": "África do Sul",
    "EGY": "EGITO",
    "ZMB": "Zâmbia",
}
indicador = "SP.POP.TOTL"  # População total

dados = []

# Baixando os dados do Banco Mundial
for codigo, nome in paises.items():
    url = f"https://api.worldbank.org/v2/country/{codigo}/indicator/{indicador}?format=json&date=2013:2025"
    resposta = requests.get(url)
    json_data = resposta.json()

    if len(json_data) > 1:
        for item in json_data[1]:
            ano = item['date']
            valor = item['value']
            if valor is not None:
                dados.append({
                    "País": nome,
                    "Ano": int(ano),
                    "População": int(valor)
                })

st.set_page_config(layout="wide")

# Criar DataFrame
df = pd.DataFrame(dados)

# Mapeamento de país para código ISO-3
iso3_codes = {
    "Brasil": "BRA",
    "Argentina": "ARG",
    "Chile": "CHL",
    "Colômbia": "COL",
    "Peru": "PER",
    "México": "MEX",
    "Venezuela": "VEN",
    "Estados Unidos": "USA",
    "África do Sul": "ZAF",
    "EGITO": "EGY",
    "Zâmbia": "ZMB",
}

# Criar nova coluna com os códigos ISO-3
df["ISO3"] = df["País"].map(iso3_codes)


# # Mostrar título e tabela no app
# st.title("Tabela de População Total (2013-2025)")
# st.dataframe(df)

# Ordenar por país e ano antes de calcular a variação
df = df.sort_values(by=["País", "Ano"])

# Calcular crescimento percentual ano a ano por país
df["Crescimento Anual (%)"] = df.groupby("País")["População"].pct_change() * 100
df["Crescimento Anual (%)"] = df.groupby("País")["População"].pct_change() * 100
df["Crescimento Anual (%)"] = df["Crescimento Anual (%)"].round(2)  # opcional, para arredondar
df = df.dropna(subset=["Crescimento Anual (%)"])  # remove linhas com NaN nessa coluna
df["Variação"] = df["Crescimento Anual (%)"].apply(lambda x: "Crescimento" if x > 0 else "Queda")


df["País"] = df["País"].astype(str)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<p style='text-align: center;'>País</p>", unsafe_allow_html=True)
    pais_selecionado = st.selectbox("", ["Todos"] + list(df["País"].unique()))

with col2:
    st.markdown("<p style='text-align: center;'>Ano</p>", unsafe_allow_html=True)
    ano = st.selectbox("", ["Todos"] + list(df["Ano"].unique()))
    valores_crescimento = sorted(df["Crescimento Anual (%)"].unique(), reverse=True)

with col3:
    st.markdown("<p style='text-align: center;'>Crescimento Anual (%)</p>", unsafe_allow_html=True)
    crescimento_anual = st.selectbox("", ["Todos"] + list(valores_crescimento))

with col4:
    st.markdown("<p style='text-align: center;'>Variação</p>", unsafe_allow_html=True)
    variacao_selecionada = st.selectbox("", ["Todos"] + list(df["Variação"].unique()))


# Filtragem de dados
if pais_selecionado == "Todos" and ano == "Todos":
    df_filtred = df.copy()
elif pais_selecionado != "Todos" and ano == "Todos":
    df_filtred = df[df["País"] == pais_selecionado]
elif pais_selecionado == "Todos" and ano != "Todos":
    df_filtred = df[df["Ano"] == ano]
else:
    df_filtred = df[(df["País"] == pais_selecionado) & (df["Ano"] == ano)]


# Novo filtro: Crescimento Anual (%)
if crescimento_anual != "Todos":
    df_filtred = df_filtred[df_filtred["Crescimento Anual (%)"] == crescimento_anual]

# Novo filtro: Variação
if variacao_selecionada != "Todos":
    df_filtred = df_filtred[df_filtred["Variação"] == variacao_selecionada]


# Mostrar título
st.markdown(
    "<h1 style='text-align: center;'>Tabela de População Total (2013-2023)</h1>",
    unsafe_allow_html=True
)

# Supondo que df_filtred seja seu DataFrame filtrado
html = df_filtred.to_html(index=False, classes='wide-table')

# Estilo CSS para largura total
st.markdown("""
    <style>
        .wide-table {
            width: 100%;
            border-collapse: collapse;
        }
        .wide-table th, .wide-table td {
            padding: 8px 12px;
            text-align: center;
            border: 1px solid #ddd;
            background-color: #003366;
        }
        .wide-table th {
            align: center;
            background-color: #FFA500;
        }
    </style>
""", unsafe_allow_html=True)

# Exibe a tabela com a classe definida
st.markdown(html, unsafe_allow_html=True)

# Exibir gráficos apenas se houver dados
if not df_filtred.empty:
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    col5, col6 = st.columns(2)

    fig1 = px.bar(df_filtred, x="Ano", y="População", color="Variação", title=f"Crescimento/Queda Populacional {pais_selecionado} (2013-2023)", barmode="group", color_discrete_map={"Crescimento": "green", "Queda": "red"})
    col1.plotly_chart(fig1)

    fig2 = px.bar(df_filtred, x="População", y="Ano", color="Ano", title=f"População Total {pais_selecionado} (2013-2023)", orientation='h')
    col2.plotly_chart(fig2)

    fig3 = px.line(df_filtred, x="Ano", y="População", color="País", title=f"População por Ano {pais_selecionado} (2013-2023)")
    col3.plotly_chart(fig3)

    fig4 = px.pie(df_filtred, values="População", names="Ano", title=f"População por Ano - {pais_selecionado}")
    col4.plotly_chart(fig4)

    fig6 = px.line(df_filtred, x="Ano", y="Crescimento Anual (%)", color="País", title="Evolução da Taxa de Crescimento (%)")
    col6.plotly_chart(fig6)

    # NOVO GRÁFICO 2: Scatter População vs Crescimento
    st.subheader("Relação entre População Total e Crescimento Percentual")
    fig7 = px.scatter(df_filtred,x="População",y="Crescimento Anual (%)",color="País",size="População",hover_name="Ano",title="Correlação: População x Crescimento (%)")
    st.plotly_chart(fig7)

    # Mapa
    st.subheader("Mapa de População Total por País")

    if ano != "Todos":
        df_mapa = df[df["Ano"] == ano]

        fig_mapa = px.choropleth(
            df_mapa,
            locations="ISO3",  # agora com códigos ISO válidos
            color="População",
            hover_name="País",
            title=f"População Total por País em {ano}",
            color_continuous_scale=px.colors.sequential.Plasma,
            projection="natural earth"
        )

        fig_mapa.update_geos(showcountries=True, showcoastlines=True, showland=True, fitbounds="locations")
        fig_mapa.update_layout(
            autosize=True,
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.info("Selecione um ano específico para visualizar o mapa.")
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")


