import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
import io
import tempfile
import os
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
    # Detectar caminhos de Tesseract e Poppler em locais comuns (WinGet e Program Files)
    TESSERACT_PATH = None
    TESSERACT_CANDIDATES = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in TESSERACT_CANDIDATES:
        if os.path.exists(p):
            TESSERACT_PATH = p
            break
    if not TESSERACT_PATH:
        wg = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WinGet', 'Packages')
        if os.path.isdir(wg):
            for root, dirs, files in os.walk(wg):
                if 'tesseract.exe' in files:
                    TESSERACT_PATH = os.path.join(root, 'tesseract.exe')
                    break
                # limitar busca para performance
    if TESSERACT_PATH:
        try:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        except Exception:
            pass

    POPPLER_PATH = None
    POPPLER_CANDIDATES = [
        os.path.join(os.environ.get('LOCALAPPDATA',''), 'Microsoft', 'WinGet', 'Packages', 'oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe', 'poppler-25.07.0', 'Library', 'bin'),
        r"C:\Program Files\Poppler\Library\bin",
        r"C:\Program Files (x86)\Poppler\Library\bin",
    ]
    for p in POPPLER_CANDIDATES:
        if p and os.path.isdir(p):
            POPPLER_PATH = p
            break
except Exception:
    OCR_AVAILABLE = False
    TESSERACT_PATH = None
    POPPLER_PATH = None

# 1. Configuração da Página Web
st.set_page_config(page_title="Rastreador de Gastos Multi-Bancos", layout="wide")

st.title("📊 Dashboard de Gastos Pessoais Unificado")
st.markdown("Suba quantos extratos quiser (.csv, .xlsx ou .pdf) e veja a consolidação de todas as suas contas em um só lugar.")
st.markdown("---")

# Regras de categorização automática
REGRAS_CATEGORIA = {
    
   # Regras de categorização automática
# A regra é: 'palavra minúscula que aparece no extrato': 'Nome da Categoria Oficial'

    # Assinaturas
    'prime video': 'Assinaturas digitais',
    'spotify': 'Assinaturas digitais',
    'disneyplus': 'Assinaturas digitais',
    'amazon': 'Assinaturas digitais',
    'google one': 'Assinaturas digitais',
    'discord': 'Assinaturas digitais',
    'youtube premium': 'Assinaturas digitais',
    'deezer': 'Assinaturas digitais',
    'applemusic': 'Assinaturas digitais',
    'brainly': 'Assinaturas digitais',
    'open ai': 'Assinaturas digitais',
    'hbo max': 'Assinaturas digitais',

    
    # Supermercado
    'guanabara': 'Supermercado',
    'carrefour': 'Supermercado',
    'prezunic': 'Supermercado',
    'supermarket': 'Supermercado',
    'mundial': 'Supermercado',
    'vianense': 'Supermercado',
    'multimarket': 'Supermercado',

    
    # Animais
    'petshop': 'Animais de estimação',
    'clinica': 'Animais de estimação', 

    
    # Cartão
    'fatura': 'Cartão de crédito',

    
    # Casa
    'iptu': 'Casa',
    'agua': 'Casa',
    'luz': 'Casa',
    'aluguel': 'Casa',
    'tv a cabo': 'Casa',
    'internet': 'Casa',
    'telefone': 'Casa',
    'gas': 'Casa',
    'taxa de incendio': 'Casa',
    'condominio': 'Casa',

    
    # Comida e bebida
    '99food': 'Comida e bebida',
    'mcdonald': 'Comida e bebida',
    'ifood': 'Comida e bebida',
    'burgerking': 'Comida e bebida',
    'padaria': 'Comida e bebida',
    'mercearia': 'Supermercado',
    'minimercado': 'Supermercado',

    
    # Compras diversas
    'shein': 'Compras diversas',
    'mercado livre': 'Compras diversas',
    'shopee': 'Compras diversas',
    'aliexpress': 'Compras diversas',
    'tiktok shop': 'Compras diversas',
    'amazon': 'Compras diversas',
    'moda': 'Compras diversas',
    'riachuelo': 'Compras diversas',
    'renner': 'Compras diversas',
    'c&a': 'Compras diversas',
    'google play': 'Compras diversas',

    
    # Educação
    'livraria': 'Educação',
    'faculdade': 'Educação',
    'escola': 'Educação',
    'mensalidade': 'Educação',
    'creche': 'Educação',
    'curso': 'Educação',
    'colegio': 'Educação',

    
    # Eletrônicos e informática
    'kabum': 'Eletrônicos',
    'pichau': 'Eletrônicos',
    'terabyte': 'Eletrônicos',

    
    # Saúde e cuidados pessoais
    'droga raia': 'Saúde e cuidados pessoais',
    'drogasil': 'Saúde e cuidados pessoais',
    'pacheco': 'Saúde e cuidados pessoais',
    'venancio': 'Saúde e cuidados pessoais',
    'barbearia': 'Saúde e cuidados pessoais',
    'beleza': 'Saúde e cuidados pessoais',
    'academia': 'Saúde e cuidados pessoais',
    'odonto': 'Saúde e cuidados pessoais',
    'natura': 'Saúde e cuidados pessoais',
    'sephora': 'Saúde e cuidados pessoais',
    'boticario': 'Saúde e cuidados pessoais',
    'consultas medicas': 'Saúde e cuidados pessoais',
    'plano de saude': 'Saúde e cuidados pessoais',

    # Segurança
    'seguro auto': 'Segurança',
    'porto seguro': 'Segurança', 
    'tokio marine': 'Segurança',
    'azul seguros': 'Segurança',
    'seguro de vida': 'Segurança',
    'prudential': 'Segurança',
    'metlife': 'Segurança',
    'mongeral': 'Segurança',

    
    # Transporte
    'uber': 'Transporte',
    '99': 'Transporte',
    'mais.mobi': 'Transporte',
    'jae': 'Transporte',
    'riocard': 'Transporte',

    
    # Transferências
    'pix': 'Transferências',
}

