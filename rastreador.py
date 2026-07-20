import re
import sys
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

try:
    import seaborn as sns
except ImportError:
    sns = None


def categorizar_gasto(descricao: str) -> str:
    texto = (descricao or "").strip()
    texto_lower = texto.lower()

    if re.search(r"\buber\b", texto, flags=re.IGNORECASE):
        return "transporte"

    if any(p in texto_lower for p in ["taxi", "transporte", "uber", "metro", "onibus", "estacionamento", "99taxi", "trem", "barca", "parking", "vlt", "moto", "bicicleta", "carro", "aluguel", "combustivel", "gasolina", "diesel", "etanol", "gas", "oleo", "lubrificante", "manutencao", "revisao", "lavagem", "detalhamento", "carwash"]):
        return "transporte"
    if any(p in texto_lower for p in ["netflix", "spotify", "primevideo", "assinatura", "google", "dropbox", "youtube", "amazonprime", "hbo", "disneyplus", "globoplay", "deezer", "twitch", "skype", "zoom", "office365", "adobe", "canva", "notion", "slack", "trello", "evernote"]):
        return "assinaturas"
    if any(p in texto_lower for p in ["saque", "transferencia", "pagamento", "conta", "boleto", "juros", "imposto", "taxa", "tarifa", "cartao", "debito", "credito", "deposito", "pix", "recarga", "recibo", "fatura", "parcelamento", "emprestimo", "financiamento", "investimento", "rendimento", "dividendo", "lucro", "perda", "despesa", "receita", "saldo", "extrato", "resgate", "aporte", "aporteextra", "aporteadicional"]):
        return "saidas"
    if any(p in texto_lower for p in ["mcdonald", "burgerking", "pizza", "habib", "subway", "kfc", "ifood", "99food", "delivery", "fastfood", "lanchonete", "restaurante", "comida", "alimentacao", "refeicao", "lanche", "snack", "sanduiche", "hamburguer", "batatafrita", "salgado", "pizza", "pizzaria", "churrasco", "rodizio", "selfservice", "buffet", "comidacaseira", "comidasaudavel", "comidavegetariana", "comidavegana", "comidajaponesa", "comidachinesa", "comidaitaliana", "comidafrancesa", "comidaindiana", "comidaamericana", "comidaafricana", "comidaoriental"]):
        return "fast_food"
    return "outros"


def localizar_coluna(df: pd.DataFrame, nomes: list[str]) -> Optional[str]:
    colunas_lower = {col.lower(): col for col in df.columns}
    for nome in nomes:
        if nome.lower() in colunas_lower:
            return colunas_lower[nome.lower()]
    return None


def inferir_mes_ano(path: Path, df: pd.DataFrame) -> str:
    texto = path.stem.lower()
    padrao = re.search(r"(\d{4})[-_. ]?(\d{1,2})", texto)
    if padrao:
        ano, mes = padrao.groups()
        return f"{ano}-{int(mes):02d}"

    for mes_nome, numero in {
        "jan": 1,
        "janeiro": 1,
        "fev": 2,
        "fevereiro": 2,
        "mar": 3,
        "marco": 3,
        "abr": 4,
        "abril": 4,
        "mai": 5,
        "maio": 5,
        "jun": 6,
        "junho": 6,
        "jul": 7,
        "julho": 7,
        "ago": 8,
        "agosto": 8,
        "set": 9,
        "setembro": 9,
        "out": 10,
        "outubro": 10,
        "nov": 11,
        "novembro": 11,
        "dez": 12,
        "dezembro": 12,
    }.items():
        if mes_nome in texto:
            for ano_match in re.findall(r"(\d{4})", texto):
                return f"{ano_match}-{numero:02d}"

    for coluna in df.columns:
        nome_col = coluna.lower()
        if "data" in nome_col or "date" in nome_col or "mes" in nome_col:
            serie = pd.to_datetime(df[coluna], errors="coerce")
            if serie.notna().any():
                data_valida = serie.dropna().iloc[0]
                return data_valida.to_period("M").strftime("%Y-%m")

    data_modificacao = pd.Timestamp(path.stat().st_mtime, unit="s")
    return data_modificacao.to_period("M").strftime("%Y-%m")


