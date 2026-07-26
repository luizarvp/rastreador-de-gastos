import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import tempfile
import os
import re
import zipfile
import xml.etree.ElementTree as ET
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except Exception:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except Exception:
    PdfReader = None
    PYPDF_AVAILABLE = False

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
    'netflix': 'Assinaturas digitais',
    'twitch': 'Assinaturas digitais',
    'microsoft 365': 'Assinaturas digitais',
    'ebanx': 'Assinaturas digitais',
    'onedrive': 'Assinaturas digitais',

    
    # Supermercado
    'guanabara': 'Supermercado',
    'carrefour': 'Supermercado',
    'prezunic': 'Supermercado',
    'supermarket': 'Supermercado',
    'mundial': 'Supermercado',
    'vianense': 'Supermercado',
    'multimarket': 'Supermercado',
    'mercadinho': 'Supermercado',
    'mercado': 'Supermercado',
    'rede economia': 'Supermercado',

    
    # Animais
    'petshop': 'Animais de estimação',
    'clinica': 'Animais de estimação',
    'veterinario': 'Animais de estimação',
    'veterinário': 'Animais de estimação',
    'banho e tosa': 'Animais de estimação',
    'american pet': 'Animais de estimação',
    'pet love': 'Animais de estimação',

    
    # Cartão
    'fatura': 'Cartão de crédito',
    'cartao': 'Cartão de crédito',
    'cartão': 'Cartão de crédito',
    

    
    # Casa
    'iptu': 'Casa',
    'agua': 'Casa',
    'água': 'Casa',
    'luz': 'Casa',
    'aluguel': 'Casa',
    'tv a cabo': 'Casa',
    'internet': 'Casa',
    'telefone': 'Casa',
    'gas': 'Casa',
    'gás': 'Casa',
    'taxa de incendio': 'Casa',
    'taxa de incêndio': 'Casa',
    'condominio': 'Casa',
    'condomínio': 'Casa',

    
    # Comida e bebida
    '99food': 'Comida e bebida',
    'mcdonald': 'Comida e bebida',
    'ifood': 'Comida e bebida',
    'burgerking': 'Comida e bebida',
    'padaria': 'Comida e bebida',
    'mercearia': 'Supermercado',
    'minimercado': 'Supermercado',
    'restaurante': 'Comida e bebida',
    'lanchonete': 'Comida e bebida',
    'bar': 'Comida e bebida',
    'cafeteria': 'Comida e bebida',
    'pizzaria': 'Comida e bebida',
    'churrascaria': 'Comida e bebida',
    'sorveteria': 'Comida e bebida',
    'starbucks': 'Comida e bebida',
    'california coffee': 'Comida e bebida',
    'subway': 'Comida e bebida',

    
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
    'app store': 'Compras diversas',
    'pichau': 'Compras diversas',
    'terabyte': 'Compras diversas',
    'kabum': 'Compras diversas',
    'americanas': 'Compras diversas',

    
    # Educação
    'livraria': 'Educação',
    'faculdade': 'Educação',
    'escola': 'Educação',
    'mensalidade': 'Educação',
    'creche': 'Educação',
    'curso': 'Educação',
    'colegio': 'Educação',
    'colégio': 'Educação',
    'universidade': 'Educação',
    'instituto': 'Educação',
    'educacional': 'Educação',
    'ensino': 'Educação',

    
    # Saúde e cuidados pessoais
    'droga raia': 'Saúde e cuidados pessoais',
    'drogasil': 'Saúde e cuidados pessoais',
    'pacheco': 'Saúde e cuidados pessoais',
    'venancio': 'Saúde e cuidados pessoais',
    'venâncio': 'Saúde e cuidados pessoais',
    'barbearia': 'Saúde e cuidados pessoais',
    'beleza': 'Saúde e cuidados pessoais',
    'academia': 'Saúde e cuidados pessoais',
    'odonto': 'Saúde e cuidados pessoais',
    'natura': 'Saúde e cuidados pessoais',
    'sephora': 'Saúde e cuidados pessoais',
    'boticario': 'Saúde e cuidados pessoais',
    'boticário': 'Saúde e cuidados pessoais',
    'consultas medicas': 'Saúde e cuidados pessoais',
    'consultas médicas': 'Saúde e cuidados pessoais',
    'plano de saude': 'Saúde e cuidados pessoais',
    'plano de saúde': 'Saúde e cuidados pessoais',

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
    'greencar': 'Transporte',

    
    # Transferências
    'pix': 'Transferências',
    'transferencia': 'Transferências',
    'transferência': 'Transferências',

    # Receitas
    'salario': 'Salário',
    'salário': 'Salário',
    'remuneracao': 'Salário',
    'remuneração': 'Salário',
    'pagamento de salario': 'Salário',
    'pagamento de salário': 'Salário',
}