def classificar_descricao(texto_bruto):
    texto_min = str(texto_bruto).lower()
    for palavra_chave, categoria in REGRAS_CATEGORIA.items():
        if palavra_chave in texto_min:
            return categoria
    return 'Outros'

def extrair_tabela_de_pdf(arquivo_pdf):
    """Tenta extrair tabelas estruturadas com pdfplumber e, se falhar ou os dados forem insuficientes,
    faz fallback para OCR (pdf2image + pytesseract) e heurísticas de extração de linhas.
    Recebe um file-like (UploadedFile) ou bytes-like.
    """
    linhas_tabela = []

    # Ler bytes do arquivo (UploadedFile fornece .read())
    try:
        arquivo_pdf.seek(0)
    except Exception:
        pass

    try:
        data = arquivo_pdf.read() if hasattr(arquivo_pdf, 'read') else arquivo_pdf
    except Exception:
        data = None

    # 1) Tentar com pdfplumber (tabelas estruturadas e texto)
    try:
        pdf_stream = io.BytesIO(data) if data is not None else arquivo_pdf
        with pdfplumber.open(pdf_stream) as pdf:
            for pagina in pdf.pages:
                tabelas = pagina.extract_tables()
                if tabelas:
                    for tabela in tabelas:
                        for linha in tabela:
                            linha_limpa = [celula if celula is not None else '' for celula in linha]
                            if any(linha_limpa):
                                linhas_tabela.append(linha_limpa)
                else:
                    # extrai texto por linha como fallback
                    texto = pagina.extract_text()
                    if texto:
                        for linha in texto.split('\n'):
                            if linha.strip():
                                linhas_tabela.append([linha.strip()])
    except Exception:
        # pdfplumber pode falhar em PDFs escaneados; continuamos para tentar OCR
        linhas_tabela = []

    # Se extraímos algo confiável, retornamos
    if linhas_tabela:
        return pd.DataFrame(linhas_tabela)

    # 2) Fallback OCR: renderizar páginas como imagens e extrair texto
    if not OCR_AVAILABLE:
        # OCR não disponível (pdf2image/pytesseract não instalados)
        return pd.DataFrame()

    try:
            if 'POPPLER_PATH' in globals() and POPPLER_PATH:
                imagens = convert_from_bytes(data, dpi=300, poppler_path=POPPLER_PATH)
            else:
                imagens = convert_from_bytes(data, dpi=300)
        except Exception:
            # conversão falhou (poppler ausente ou arquivo inválido)
            return pd.DataFrame()

    ocr_lines = []
    for img in imagens:
        try:
            texto = pytesseract.image_to_string(img, lang='por+eng')
        except Exception:
            texto = pytesseract.image_to_string(img)
        for linha in texto.split('\n'):
            if linha.strip():
                ocr_lines.append(linha.strip())

    # Heurística para transformar linhas OCR em colunas Data/Descricao/Valor quando possível
    import re
    datas, descricoes, valores = [], [], []
    for txt in ocr_lines:
        # Ignora linhas de sumário
        if any(pal in txt.lower() for pal in ['entradas:', 'saídas:', 'saldo', 'total', 'extrato de']):
            continue

        match_data = re.search(r'(\d{2}[-/\.]\d{2}[-/\.]\d{4}|\d{2}[-/\.]\d{2})', txt)
        if not match_data:
            # tenta encontrar valores; se encontrar, usa a linha como descrição única
            match_val = re.findall(r'R?\$?\s*([+-]?\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', txt)
            if match_val:
                val_alvo = match_val[-1]
                val_str = val_alvo.replace('.', '').replace(',', '.')
                try:
                    val = abs(float(val_str))
                except Exception:
                    val = 0.0
                datas.append('')
                descricoes.append(txt)
                valores.append(val)
            continue

        dt = match_data.group(0).replace('-', '/').replace('.', '/')
        match_val = re.findall(r'R?\$?\s*([+-]?\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', txt)
        val = 0.0
        if match_val:
            # prefere o penúltimo quando há múltiplos (saldo + valor)
            val_alvo = match_val[0] if len(match_val) == 1 else match_val[-2]
            val_str = val_alvo.replace('.', '').replace(',', '.')
            try:
                val = abs(float(val_str))
            except Exception:
                val = 0.0

        desc_limpa = txt.replace(match_data.group(0), '').strip()
        if val > 0:
            datas.append(dt)
            descricoes.append(desc_limpa)
            valores.append(val)

    if datas:
        df_final = pd.DataFrame({
            'Data': datas,
            'Descricao': descricoes,
            'Valor': valores,
            'Origem': getattr(arquivo_pdf, 'name', 'pdf')
        })
        return df_final

    return pd.DataFrame()