def carregar_arquivo(caminho: str | Path) -> pd.DataFrame:
    path = Path(caminho)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
            linhas = handle.read().splitlines()
        if not linhas:
            raise ValueError("O arquivo CSV está vazio.")

        delimitador = ";" if ";" in linhas[0] else ","
        if any(coluna.lower() in {"descricao", "description", "historico", "histórico", "detalhes", "observacao", "observações", "descrição", "valor", "amount", "gasto", "montante", "valor_gasto"} for coluna in linhas[0].split(delimitador)):
            df = pd.read_csv(path, sep=delimitador, engine="python")
        else:
            df = pd.read_csv(path, sep=delimitador, header=None, engine="python")
            if df.shape[1] >= 2:
                df.columns = ["descricao", "valor"]
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError("Formato não suportado. Use CSV ou Excel.")

    descricao_col = localizar_coluna(df, ["descricao", "description", "historico", "histórico", "detalhes", "observacao", "observações", "descrição"])
    valor_col = localizar_coluna(df, ["valor", "amount", "valor_total", "total", "gasto", "montante", "valor_gasto"])

    if not descricao_col or not valor_col:
        raise ValueError("O arquivo deve conter colunas semelhantes a 'descricao' e 'valor'.")

    df = df.rename(columns={descricao_col: "descricao", valor_col: "valor"})
    df["valor"] = df["valor"].astype(str).str.replace("R$", "", regex=False)
    df["valor"] = df["valor"].astype(str).str.replace(".", "", regex=False)
    df["valor"] = df["valor"].astype(str).str.replace(",", ".", regex=False)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    df["descricao"] = df["descricao"].fillna("").astype(str)
    df["categoria"] = df["descricao"].apply(categorizar_gasto)
    df["mes_ano"] = inferir_mes_ano(path, df)
    df["arquivo_origem"] = path.name
    return df


def carregar_dados(caminho: str | Path) -> pd.DataFrame:
    path = Path(caminho)
    if not path.exists():
        raise FileNotFoundError(f"Caminho não encontrado: {caminho}")

    if path.is_dir():
        arquivos = [
            arquivo
            for arquivo in sorted(path.iterdir())
            if arquivo.is_file() and arquivo.suffix.lower() in {".csv", ".xlsx", ".xls"}
        ]
        if not arquivos:
            raise FileNotFoundError(f"Nenhum arquivo CSV/Excel encontrado na pasta: {caminho}")

        frames = [carregar_arquivo(arquivo) for arquivo in arquivos]
        return pd.concat(frames, ignore_index=True)

    return carregar_arquivo(path)


def gerar_relatorio_anual(df: pd.DataFrame, saida: str = "relatorio_anual.csv") -> str:
    relatorio = (
        df.assign(valor_gasto=df["valor"].abs())
        .groupby(["mes_ano", "categoria"], as_index=False)["valor_gasto"]
        .sum()
        .sort_values(["mes_ano", "categoria"])
    )
    relatorio.to_csv(saida, index=False)
    return saida


def gerar_grafico_mensal(df: pd.DataFrame, saida: str = "grafico_gastos_mensais.png") -> str:
    mensal = (
        df.assign(valor_gasto=df["valor"].abs())
        .groupby("mes_ano", as_index=False)["valor_gasto"]
        .sum()
        .sort_values("mes_ano")
    )
    mensal["mes_ano"] = pd.to_datetime(mensal["mes_ano"])

    if sns is not None:
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(10, 5))
        ax = sns.lineplot(data=mensal, x="mes_ano", y="valor_gasto", marker="o")
    else:
        plt.style.use("ggplot")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(mensal["mes_ano"], mensal["valor_gasto"], marker="o")

    ax.set_title("Evolução mensal dos gastos")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Total gasto")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(saida, dpi=300)
    plt.close()
    return saida


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python rastreador.py <arquivo.csv|arquivo.xlsx|pasta>")
        print("Exemplo: python rastreador.py extratos/ ")
        return

    entrada = sys.argv[1]
    relatorio_saida = sys.argv[2] if len(sys.argv) > 2 else "relatorio_anual.csv"
    grafico_saida = sys.argv[3] if len(sys.argv) > 3 else "grafico_gastos_mensais.png"

    try:
        df = carregar_dados(entrada)
        print(df[["descricao", "valor", "categoria", "mes_ano"]].head())
        caminho_relatorio = gerar_relatorio_anual(df, relatorio_saida)
        caminho_grafico = gerar_grafico_mensal(df, grafico_saida)
        print(f"Relatório anual salvo em: {caminho_relatorio}")
        print(f"Gráfico salvo em: {caminho_grafico}")
    except Exception as exc:
        print(f"Erro: {exc}")


if __name__ == "__main__":
    main()
