import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Configuração da Página Web
st.set_page_config(page_title="Rastreador de Gastos", layout="wide")

# Título Principal
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
        if palavra_chave in texto_min:
            return categoria
    return 'Outros'

# 2. BARRA LATERAL (Sidebar)
st.sidebar.header("📁 Importar Dados")
arquivo_carregado = st.sidebar.file_uploader(
    "Carregue seu extrato (.csv ou .xlsx)", 
    type=["csv", "xlsx", "xls"]
)

# 3. VERIFICAÇÃO E LEITURA DO ARQUIVO
if arquivo_carregado is not None:
    try:
        if arquivo_carregado.name.endswith('.csv'):
            df = pd.read_csv(arquivo_carregado)
        else:
            df = pd.read_excel(arquivo_carregado)

        # Mapeamento automático de colunas flexível (aceita variações de nomes)
        colunas_originais = df.columns.tolist()
        mapa_colunas = {}

        for col in colunas_originais:
            col_limpa = str(col).strip().lower()
            if col_limpa in ['descricao', 'descrição', 'historico', 'histórico', 'lançamento', 'lancamento', 'detalhes', 'extrato']:
                mapa_colunas[col] = 'Descricao'
                
            elif col_limpa in ['valor', 'valor (r$)', 'quantia', 'monto', 'amount']:
                mapa_colunas[col] = 'Valor'
                
            elif col_limpa in ['data', 'date', 'dia']:
                mapa_colunas[col] = 'Data'

        # Renomeia as colunas encontradas
        df = df.rename(columns=mapa_colunas)

        # Checa se conseguimos mapear as 3 colunas obrigatórias
        colunas_faltantes = [c for c in ['Data', 'Descricao', 'Valor'] if c not in df.columns]

        if colunas_faltantes:
            st.error(f"⚠️ Não conseguimos encontrar a(s) coluna(s): **{', '.join(colunas_faltantes)}** na sua planilha.")
            st.info(f"📋 As colunas identificadas no seu arquivo foram: `{', '.join([str(c) for c in colunas_originais])}`.\n\n"
                    "Para o sistema funcionar, altere o nome da coluna no Excel para **Descricao**, **Valor** ou **Data**.")
        else:
            st.sidebar.success("Arquivo carregado com sucesso!")
            
            # Garante que valores de gastos fiquem positivos para a soma
            df['Valor'] = df['Valor'].abs()
            
            # Processa as categorias
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

    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo: {e}")

else:
    st.info("👋 **Bem-vindo!** Para gerar o seu relatório, abra a barra lateral esquerda (clicando na setinha `>` no topo esquerdo) e faça o upload do seu arquivo de extrato em formato `.csv` ou `.xlsx`.")