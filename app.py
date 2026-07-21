import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber

# 1. Configuração da Página Web
st.set_page_config(page_title="Rastreador de Gastos Multi-Bancos", layout="wide")

st.title("📊 Dashboard de Gastos Pessoais Unificado")
st.markdown("Suba quantos extratos quiser (.csv, .xlsx ou .pdf) e veja a consolidação de todas as suas contas em um só lugar.")
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

# Palavras-chave prioritárias
PALAVRAS_DATA = ['data', 'datas', 'date', 'dates', 'dia', 'dt']
PALAVRAS_DESCRICAO = ['descricao', 'descrição', 'historico', 'histórico', 'lançamento', 'lancamento', 'detalhes', 'extrato', 'transacao', 'transação', 'item']
PALAVRAS_VALOR = ['valor', 'valores', 'valor (r$)', 'quantia', 'saida', 'saída', 'debito', 'débito', 'entrada', 'credito', 'crédito']

def extrair_tabela_de_pdf(arquivo_pdf):
    linhas_tabela = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    linha_limpa = [celula if celula is not None else '' for celula in linha]
                    if any(linha_limpa):
                        linhas_tabela.append(linha_limpa)
    if linhas_tabela:
        return pd.DataFrame(linhas_tabela)
    return pd.DataFrame()

def carregar_e_encontrar_tabela(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith('.csv'):
        df_raw = pd.read_csv(arquivo, header=None)
    elif nome.endswith('.pdf'):
        df_raw = extrair_tabela_de_pdf(arquivo)
    else:
        df_raw = pd.read_excel(arquivo, header=None)

    if df_raw.empty:
        return pd.DataFrame()

    linha_cabecalho = None
    todas_palavras = PALAVRAS_DATA + PALAVRAS_DESCRICAO + PALAVRAS_VALOR

    for idx, row in df_raw.head(25).iterrows():
        texto_linha = " ".join([str(v).lower() for v in row.values if pd.notna(v)])
        matches = sum(1 for p in todas_palavras if p in texto_linha)
        if matches >= 2:
            linha_cabecalho = idx
            break

    if linha_cabecalho is not None:
        novas_colunas = df_raw.iloc[linha_cabecalho].values
        df = df_raw.iloc[linha_cabecalho + 1:].copy()
        df.columns = novas_colunas
        return df.reset_index(drop=True)
    
    return df_raw

# 2. BARRA LATERAL (Sidebar) - AGORA COM SUPORTE A MÚLTIPLOS ARQUIVOS!
st.sidebar.header("📁 Importar Dados")
arquivos_carregados = st.sidebar.file_uploader(
    "Carregue seus extratos (.csv, .xlsx ou .pdf)", 
    type=["csv", "xlsx", "xls", "pdf"],
    accept_multiple_files=True # Permite selecionar vários arquivos de uma vez!
)

# 3. VERIFICAÇÃO E PROCESSAMENTO MULTI-ARQUIVOS
if arquivos_carregados:
    dfs_processados = []

    for arquivo in arquivos_carregados:
        try:
            df_temp = carregar_e_encontrar_tabela(arquivo)

            if not df_temp.empty:
                colunas_originais = df_temp.columns.tolist()
                mapa_colunas = {}
                colunas_mapeadas = set()

                for col in colunas_originais:
                    col_limpa = str(col).strip().lower()
                    if 'saldo' in col_limpa:
                        continue

                    if 'Data' not in colunas_mapeadas and (col_limpa in PALAVRAS_DATA or any(p in col_limpa for p in ['data', 'date', 'dia'])):
                        mapa_colunas[col] = 'Data'
                        colunas_mapeadas.add('Data')
                    elif 'Descricao' not in colunas_mapeadas and (col_limpa in PALAVRAS_DESCRICAO or any(p in col_limpa for p in ['desc', 'hist', 'lanç', 'lanc', 'detalhe', 'extrato'])):
                        mapa_colunas[col] = 'Descricao'
                        colunas_mapeadas.add('Descricao')
                    elif 'Valor' not in colunas_mapeadas and (col_limpa in PALAVRAS_VALOR or any(p in col_limpa for p in ['valor', 'saida', 'saída', 'debito', 'débito'])):
                        mapa_colunas[col] = 'Valor'
                        colunas_mapeadas.add('Valor')

                df_temp = df_temp.rename(columns=mapa_colunas)

                if all(c in df_temp.columns for c in ['Data', 'Descricao', 'Valor']):
                    if isinstance(df_temp['Valor'], pd.DataFrame):
                        col_valor = df_temp['Valor'].iloc[:, 0]
                    else:
                        col_valor = df_temp['Valor']

                    if col_valor.dtype == object:
                        col_valor = (
                            col_valor.astype(str)
                            .str.replace('R$', '', regex=False)
                            .str.replace('.', '', regex=False)
                            .str.replace(',', '.', regex=False)
                            .str.strip()
                        )

                    df_temp['Valor'] = pd.to_numeric(col_valor, errors='coerce').fillna(0).abs()
                    
                    # Adiciona uma coluna indicando de qual arquivo veio essa informação
                    df_temp['Origem'] = arquivo.name
                    
                    dfs_processados.append(df_temp[['Data', 'Descricao', 'Valor', 'Origem']])

        except Exception as e:
            st.sidebar.error(f"Erro no arquivo {arquivo.name}: {e}")

    if dfs_processados:
        # Junta todas as tabelas de todos os bancos em uma só!
        df = pd.concat(dfs_processados, ignore_index=True)
        
        st.sidebar.success(f"✅ {len(arquivos_carregados)} arquivo(s) unificado(s) com sucesso!")
        
        # Processamento global
        df['Categoria'] = df['Descricao'].apply(classificar_descricao)
        total_gasto = df['Valor'].sum()
        maior_gasto = df['Valor'].max()

        # 4. LAYOUT: Métricas Consolidadas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Gasto (Todas as Contas)", value=f"R$ {total_gasto:,.2f}")
        with col2:
            st.metric(label="Maior Compra Registrada", value=f"R$ {maior_gasto:,.2f}")
        with col3:
            st.metric(label="Total de Transações", value=f"{len(df)} compras")

        st.markdown("---")

        # 5. LAYOUT: Gráfico e Tabela Unificada
        col_grafico, col_tabela = st.columns([3, 2])

        with col_grafico:
            st.subheader("📈 Gastos Consolidados por Categoria")
            gastos_por_categoria = df.groupby('Categoria')['Valor'].sum().reset_index()
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.bar(gastos_por_categoria['Categoria'], gastos_por_categoria['Valor'], color='#1E88E5')
            ax.set_ylabel('Total (R$)')
            plt.xticks(rotation=45)
            st.pyplot(fig)

        with col_tabela:
            st.subheader("📋 Extrato Unificado")
            st.dataframe(df[['Data', 'Descricao', 'Categoria', 'Valor', 'Origem']], use_container_width=True)
    else:
        st.error("⚠️ Nenhum dos arquivos enviados possui as colunas válidas de Data, Descrição e Valor.")

else:
    st.info("👋 **Bem-vindo(a)!** Abra a barra lateral e selecione um ou mais extratos bancários (.csv, .xlsx ou .pdf) para gerar o relatório consolidado.")