import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("rastreador", Path(__file__).with_name("rastreador.py"))
rastreador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rastreador)


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


if __name__ == "__main__":
    unittest.main()