def carregar_e_encontrar_tabela(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith('.csv'):
        return pd.read_csv(arquivo, header=None)
    elif nome.endswith('.xlsx') or nome.endswith('.xls'):
        return pd.read_excel(arquivo, header=None)
    elif nome.endswith('.pdf'):
        try:
            arquivo.seek(0)
        except Exception:
            pass
        df_pdf = extrair_tabela_de_pdf(arquivo)
        if not df_pdf.empty:
            return df_pdf

    return pd.DataFrame()

# 2. BARRA LATERAL (Sidebar)
st.sidebar.header("📁 Importar Dados")
arquivos_carregados = st.sidebar.file_uploader(
    "Carregue seus extratos (.csv, .xlsx, .pdf ou word)", 
    type=["csv", "xlsx", "xls", "pdf", "word"],
    accept_multiple_files=True
)

if arquivos_carregados:
    dfs_processados = []

    for arquivo in arquivos_carregados:
        try:
            df_temp = carregar_e_encontrar_tabela(arquivo)

            if not df_temp.empty:
                colunas_originais = df_temp.columns.tolist()
                
                # Se for um PDF de texto livre (como o do Mercado Pago)
                if len(colunas_originais) == 1:
                    import re
                    datas, descricoes, valores = [], [], []
                    
                    for idx, row in df_temp.iterrows():
                        txt = str(row.iloc[0]).strip()
                        
                        # Ignora linhas de resumo que não são transações reais
                        if any(palavra in txt.lower() for palavra in ['entradas:', 'saídas:', 'saldo', 'total', 'extrato de']):
                            continue
                            
                        # Procura o padrão de data no começo da linha (ex: 03-06-2026 ou 03/06/2026)
                        match_data = re.search(r'^(\d{2}[-/]\d{2}[-/]\d{4}|\d{2}[-/]\d{2})', txt)
                        if not match_data:
                            continue # Se não tem data no começo, pula a linha (evita lixo de cabeçalho)
                            
                        dt = match_data.group(0).replace('-', '/')
                        
                        # Extrai todos os valores monetários da linha (ex: R$ 47,74 ou -R$ 10,00)
                        match_val = re.findall(r'R?\$?\s*([+-]?\d{1,3}(?:\.\d{3})*,\d{2})', txt)
                        
                        val = 0.0
                        if match_val:
                            # O último valor geralmente é o saldo final da linha, e o penúltimo ou primeiro é o valor da transação
                            # No Mercado Pago, o valor da transação vem antes do saldo. Pegamos o penúltimo se houver mais de um, ou o único.
                            val_alvo = match_val[0] if len(match_val) == 1 else match_val[-2]
                            val_str = val_alvo.replace('.', '').replace(',', '.')
                            val = abs(float(val_str))
                            
                        # Remove a data do texto da descrição para ficar limpo
                        desc_limpa = txt.replace(match_data.group(0), '').strip()
                        
                        if val > 0:
                            datas.append(dt)
                            descricoes.append(desc_limpa)
                            valores.append(val)
                            
                    if datas:
                        df_final = pd.DataFrame({
                            'Data': datas,
                            'Descricao': descricoes,
                            'Valor': valores,
                            'Origem': arquivo.name
                        })
                        dfs_processados.append(df_final)
                else:
                    # Lógica padrão para arquivos com colunas (Itaú, CSVs, Excel)
                    col_data_encontrada, col_desc_encontrada, col_valor_encontrada = None, None, None
                    for col in colunas_originais:
                        c_low = str(col).lower()
                        if not col_data_encontrada and any(k in c_low for k in ['data', 'date', 'dia']):
                            col_data_encontrada = col
                        elif not col_desc_encontrada and any(k in c_low for k in ['desc', 'hist', 'lanç', 'lanc', 'detalhe', 'extrato', 'movimentacao']):
                            col_desc_encontrada = col
                        elif not col_valor_encontrada and ('valor' in c_low or 'val' in c_low or 'quantia' in c_low):
                            col_valor_encontrada = col

                    if not col_data_encontrada and len(colunas_originais) >= 1: col_data_encontrada = colunas_originais[0]
                    if not col_desc_encontrada and len(colunas_originais) >= 2: col_desc_encontrada = colunas_originais[1]
                    if not col_valor_encontrada and len(colunas_originais) >= 3: col_valor_encontrada = colunas_originais[-2]

                    if col_data_encontrada and col_desc_encontrada and col_valor_encontrada:
                        df_final = pd.DataFrame()
                        df_final['Data'] = df_temp[col_data_encontrada]
                        df_final['Descricao'] = df_temp[col_desc_encontrada]
                        
                        s_val = df_temp[col_valor_encontrada].astype(str)
                        s_val = s_val.str.replace('R$', '', regex=False).str.replace(' ', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        df_final['Valor'] = pd.to_numeric(s_val, errors='coerce').fillna(0).abs()
                        df_final['Origem'] = arquivo.name
                        dfs_processados.append(df_final)

        except Exception as e:
            st.sidebar.error(f"Erro no arquivo {arquivo.name}: {e}")

    if dfs_processados:
        df = pd.concat(dfs_processados, ignore_index=True)
        
        st.sidebar.success(f"✅ {len(arquivos_carregados)} arquivo(s) unificado(s) com sucesso!")
        
        # Filtra ruídos comuns de extrato bancário
        df = df[~df['Descricao'].str.lower().str.contains('saldo|rendimento|limite|transf. entre contas|total', na=False)]
        df = df[df['Valor'] > 0] # Remove valores zerados
        
        df['Categoria'] = df['Descricao'].apply(classificar_descricao)
        total_gasto = df['Valor'].sum()
        maior_gasto = df['Valor'].max() if not df.empty else 0

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
            if not df.empty:
                gastos_por_categoria = df.groupby('Categoria')['Valor'].sum()
                st.bar_chart(gastos_por_categoria)
            else:
                st.info("Nenhuma transação válida encontrada após os filtros.")

        with col_tabela:
            st.subheader("📋 Extrato Unificado")
            st.dataframe(df[['Data', 'Descricao', 'Categoria', 'Valor', 'Origem']], use_container_width=True)
    else:
        st.error("⚠️ Nenhum dos arquivos enviados possui colunas válidas reconhecíveis de Data, Descrição e Valor.")

else:
    st.info("👋 **Bem-vindo(a)!** Abra a barra lateral e selecione um ou mais extratos bancários (.csv, .xlsx ou .pdf) para gerar o relatório consolidado.")