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


# --- NOVO TRECHO: DADOS DE PIB e PIB per capita --- #

# Indicador de PIB
indicador_pib = "NY.GDP.MKTP.CD"  # PIB total em dólares correntes
dados_pib = []

# Baixando os dados de PIB do Banco Mundial
for codigo, nome in paises.items():
    url_pib = f"https://api.worldbank.org/v2/country/{codigo}/indicator/{indicador_pib}?format=json&date=2013:2025"
    resposta_pib = requests.get(url_pib)
    json_pib = resposta_pib.json()

    if len(json_pib) > 1:
        for item in json_pib[1]:
            ano = item['date']
            valor = item['value']
            if valor is not None:
                dados_pib.append({
                    "País": nome,
                    "Ano": int(ano),
                    "PIB": float(valor)
                })

# Criar DataFrame de PIB
df_pib = pd.DataFrame(dados_pib)

# Mesclar população com PIB
df = pd.merge(df, df_pib, on=["País", "Ano"], how="inner")

# Calcular PIB per capita
df["PIB per capita"] = df["PIB"] / df["População"]

# Calcular crescimento PIB e população
df = df.sort_values(by=["País", "Ano"])
df["Crescimento PIB (%)"] = df.groupby("País")["PIB"].pct_change() * 100
df["Crescimento PIB (%)"] = df["Crescimento PIB (%)"].round(2)

# OBS: "Crescimento População (%)" já está calculado como "Crescimento Anual (%)"


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
    "Egito": "EGY",
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
df["Crescimento Anual (%)"] = df["Crescimento Anual (%)"].round(2)  # opcional, para arredondar
df = df.dropna(subset=["Crescimento Anual (%)"])  # remove linhas com NaN nessa coluna
# Filtrar países com pelo menos uma queda populacional entre 2013 e 2023
# Definir variação com base no crescimento
df["Variação"] = df["Crescimento Anual (%)"].apply(lambda x: "Crescimento" if x > 0 else "Queda")

df["População formatada"] = df["População"].apply(lambda x: f"{x:,}")
df["PIB formatado"] = df["PIB"].apply(lambda x: f"${x:,.0f}")

# Obter lista de países que tiveram ao menos uma queda populacional
paises_com_queda = df[df["Variação"] == "Queda"]["País"].unique().tolist()


df["País"] = df["País"].astype(str)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<p style='text-align: center;'>País(es)</p>", unsafe_allow_html=True)
    paises_selecionados = st.multiselect("Selecione um ou mais países", options=sorted(df["País"].unique()), default=sorted(df["País"].unique()))

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
df_filtred = df.copy()

if paises_selecionados:
    df_filtred = df_filtred[df_filtred["País"].isin(paises_selecionados)]

if ano != "Todos":
    df_filtred = df_filtred[df_filtred["Ano"] == ano]


# Novo filtro: Crescimento Anual (%)
min_val, max_val = df["Crescimento Anual (%)"].min(), df["Crescimento Anual (%)"].max()
valor_min, valor_max = st.slider("Filtrar Crescimento Anual (%)", float(min_val), float(max_val), (float(min_val), float(max_val)))
df_filtred = df_filtred[(df_filtred["Crescimento Anual (%)"] >= valor_min) & (df_filtred["Crescimento Anual (%)"] <= valor_max)]


# Novo filtro: Variação
if variacao_selecionada != "Todos":
    df_filtred = df_filtred[df_filtred["Variação"] == variacao_selecionada]


ano_min, ano_max = df["Ano"].min(), df["Ano"].max()
todos_paises = sorted(df["País"].unique())
if sorted(paises_selecionados) == todos_paises:
    paises_exibicao = "Todos"
else:
    paises_exibicao = ", ".join(paises_selecionados)
st.markdown(f"<h1 style='text-align: center;'>Tabela de População Total ({paises_exibicao})</h1>", unsafe_allow_html=True)




# Cópia apenas para exibição
df_exibicao = df_filtred.copy()

# Substituir as colunas originais pelas formatadas
df_exibicao["População"] = df_exibicao["População formatada"]
df_exibicao["PIB"] = df_exibicao["PIB formatado"]

# Opcional: Remover as colunas auxiliares que não devem aparecer
df_exibicao = df_exibicao.drop(columns=["População formatada", "PIB formatado"])

# Converter para HTML
html = df_exibicao.to_html(index=False, classes='wide-table')


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
        }
        .wide-table th {
            background-color: #FFA500;
        }
        .wide-table td {
            background-color: #003366;
        }
        .table-container {
            overflow-x: auto;
        }
    </style>
""", unsafe_allow_html=True)

# Exibe a tabela com responsividade
st.markdown(f"""
    <div class="table-container">
        {html}
    </div>
""", unsafe_allow_html=True)

csv = df_filtred.to_csv(index=False).encode('utf-8')
st.download_button("Baixar CSV", csv, "dados_filtrados.csv", "text/csv", key='download-csv')

# Exibir gráficos apenas se houver dados
if not df_filtred.empty:
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    col5, col6 = st.columns(2)
    fig_pib_pc = st.columns(2)

    fig1 = px.bar(
        df_filtred,
        x="Ano",
        y="População",
        color="País", 
        title=f"Crescimento Populacional por País - {paises_exibicao} {ano_min}-{ano_max}", 
        barmode="group", 
        color_discrete_map={"Crescimento": "green", "Queda": "red"}
    )
    col1.plotly_chart(fig1)

    fig2 = px.bar(df_filtred, 
                x="População", 
                y="Ano", color="País", 
                title=f"População Total {paises_exibicao} {ano_min}-{ano_max}", 
                orientation='h')
    col2.plotly_chart(fig2)

     # NOVO fig3: Linha com Crescimento Populacional (%) e PIB (%)
    df_linha = df_filtred[["Ano", "País", "Crescimento Anual (%)", "Crescimento PIB (%)"]].dropna()

    fig3 = px.line(
        df_linha.melt(id_vars=["Ano", "País"], 
                      value_vars=["Crescimento Anual (%)", "Crescimento PIB (%)"],
                      var_name="Indicador", value_name="Valor"),
        x="Ano",
        y="Valor",
        color="Indicador",
        line_dash="Indicador",
        markers=True,
        title=f"Crescimento Populacional vs Econômico - {paises_exibicao if paises_exibicao != 'Todos' else 'Todos os Países'}"
    )
    fig3.update_layout(yaxis_title="Crescimento (%)")

    col3.plotly_chart(fig3)

    fig4 = px.pie(df_filtred, 
                values="População", 
                names="País", 
                title=f"População por Ano - {paises_exibicao} {ano_min}-{ano_max}", 
                color_discrete_sequence=px.colors.sequential.Plasma)
    col4.plotly_chart(fig4)

    fig_pib_pc = px.line(df_filtred, x="Ano", y="PIB per capita", color="País", title="Evolução do PIB per capita")
    st.plotly_chart(fig_pib_pc)


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


