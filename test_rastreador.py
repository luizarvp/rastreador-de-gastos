import importlib.util
import sys
import types
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("rastreador", Path(__file__).with_name("rastreador.py"))
rastreador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rastreador)


class DummySidebar:
    def __getattr__(self, name):
        def method(*args, **kwargs):
            return None
        return method


class DummyColumn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyStreamlit(types.SimpleNamespace):
    def __init__(self):
        super().__init__(sidebar=DummySidebar())

    def set_page_config(self, *args, **kwargs):
        return None

    def title(self, *args, **kwargs):
        return None

    def markdown(self, *args, **kwargs):
        return None

    def columns(self, specs):
        return [DummyColumn() for _ in range(len(specs))]

    def subheader(self, *args, **kwargs):
        return None

    def bar_chart(self, *args, **kwargs):
        return None

    def dataframe(self, *args, **kwargs):
        return None

    def metric(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None


sys.modules['streamlit'] = DummyStreamlit()

app_spec = importlib.util.spec_from_file_location("app", Path(__file__).with_name("app.py"))
app = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app)


class RastreadorTests(unittest.TestCase):
    def test_categorizar_gasto(self):
        resultado = rastreador.categorizar_gasto("Uber")
        self.assertEqual(resultado, "transporte")

        resultado = rastreador.categorizar_gasto("PAGAMENTO UBER EATS")
        self.assertEqual(resultado, "transporte")

        resultado = rastreador.categorizar_gasto("Netflix")
        self.assertEqual(resultado, "assinaturas")

        resultado = rastreador.categorizar_gasto("McDonald's")
        self.assertEqual(resultado, "fast_food")

    def test_carregar_dados_de_pasta(self):
        with tempfile.TemporaryDirectory() as pasta_temporaria:
            pasta = Path(pasta_temporaria)
            (pasta / "2024-01.csv").write_text("descricao,valor\nUber,20\nNetflix,15\n", encoding="utf-8")
            (pasta / "2024-02.csv").write_text("descricao,valor\nMcDonald's,30\nSaque,50\n", encoding="utf-8")

            df = rastreador.carregar_dados(pasta)

            self.assertEqual(set(df["mes_ano"]), {"2024-01", "2024-02"})
            self.assertIn("transporte", df["categoria"].values)
            self.assertIn("fast_food", df["categoria"].values)

    def test_carregar_arquivo_com_separador_e_moeda(self):
        with tempfile.TemporaryDirectory() as pasta_temporaria:
            pasta = Path(pasta_temporaria)
            arquivo = pasta / "2024-03.csv"
            arquivo.write_text("Descrição;Valor\nUber;R$ 20,50\nNetflix;R$ 15,00\n", encoding="utf-8")

            df = rastreador.carregar_dados(arquivo)

            self.assertEqual(df.loc[0, "categoria"], "transporte")
            self.assertAlmostEqual(df.loc[0, "valor"], 20.5)
            self.assertEqual(df.loc[1, "categoria"], "assinaturas")

    def test_extrair_valor_monetario_usa_o_valor_real_no_fim_da_linha(self):
        texto = "17/06/2026 PIX Q NOME FANTASIA 60.263.728,00 2,50"

        resultado = app._extrair_valor_monetario(texto)

        self.assertAlmostEqual(resultado, 2.5)


if __name__ == "__main__":
    unittest.main()
