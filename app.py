import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Configuração da Página Web
st.set_page_config(page_title="Rastreador de Gastos", layout="wide")

# Título Principal na Tela
st.title("📊 Dashboard de Gastos Pessoais Inteligente")
st.markdown("Transforme seus extratos bancários brutos em relatórios visuais instantâneos.")
st.markdown("---")

# Regras de categorização automática
REGRAS_CATEGORIA = {
    'uber': 'Transporte', '99app': 'Transporte',
    'ifood': 'Alimentação', 'burger': 'Alimentação', 'mcdonald': 'Alimentação',
    'netflix': 'Assinaturas', 'spotify': 'Assinaturas', 'amazon': 'Assinaturas',
    'supermercado': 'Mercado', 'carrefour': 'Mercado'
}

def classificar_descricao(texto_bruto):
    texto_min = str(texto_bruto).lower()
    for palavra_chave, categoria in REGRAS_CATEGORIA.items():
        if palabra_chave in texto_min:
            return categoria
    return 'Outros'

# 2. BARRA LATERAL (Sidebar)
st.sidebar.header("📁 Importar Dados")
arquivo_carregado = st.sidebar.file_uploader("Carregue seu extrato (.csv)", type=["csv"])

if arquivo_carregado is not None:
    df = pd.read_csv(arquivo_carregado)
    st.sidebar.success("Arquivo carregado com sucesso!")
else:
    st.sidebar.info("Exibindo dados de demonstração (Nenhum arquivo enviado).")
    dados_demonstracao = {
        'Data': ['2026-07-02', '2026-07-05', '2026-07-10', '2026-07-12', '2026-07-15'],
        'Descricao': ['UBER TRIP', 'IFOOD *BR', 'SUPERMERCADO CARREFOUR', 'NETFLIX ASSINATURA', 'RESTAURANTE BURGER'],
        'Valor': [35.50, 89.90, 245.10, 55.90, 42.00]
    }
    df = pd.DataFrame(dados_demonstracao)

# 3. TRATAMENTO E PROCESSAMENTO DOS DADOS
df['Categoria'] = df['Descricao'].apply(classificar_descricao)
total_gasto = df['Valor'].sum()
maior_gasto = df['Valor'].max()

# 4. LAYOUT: Linha de Cartões (Métricas)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Gasto no Período", value=f"R$ {total_gasto:,.2f}")
with col2:
    st.metric(label="Maior Compra Registrada", value=f"R$ {maior_gasto:,.2f}")
with col3:
    st.metric(label="Total de Transações", value=f"{len(df)} compras")

st.markdown("---")

# 5. LAYOUT: Gráfico e Tabela Lado a Lado
col_grafico, col_tabela = st.columns([3, 2])

with col_grafico:
    st.subheader("📈 Gastos por Categoria")
    gastos_por_categoria = df.groupby('Categoria')['Valor'].sum().reset_index()
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(gastos_por_categoria['Categoria'], gastos_por_categoria['Valor'], color='#1E88E5')
    ax.set_ylabel('Total (R$)')
    plt.xticks(rotation=45)
    st.pyplot(fig)

with col_tabela:
    st.subheader("📋 Extrato Processado")
    st.dataframe(df[['Data', 'Descricao', 'Categoria', 'Valor']], use_container_width=True)