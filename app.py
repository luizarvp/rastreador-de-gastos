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

# Listas de palavras-chave para identificação de colunas
PALAVRAS_DATA = [
    'data', 'datas', 'date', 'dates', 'dia', 'dias', 'dt', 'dt_transacao'
]

PALAVRAS_DESCRICAO = [
    'descricao', 'descrição', 'descricoes', 'descrições', 
    'historico', 'histórico', 'historicos', 'históricos', 
    'lançamento', 'lancamento', 'lançamentos', 'lancamentos', 
    'detalhes', 'extrato', 'transacao', 'transação', 'transacoes', 'transações', 'item'
]

PALAVRAS_VALOR = [
    'valor', 'valores', 'valor (r$)', 'valor r$', 'quantia', 'monto', 'amount', 
    'saida', 'saída', 'saidas', 'saídas', 'entrada', 'entradas', 
    'debito', 'débito', 'debitos', 'débitos', 'credito', 'crédito', 'creditos', 'créditos'
]

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

        # Mapeamento automático inteligente
        colunas_originais = df.columns.tolist()
        mapa_colunas = {}

        for col in colunas_originais:
            col_limpa = str(col).strip().lower()

            # 1º Passo: Checagem por lista de palavras exatas
            if col_limpa in PALAVRAS_DATA:
                mapa_colunas[col] = 'Data'
            elif col_limpa in PALAVRAS_DESCRICAO:
                mapa_colunas[col] = 'Descricao'
            elif col_limpa in PALAVRAS_VALOR:
                mapa_colunas[col] = 'Valor'
            else:
                # 2º Passo: Checagem flexível por trechos de palavras
                if any(p in col_limpa for p in ['valor', 'saida', 'saída', 'entrada', 'debito', 'débito', 'credito', 'crédito']):
                    mapa_colunas[col] = 'Valor'
                elif any(p in col_limpa for p in ['data', 'date', 'dia']):
                    mapa_colunas[col] = 'Data'
                elif any(p in col_limpa for p in ['desc', 'hist', 'lanç', 'lanc', 'detalhe', 'extrato']):
                    mapa_colunas[col] = 'Descricao'

        # Renomeia as colunas para o padrão do sistema
        df = df.rename(columns=mapa_colunas)

        # Verifica se as 3 colunas vitais foram encontradas
        colunas_faltantes = [c for c in ['Data', 'Descricao', 'Valor'] if c not in df.columns]

        if colunas_faltantes:
            st.error(f"⚠️ Não conseguimos identificar a(s) coluna(s): **{', '.join(colunas_faltantes)}** no seu arquivo.")
            st.info(f"📋 As colunas encontradas na sua planilha foram: `{', '.join([str(c) for c in colunas_originais])}`.\n\n"
                    "Para corrigir, basta mudar o nome da coluna no Excel para **Data**, **Descrição/Histórico** ou **Valor/Entradas/Saídas**.")
        else:
            st.sidebar.success("Arquivo carregado com sucesso!")
            
            # Garante conversão correta de números e valores positivos
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0).abs()
            
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
        st.error(f"Ocorreu um erro ao processar a planilha: {e}")

else:
    st.info("👋 **Bem-vinda!** Para gerar o seu relatório, abra a barra lateral esquerda (clicando na setinha `>` no topo esquerdo) e faça o upload do seu arquivo em formato `.csv` ou `.xlsx`.")