def classificar_descricao(texto_bruto):
    texto_min = str(texto_bruto).lower()
    for palavra_chave, categoria in REGRAS_CATEGORIA.items():
        if palavra_chave in texto_min:
            return categoria
    return 'Outros'


def classificar_tipo(categoria):
    return 'Receita' if categoria == 'Salário' else 'Despesa'


def _normalizar_texto(texto):
    if texto is None:
        return ''
    texto = str(texto).replace('\xa0', ' ').strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def _extrair_data(texto):
    match_data = re.search(r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{1,2}[-/\.]\d{1,2})', str(texto))
    if not match_data:
        return None
    return match_data.group(0).replace('-', '/').replace('.', '/')


def _extrair_valor_monetario(texto):
    match_val = re.findall(r'R?\$?\s*([+-]?\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', str(texto))
    if not match_val:
        return None

    val_alvo = match_val[0] if len(match_val) == 1 else match_val[-2]
    val_str = val_alvo.replace('.', '').replace(',', '.')
    try:
        return abs(float(val_str))
    except Exception:
        return None


def _limpar_descricao(texto, data=None):
    descricao = str(texto or '').strip()
    if data:
        descricao = descricao.replace(data, '').strip()
    descricao = re.sub(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*', '', descricao)
    descricao = re.sub(r'^\d{1,2}:\d{2}\s*', '', descricao)
    descricao = re.sub(r'\b(?:R\$|RS|S/|\$)\b', '', descricao)
    descricao = re.sub(r'([+-]?\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', '', descricao)
    descricao = re.sub(r'\s+', ' ', descricao).strip(' -|/.,')
    descricao = descricao.strip()
    return descricao or 'Transação sem descrição'


def _criar_registro_de_texto(texto, origem, estrategia='generico'):
    texto_limpo = _normalizar_texto(texto)
    if not texto_limpo:
        return None

    if any(pal in texto_limpo.lower() for pal in ['entradas:', 'saídas:', 'saldo', 'total', 'extrato de', 'resumo', 'fatura', 'data', 'descrição', 'valor', 'histórico']):
        return None

    padrao_data = r'^(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:\d{1,2}:\d{2})?\s*(.*)$'

    if estrategia in {'mercado_pago', 'nubank', 'itau', 'santander', 'bradesco', 'caixa'}:
        match_data = re.match(padrao_data, texto_limpo)
        if match_data:
            data = _extrair_data(match_data.group(1))
            restante = match_data.group(2)
            valor = _extrair_valor_monetario(restante)
            if data and valor is not None:
                descricao = _limpar_descricao(restante, data)
                return {'Data': data, 'Descricao': descricao, 'Valor': valor, 'Origem': origem}

    data = _extrair_data(texto_limpo)
    valor = _extrair_valor_monetario(texto_limpo)
    if not data or valor is None:
        return None

    descricao = _limpar_descricao(texto_limpo, data)

    return {
        'Data': data,
        'Descricao': descricao,
        'Valor': valor,
        'Origem': origem,
    }


def _criar_registro_de_celulas(celulas, origem):
    valores = [str(celula or '').strip() for celula in celulas if str(celula or '').strip()]
    if len(valores) < 2:
        return None

    data_idx = None
    valor_idx = None
    for idx, valor in enumerate(valores):
        if data_idx is None and _extrair_data(valor):
            data_idx = idx
        if valor_idx is None and _extrair_valor_monetario(valor) is not None:
            valor_idx = idx

    if data_idx is None or valor_idx is None:
        return None

    data = _extrair_data(valores[data_idx])
    valor = _extrair_valor_monetario(valores[valor_idx])
    if not data or valor is None:
        return None

    descricao_candidatos = [
        _normalizar_texto(valores[idx])
        for idx in range(len(valores))
        if idx not in {data_idx, valor_idx}
    ]
    descricao = ' | '.join([d for d in descricao_candidatos if d])
    if not descricao:
        descricao = 'Transação sem descrição'

    descricao = re.sub(r'R?\$?\s*([+-]?\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})', '', descricao)
    descricao = re.sub(r'\s+', ' ', descricao).strip(' -|')
    if not descricao:
        descricao = 'Transação sem descrição'

    return {
        'Data': data,
        'Descricao': descricao,
        'Valor': valor,
        'Origem': origem,
    }


def _detectar_estrategia(texto, nome_arquivo=''):
    texto_min = str(texto or '').lower()
    nome_min = str(nome_arquivo or '').lower()
    texto_completo = f'{texto_min}\n{nome_min}'

    if 'mercado pago' in texto_completo or 'mercadopago' in texto_completo:
        return 'mercado_pago'
    if 'nubank' in texto_completo:
        return 'nubank'
    if 'itau' in texto_completo or 'itaú' in texto_completo:
        return 'itau'
    if 'santander' in texto_completo:
        return 'santander'
    if 'bradesco' in texto_completo:
        return 'bradesco'
    if 'caixa' in texto_completo:
        return 'caixa'
    if 'inter' in texto_completo:
        return 'inter'
    if 'banrisul' in texto_completo:
        return 'banrisul'
    return 'generico'


def _adicionar_registros_de_linhas(registros, linhas, origem, nome_arquivo=''):
    for linha in linhas:
        if not linha:
            continue
        if isinstance(linha, (list, tuple)):
            registro = _criar_registro_de_celulas(linha, origem)
            if registro is None:
                texto = ' | '.join(str(celula or '').strip() for celula in linha if str(celula or '').strip())
                estrategia = _detectar_estrategia(texto, nome_arquivo)
                registro = _criar_registro_de_texto(texto, origem, estrategia=estrategia)
        else:
            texto = str(linha).strip()
            estrategia = _detectar_estrategia(texto, nome_arquivo)
            registro = _criar_registro_de_texto(texto, origem, estrategia=estrategia)

        if registro is not None:
            registros.append(registro)


def extrair_tabela_de_pdf(arquivo_pdf):
    """Tenta extrair transações de PDFs por texto, tabelas e OCR.
    O fluxo usa várias estratégias para lidar com diferentes layouts de extrato
    e converte tudo para um DataFrame padronizado com Data/Descricao/Valor.
    """
    registros = []
    nome_arquivo = getattr(arquivo_pdf, 'name', 'pdf')

    try:
        arquivo_pdf.seek(0)
    except Exception:
        pass

    try:
        data = arquivo_pdf.read() if hasattr(arquivo_pdf, 'read') else arquivo_pdf
    except Exception:
        data = None

    origem = getattr(arquivo_pdf, 'name', 'pdf')

    if PYPDF_AVAILABLE and data is not None:
        try:
            reader = PdfReader(io.BytesIO(data))
            for pagina in reader.pages:
                texto = pagina.extract_text() or ''
                if texto:
                    _adicionar_registros_de_linhas(registros, texto.split('\n'), origem, nome_arquivo=nome_arquivo)
        except Exception:
            registros = []

    if not registros and PDFPLUMBER_AVAILABLE:
        try:
            pdf_stream = io.BytesIO(data) if data is not None else arquivo_pdf
            with pdfplumber.open(pdf_stream) as pdf:
                for pagina in pdf.pages:
                    tabelas = pagina.extract_tables()
                    if tabelas:
                        for tabela in tabelas:
                            for linha in tabela:
                                if linha is not None and any(str(celula or '').strip() for celula in linha):
                                    _adicionar_registros_de_linhas(registros, [linha], origem, nome_arquivo=nome_arquivo)

                    texto = pagina.extract_text()
                    if texto:
                        _adicionar_registros_de_linhas(registros, texto.split('\n'), origem, nome_arquivo=nome_arquivo)
        except Exception:
            registros = []

    if registros:
        df_final = pd.DataFrame(registros)
        return df_final[['Data', 'Descricao', 'Valor', 'Origem']]

    if not OCR_AVAILABLE:
        return pd.DataFrame()

    try:
        if 'POPPLER_PATH' in globals() and POPPLER_PATH:
            imagens = convert_from_bytes(data, dpi=300, poppler_path=POPPLER_PATH)
        else:
            imagens = convert_from_bytes(data, dpi=300)
    except Exception:
        return pd.DataFrame()

    for img in imagens:
        try:
            texto = pytesseract.image_to_string(img, lang='por+eng')
        except Exception:
            texto = pytesseract.image_to_string(img)
        _adicionar_registros_de_linhas(registros, texto.split('\n'), origem, nome_arquivo=nome_arquivo)

    if registros:
        df_final = pd.DataFrame(registros)
        return df_final[['Data', 'Descricao', 'Valor', 'Origem']]

    return pd.DataFrame()
def extrair_texto_de_docx(arquivo):
    try:
        arquivo.seek(0)
    except Exception:
        pass

    dados = arquivo.read() if hasattr(arquivo, 'read') else arquivo
    if not dados:
        return ''

    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as pacote:
            if 'word/document.xml' not in pacote.namelist():
                return ''
            xml_bytes = pacote.read('word/document.xml')
            root = ET.fromstring(xml_bytes)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            textos = []
            for paragrafo in root.findall('.//w:p', ns):
                partes = []
                for node in paragrafo.findall('.//w:t', ns):
                    if node.text:
                        partes.append(node.text)
                if partes:
                    textos.append(''.join(partes))
            return '\n'.join(textos)
    except Exception:
        return ''


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
    elif nome.endswith('.docx'):
        texto = extrair_texto_de_docx(arquivo)
        if texto:
            registros = []
            for linha in texto.split('\n'):
                registro = _criar_registro_de_texto(linha, arquivo.name, estrategia=_detectar_estrategia(linha, arquivo.name))
                if registro is not None:
                    registros.append(registro)
            if registros:
                return pd.DataFrame(registros)
    elif nome.endswith('.txt'):
        try:
            arquivo.seek(0)
        except Exception:
            pass
        texto = arquivo.read().decode('utf-8', errors='ignore') if hasattr(arquivo, 'read') else str(arquivo)
        registros = []
        for linha in texto.split('\n'):
            registro = _criar_registro_de_texto(linha, arquivo.name, estrategia=_detectar_estrategia(linha, arquivo.name))
            if registro is not None:
                registros.append(registro)
        if registros:
            return pd.DataFrame(registros)

    return pd.DataFrame()

# 2. BARRA LATERAL (Sidebar)
st.sidebar.header("📁 Importar Dados")
arquivos_carregados = st.sidebar.file_uploader(
"Carregue seus extratos (.csv, .xlsx, .pdf, .docx, .txt)", 
type=["csv", "xlsx", "xls", "pdf", "docx", "txt"],
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
        df['Tipo'] = df['Categoria'].apply(classificar_tipo)

        despesas = df[df['Tipo'] == 'Despesa']
        receitas = df[df['Tipo'] == 'Receita']

        total_despesa = despesas['Valor'].sum() if not despesas.empty else 0
        total_receita = receitas['Valor'].sum() if not receitas.empty else 0
        saldo = total_receita - total_despesa
        maior_despesa = despesas['Valor'].max() if not despesas.empty else 0
        maior_receita = receitas['Valor'].max() if not receitas.empty else 0

        # 4. LAYOUT: Métricas Consolidadas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total Receitas", value=f"R$ {total_receita:,.2f}")
        with col2:
            st.metric(label="Total Despesas", value=f"R$ {total_despesa:,.2f}")
        with col3:
            st.metric(label="Saldo", value=f"R$ {saldo:,.2f}")
        with col4:
            st.metric(label="Total de Transações", value=f"{len(df)} registros")

        st.markdown("---")

        # 5. LAYOUT: Gráfico e Tabela Unificada
        col_grafico, col_tabela = st.columns([3, 2])

        with col_grafico:
            st.subheader("📈 Despesas por Categoria")
            if not despesas.empty:
                gastos_por_categoria = despesas.groupby('Categoria')['Valor'].sum()
                st.bar_chart(gastos_por_categoria)
            else:
                st.info("Nenhuma despesa válida encontrada após os filtros.")

            if not receitas.empty:
                st.subheader("💰 Receitas por Categoria")
                receitas_por_categoria = receitas.groupby('Categoria')['Valor'].sum()
                st.bar_chart(receitas_por_categoria)

        with col_tabela:
            st.subheader("📋 Extrato Unificado")
            st.dataframe(df[['Data', 'Descricao', 'Tipo', 'Categoria', 'Valor', 'Origem']], use_container_width=True)
    else:
        st.error("⚠️ Nenhum dos arquivos enviados possui colunas válidas reconhecíveis de Data, Descrição e Valor.")

else:
    st.info("👋 **Bem-vindo(a)!** Abra a barra lateral e selecione um ou mais extratos bancários (.csv, .xlsx ou .pdf) para gerar o relatório consolidado.")