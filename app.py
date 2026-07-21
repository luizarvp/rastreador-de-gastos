import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Configuração da Página Web
st.set_page_config(page_title="Rastreador de Gastos", layout="wide")

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

# Palavras-chave para identificar as colunas
PALAVRAS_DATA = ['data', 'datas', 'date', 'dates', 'dia', 'dt']
PALAVRAS_DESCRICAO = ['descricao', 'descrição', 'historico', 'histórico', 'lançamento', 'lancamento', 'detalhes', 'extrato', 'transacao', 'transação', 'item']
PALAVRAS_VALOR = ['valor', 'valores', 'valor (r$)', 'quantia', 'saida', 'saída', 'entrada', 'debito', 'débito', 'credito', 'crédito']

def carregar_e_encontrar_tabela(arquivo):
    """Lê o arquivo e pula linhas em branco/títulos no topo até achar o cabeçalho real"""
    # Lê os dados brutos sem assumir cabeçalho na linha 0
    if arquivo.name.endswith('.csv'):
        df_raw = pd.read_csv(arquivo, header=None)
    else:
        df_raw = pd.read_excel(arquivo, header=None)

    # Procura em qual linha está o cabeçalho de verdade
    linha_cabecalho = None
    todas_palavras = PALAVRAS_DATA + PALAVRAS_DESCRICAO + PALAVRAS_VALOR

    for idx, row in df_raw.head(20).iterrows():
        texto_linha = " ".join([str(v).lower() for v in row.values if pd.notna(v)])
        # Se a linha contiver pelo menos duas palavras conhecidas, ela é o nosso cabeçalho!
        matches = sum(1 for p in todas_palavras if p in texto_linha)
        if matches >= 2:
            linha_cabecalho = idx
            break

    # Se achou uma linha de cabeçalho abaixo do topo, reestrutura o DataFrame
    if linha_cabecalho is not None:
        novas_colunas = df_raw.iloc[linha_cabecalho].values
        df = df_raw.iloc[linha_cabecalho + 1:].copy()
        df.columns = novas_colunas
        return df.reset_index(drop=True)
    
    # Se não achou, retorna o dataframe padrão
    arquivo.seek(0)
    return pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)

# 2. BARRA LATERAL (Sidebar)
st.sidebar.header("📁 Importar Dados")
arquivo_carregado = st.sidebar.file_uploader(
    "Carregue seu extrato (.csv ou .xlsx)", 
    type=["csv", "xlsx", "xls"]
)

# 3. VERIFICAÇÃO E LEITURA DO ARQUIVO
if arquivo_carregado is not None:
    try:
        # Carrega o arquivo encontrando a tabela automaticamente
        df = carregar_e_encontrar_tabela(arquivo_carregado)

        # Mapeamento de colunas
        colunas_originais = df.columns.tolist()
        mapa_colunas = {}

        for col in colunas_originais:
            col_limpa = str(col).strip().lower()

            if col_limpa in PALAVRAS_DATA or any(p in col_limpa for p in ['data', 'date', 'dia']):
                mapa_colunas[col] = 'Data'
            elif col_limpa in PALAVRAS_DESCRICAO or any(p in col_limpa for p in ['desc', 'hist', 'lanç', 'lanc', 'detalhe', 'extrato']):
                mapa_colunas[col] = 'Descricao'
            elif col_limpa in PALAVRAS_VALOR or any(p in col_limpa for p in ['valor', 'saida', 'saída', 'entrada', 'debito', 'débito', 'credito', 'crédito']):
                mapa_colunas[col] = 'Valor'

        df = df.rename(columns=mapa_colunas)

        colunas_faltantes = [c for c in ['Data', 'Descricao', 'Valor'] if c not in df.columns]

        if colunas_faltantes:
            st.error(f"⚠️ Não conseguimos identificar a(s) coluna(s): **{', '.join(colunas_faltantes)}** no seu arquivo.")
            st.info(f"📋 As colunas encontradas foram: `{', '.join([str(c) for c in colunas_originais if pd.notna(c)])}`.")
        else:
            st.sidebar.success("Arquivo carregado com sucesso!")
            
            # Limpeza dos valores numéricos
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0).abs()
            
            # Processamento
            df['Categoria'] = df['Descricao'].apply(classificar_descricao)
            total_gasto = df['Valor'].sum()
            maior_gasto = df['Valor'].max()

            # 4. LAYOUT: Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Gasto no Período", value=f"R$ {total_gasto:,.2f}")
            with col2:
                st.metric(label="Maior Compra Registrada", value=f"R$ {maior_gasto:,.2f}")
            with col3:
                st.metric(label="Total de Transações", value=f"{len(df)} compras")

            st.markdown("---")

            # 5. LAYOUT: Gráfico e Tabela
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
    st.info("👋 **Bem-vindo!** Para gerar o seu relatório, abra a barra lateral esquerda (clicando na setinha `>` no topo esquerdo) e faça o upload do seu arquivo em formato `.csv` ou `.xlsx`.")