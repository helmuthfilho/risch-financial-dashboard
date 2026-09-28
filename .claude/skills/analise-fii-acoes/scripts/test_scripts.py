"""Testes da lógica pura dos scripts (sem rede).

Rodar da raiz do repo:
  python3 -m unittest discover -s .claude/skills/analise-fii-acoes/scripts -p "test_*.py"
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from _comum import fmt_mi, fmt_pct, load_env, quarter_label, to_cents, to_scaled_int
from cvm_cia import contas_por_nome, resumir_pareceres, ENFASE_RX, INCERTEZA_RX, LL_RX, TICKER_RX, Dados, core_setor, leaves_only, mesmo_setor, month_diff, months_between
from cotacao import PLANOS, adapt, amostra, learn, load_plano, permitidos
from proventos import completude, dedupe_proventos, parse_aviso
from cvm_fii import norm_txt, ticker_from_isin
from documentos import fnet_dedupe, ipe_dedupe, iso_ref, quarter_key, slug


class ToScaledIntTest(unittest.TestCase):
    def test_valores_da_cvm(self):
        self.assertEqual(to_cents("123144000.0000000000"), 12314400000)
        self.assertEqual(to_cents("258202136.67"), 25820213667)

    def test_arredonda_meio_para_cima_sem_float(self):
        self.assertEqual(to_cents("9.995"), 1000)
        self.assertEqual(to_cents("-5.555"), -556)
        self.assertEqual(to_cents("0.004"), 0)
        self.assertEqual(to_cents("0.005"), 1)

    def test_notacao_cientifica_e_virgula(self):
        self.assertEqual(to_scaled_int("2.5E-05", 8), 2500)
        self.assertEqual(to_cents("1,5"), 150)

    def test_vazio(self):
        self.assertIsNone(to_cents(""))
        self.assertIsNone(to_cents(None))

    def test_precisao_de_provento(self):
        self.assertEqual(to_scaled_int("0.35048637", 8), 35048637)


class FormatoTest(unittest.TestCase):
    def test_fmt(self):
        self.assertEqual(fmt_mi(12314400000000), "123.144")
        self.assertEqual(fmt_mi(12345000000), "123,5")
        self.assertEqual(fmt_pct(0.004342, 2), "0,43%")
        self.assertEqual(fmt_mi(None), "-")
        self.assertEqual(quarter_label("2026-06-30"), "2T26")

    def test_ticker_isin_e_nomes(self):
        self.assertEqual(ticker_from_isin("BRHGLGCTF004"), "HGLG11")
        self.assertEqual(iso_ref("31/08/2026"), "20260831")
        self.assertEqual(iso_ref("08/2026"), "202608")
        self.assertEqual(slug("Relatório Gerencial"), "relatorio-gerencial")


class EnvTest(unittest.TestCase):
    def test_nao_sobrescreve_ambiente_e_tira_aspas(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text('# c\nX_TESTE_A="abc"\nexport X_TESTE_B=1\nX_TESTE_C=nao\n', encoding="utf-8")
            os.environ["X_TESTE_C"] = "sim"
            load_env(p)
            self.assertEqual(os.environ["X_TESTE_A"], "abc")
            self.assertEqual(os.environ["X_TESTE_B"], "1")
            self.assertEqual(os.environ["X_TESTE_C"], "sim")


def linha(st, fim, ini, cd, v, ds="conta"):
    return {"st": st, "ref": fim, "ver": 1, "ini": ini, "fim": fim, "cd": cd, "ds": ds, "v": v}


class DadosTest(unittest.TestCase):
    def test_meses(self):
        self.assertEqual(months_between("2026-01-01", "2026-03-31"), 3)
        self.assertEqual(months_between("2026-04-01", "2026-06-30"), 3)
        self.assertEqual(months_between("2026-01-01", "2026-12-31"), 12)
        self.assertEqual(month_diff("2026-09-30", "2026-12-31"), 3)

    def test_dre_usa_3m_do_itr_e_4t_da_dfp(self):
        ls = [
            linha("DRE", "2025-03-31", "2025-01-01", "3.01", 100),
            linha("DRE", "2025-06-30", "2025-01-01", "3.01", 250),
            linha("DRE", "2025-06-30", "2025-04-01", "3.01", 150),
            linha("DRE", "2025-09-30", "2025-01-01", "3.01", 450),
            linha("DRE", "2025-09-30", "2025-07-01", "3.01", 200),
            linha("DRE", "2025-12-31", "2025-01-01", "3.01", 700),  # DFP anual
        ]
        d = Dados(ls)
        self.assertEqual([d.f("DRE", e, "3.01") for e in d.periods], [100, 150, 200, 250])

    def test_dfc_acumulada_vira_trimestral(self):
        ls = [
            linha("DFC", "2025-03-31", "2025-01-01", "6.01", 10),
            linha("DFC", "2025-06-30", "2025-01-01", "6.01", 25),
            linha("DFC", "2025-09-30", "2025-01-01", "6.01", 30),
            linha("DFC", "2025-12-31", "2025-01-01", "6.01", 70),
            linha("DRE", "2025-03-31", "2025-01-01", "3.01", 1),
        ]
        d = Dados(ls)
        self.assertEqual(
            [d.f("DFC", e, "6.01") for e in ("2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31")], [10, 15, 5, 40]
        )

    def test_trimestre_sem_anterior_fica_vazio(self):
        ls = [linha("DFC", "2025-09-30", "2025-01-01", "6.01", 30)]
        self.assertIsNone(Dados(ls).f("DFC", "2025-09-30", "6.01"))

    def test_balanco_e_busca_por_nome(self):
        ls = [
            linha("BPP", "2025-06-30", "", "2.08", 500, "Patrimônio Líquido Consolidado"),
            linha("BPP", "2025-06-30", "", "2.08.01", 400, "Capital Social Realizado"),
        ]
        d = Dados(ls)
        self.assertEqual(d.b("2025-06-30", "2.08"), 500)
        self.assertEqual(d.find("BPP", r"^patrim[ôo]nio l[íi]quido", "2.", max_level=2), ["2.08"])

    def test_lucro_controladores_com_codigo_trocado_e_filtro_de_pai(self):
        ll = "Lucro/Prejuízo Consolidado do Período"
        ctrl = "Atribuído a Sócios da Empresa Controladora"
        ls = [
            # 1T/2T: lucro em 3.11, controladores em 3.11.01; linha homônima sob outro pai (3.09.01)
            linha("DRE", "2025-03-31", "2025-01-01", "3.11", 100, ll),
            linha("DRE", "2025-03-31", "2025-01-01", "3.11.01", 90, ctrl),
            linha("DRE", "2025-03-31", "2025-01-01", "3.09", 999, "Lucro antes das Participações"),
            linha("DRE", "2025-03-31", "2025-01-01", "3.09.01", 888, ctrl),
            linha("DRE", "2025-06-30", "2025-01-01", "3.11", 250, ll),
            linha("DRE", "2025-06-30", "2025-01-01", "3.11.01", 220, ctrl),
            # DFP: código mudou para 3.13 / 3.13.02
            linha("DRE", "2025-12-31", "2025-01-01", "3.13", 500, ll),
            linha("DRE", "2025-12-31", "2025-01-01", "3.13.02", 450, ctrl),
            linha("DRE", "2025-12-31", "2025-01-01", "3.13.01", 50, "Atribuído a Sócios Não Controladores"),
        ]
        d = Dados(ls)
        from cvm_cia import LL_RX as rx

        tot = d.serie_por_nome("DRE", rx, prefixo="3.", nivel=2, ausente_zero=False)
        ctl = d.serie_por_nome("DRE", "controlador", r"n[ãa]o\s+controlador", "3.", nivel=3, pai=rx, ausente_zero=False)
        self.assertEqual(tot["2025-03-31"], 100)
        self.assertEqual(tot["2025-06-30"], 150)
        self.assertEqual(ctl["2025-03-31"], 90)  # ignora o 3.09.01 (pai não é o lucro líquido)
        self.assertEqual(ctl["2025-06-30"], 130)
        self.assertIsNone(ctl["2025-12-31"])  # sem o 3T não há como isolar o 4T
        # período sem a conta: None (não 0) quando ausente_zero=False
        ls2 = [linha("DRE", "2025-03-31", "2025-01-01", "3.01", 10, "Receita")]
        self.assertIsNone(Dados(ls2).serie_por_nome("DRE", rx, prefixo="3.", ausente_zero=False)["2025-03-31"])
        self.assertEqual(Dados(ls2).serie_por_nome("DRE", rx, prefixo="3.")["2025-03-31"], 0)

    def test_serie_por_nome_prefere_coluna_de_3_meses(self):
        ll = "Lucro/Prejuízo Consolidado do Período"
        ls = [
            linha("DRE", "2026-03-31", "2026-01-01", "3.11", 1749, ll),
            linha("DRE", "2026-06-30", "2026-01-01", "3.11", 3213, ll),
            linha("DRE", "2026-06-30", "2026-04-01", "3.11", 1464, ll),  # 3 meses (ITR)
        ]
        from cvm_cia import LL_RX as rx

        serie = Dados(ls).serie_por_nome("DRE", rx, prefixo="3.", nivel=2, ausente_zero=False)
        self.assertEqual(serie["2026-06-30"], 1464)  # e não 3213 - 1749 = 1464 por acaso: usa a coluna
        # sem o acumulado anterior, ainda assim o trimestre sai pela coluna de 3 meses
        serie2 = Dados(ls[1:]).serie_por_nome("DRE", rx, prefixo="3.", nivel=2, ausente_zero=False)
        self.assertEqual(serie2["2026-06-30"], 1464)

    def test_saldo_por_nome_com_codigo_trocado(self):
        ls = [
            linha("BPP", "2025-09-30", "", "2.01.05", 100, "Dividendos e JCP a Pagar"),
            linha("BPP", "2025-12-31", "", "2.01.07", 300, "Dividendos e JCP a Pagar"),
            linha("BPP", "2025-12-31", "", "2.01.05", 999, "Fornecedores"),
        ]
        d = Dados(ls)
        usadas: dict = {}
        saldo = d.saldo_por_nome("BPP", r"dividend", prefixo="2", contas_usadas=usadas)
        self.assertEqual(saldo, {"2025-09-30": 100, "2025-12-31": 300})
        self.assertEqual(usadas["2025-12-31"], ["2.01.07"])

    def test_contas_por_nome_filtros(self):
        nomes = {"6.03": "Caixa Financiamento", "6.03.07": "Pagamento de dividendos e JCP",
                 "6.03.10": "Dividendos pagos a não controladores", "6.03.07.01": "Dividendos"}
        self.assertEqual(contas_por_nome(nomes, "dividend", r"n[ãa]o controlador", "6.03"), ["6.03.07.01"])
        self.assertEqual(contas_por_nome(nomes, "dividend", r"n[ãa]o controlador", "6.03", nivel=3), ["6.03.07"])

    def test_leaves_only(self):
        self.assertEqual(leaves_only(["6.02.01", "6.02.01.01", "6.02.03"]), ["6.02.01.01", "6.02.03"])


def ipe(id_, ref, entrega, assunto, versao="1"):
    return {"_id": id_, "Data_Referencia": ref, "Data_Entrega": entrega, "Assunto": assunto, "Versao": versao,
            "Categoria": "Dados Econômico-Financeiros", "Tipo": "Press-release"}


class DedupeTest(unittest.TestCase):
    def test_quarter_key(self):
        self.assertEqual(quarter_key("2026-03-30"), "2026T1")
        self.assertEqual(quarter_key("2025-12-31"), "2025T4")

    def test_release_fica_com_a_entrega_mais_recente_do_trimestre(self):
        docs = [
            ipe("100", "2026-03-30", "2026-05-11", "Relatório de Desempenho 1T26"),
            ipe("101", "2026-03-30", "2026-05-11", "Relatório de Desempenho 1T26", "2"),
            ipe("102", "2026-03-31", "2026-05-13", "Relatório de Desempenho 1T26"),
            ipe("200", "2026-06-30", "2026-08-06", "Relatório de Desempenho 2T26"),
        ]
        out = ipe_dedupe(docs, "release")
        self.assertEqual([d["_id"] for d in out], ["200", "102"])
        self.assertEqual(out[1]["_omitidos"], 2)

    def test_release_prefere_portugues_e_release_a_relatorio_da_administracao(self):
        docs = [
            ipe("1", "2025-12-31", "2026-03-12", "Release Resultados 4T25 Português"),
            ipe("2", "2025-12-31", "2026-03-12", "Release Resultados 4Q25 Inglês"),
            ipe("3", "2025-12-31", "2026-03-31", "Relatório da Administração 2025", "2"),
        ]
        self.assertEqual([d["_id"] for d in ipe_dedupe(docs, "release")], ["1"])

    def test_fatos_distintos_no_mesmo_trimestre_nao_sao_fundidos(self):
        docs = [
            ipe("1", "2026-08-06", "2026-08-06", "Remuneração aos acionistas"),
            ipe("2", "2026-09-19", "2026-09-19", "Nova subvenção"),
            ipe("3", "2026-09-19", "2026-09-20", "Nova subvenção", "2"),
        ]
        out = ipe_dedupe(docs, "fato")
        self.assertEqual([d["_id"] for d in out], ["3", "1"])

    def test_fnet_um_relatorio_por_mes_mais_recente(self):
        docs = [
            {"id": 3, "tipoDocumento": "Relatório Gerencial", "dataReferencia": "31/08/2026", "dataEntrega": "23/09/2026 21:35"},
            {"id": 2, "tipoDocumento": "Relatório Gerencial", "dataReferencia": "31/08/2026", "dataEntrega": "15/09/2026 10:00"},
            {"id": 1, "tipoDocumento": "Relatório Gerencial", "dataReferencia": "31/07/2026", "dataEntrega": "12/08/2026 19:43"},
        ]
        self.assertEqual([d["id"] for d in fnet_dedupe(docs, True)], [3, 1])


class PlanoBrapiTest(unittest.TestCase):
    MSG_RANGE = 'O range "1y" não está disponível no seu plano. Ranges permitidos: 1d, 5d, 1mo, 3mo. Faça upgrade'
    MSG_DIV = "Dividendos e JCP requer o plano Startup (R$ 119,99/mês). Seu plano atual: Gratuito."

    def test_permitidos(self):
        self.assertEqual(permitidos(self.MSG_RANGE), ["1d", "5d", "1mo", "3mo"])
        self.assertEqual(permitidos("sem lista"), [])

    def test_aprende_e_adapta(self):
        plano: dict = {}
        params = {"dividends": "true", "range": "1y", "interval": "1mo"}
        self.assertTrue(learn(plano, self.MSG_DIV, params))
        self.assertTrue(learn(plano, self.MSG_RANGE, params))
        self.assertFalse(learn(plano, "erro qualquer", {"range": "1y"}))
        eff, notas = adapt(params, plano)
        self.assertEqual(eff, {"range": "3mo", "interval": "1mo"})
        self.assertEqual(len(notas), 2)

    def test_nao_aprende_recurso_nao_pedido(self):
        self.assertFalse(learn({}, self.MSG_DIV, {"fundamental": "true"}))

    def test_amostra_mantem_ultimo(self):
        hist = [{"i": i} for i in range(64)]
        out = amostra(hist)
        self.assertLessEqual(len(out), 25)
        self.assertIs(out[-1], hist[-1])
        self.assertEqual(amostra(hist[:10]), hist[:10])

    def test_segmento_sem_acento(self):
        self.assertEqual(norm_txt(" Logística "), norm_txt("logistica"))


class PlanoDeclaradoTest(unittest.TestCase):
    def test_gratuito_ja_sai_sem_proventos(self):
        antigo = os.environ.get("BRAPI_PLANO")
        os.environ["BRAPI_PLANO"] = "Gratuito"
        try:
            with tempfile.TemporaryDirectory() as d:
                import _comum

                cache_antigo = _comum.CACHE_DIR
                _comum.CACHE_DIR = Path(d)
                try:
                    plano = load_plano()
                finally:
                    _comum.CACHE_DIR = cache_antigo
        finally:
            if antigo is None:
                os.environ.pop("BRAPI_PLANO", None)
            else:
                os.environ["BRAPI_PLANO"] = antigo
        eff, _ = adapt({"dividends": "true", "fundamental": "true"}, plano)
        self.assertEqual(eff, {"fundamental": "true"})
        self.assertIs(plano["agrupado"], False)
        self.assertEqual(PLANOS["gratuito"]["intervals"], ["1d"])


AVISO = b"""<?xml version="1.0" encoding="UTF-8"?>
<DadosEconomicoFinanceiros><InformeRendimentos>
<Provento><CodISIN>BRHGLGCTF004</CodISIN><CodNegociacao>HGLG11</CodNegociacao>
<Rendimento><DataBase>2026-08-31</DataBase><ValorProvento>1.17</ValorProvento>
<DataPagamento>2026-09-15</DataPagamento><PeriodoReferencia>AGOSTO</PeriodoReferencia>
<RendimentoIsentoIR>Sim</RendimentoIsentoIR></Rendimento>
<Amortizacao><DataBase>2026-08-31</DataBase><ValorProvento>0.5</ValorProvento></Amortizacao>
</Provento>
<Provento><CodNegociacao>HGLG12</CodNegociacao>
<Rendimento><DataBase>2026-08-31</DataBase><ValorProvento>9.99</ValorProvento></Rendimento>
</Provento></InformeRendimentos></DadosEconomicoFinanceiros>"""


class ProventosTest(unittest.TestCase):
    def test_parse_aviso_filtra_ticker_e_separa_amortizacao(self):
        itens = parse_aviso(AVISO, "hglg11")
        self.assertEqual([(i["tipo"], i["valor_1e8"]) for i in itens], [("rendimento", 117000000), ("amortização", 50000000)])
        self.assertEqual(itens[0]["periodo"], "agosto")

    def test_reapresentacao_vale_a_ultima_entrega(self):
        a = {"tipo": "rendimento", "data_base": "2026-08-31", "valor_1e8": 1, "_entrega": "2026-08-31 10:00"}
        b = dict(a, valor_1e8=2, _entrega="2026-09-02 10:00")
        c = dict(a, data_base="2026-07-31", _entrega="2026-07-31 10:00")
        out = dedupe_proventos([a, c, b])
        self.assertEqual([i["valor_1e8"] for i in out], [2, 1])

    def test_completude_com_avisos_faltando(self):
        rend = [{"data_base": "2026-08-31"}, {"data_base": "2026-07-31"}]
        self.assertEqual(completude([], rend), (True, True))
        # faltou um mês antigo: DY 12m n/d, último ainda vale
        self.assertEqual(completude(["2026-03-31"], rend), (False, True))
        # faltou aviso da mesma data ou mais novo que o último: os dois n/d
        self.assertEqual(completude(["2026-08-31"], rend), (False, False))
        self.assertEqual(completude(["2026-09-30"], rend), (False, False))
        # data desconhecida: não dá para garantir o último
        self.assertEqual(completude([""], rend), (False, False))

    def test_serie_por_nome_com_codigo_trocado(self):
        # TAEE11: mesma conta em 6.03.09 nos ITRs e 6.03.07 na DFP
        ds = "Pagamento de dividendos e JCP"
        ls = [
            linha("DFC", "2025-06-30", "2025-01-01", "6.03.09", -428, ds),
            linha("DFC", "2025-09-30", "2025-01-01", "6.03.09", -621, ds),
            linha("DFC", "2025-09-30", "2025-01-01", "6.03.07", -50, "Pagamento de empréstimos"),
            linha("DFC", "2025-12-31", "2025-01-01", "6.03.07", -1021, ds),
            linha("DFC", "2025-12-31", "2025-01-01", "6.03.09", -30, "Aumento de capital"),
            linha("DFC", "2025-12-31", "2025-01-01", "6.03.10", -5, "Dividendos pagos a não controladores"),
        ]
        d = Dados(ls)
        serie = d.serie_por_nome("DFC", r"dividend", r"n[ãa]o controlador", "6.03")
        self.assertEqual(serie["2025-09-30"], -193)
        self.assertEqual(serie["2025-12-31"], -400)


class ParesCiaTest(unittest.TestCase):
    def test_holding_e_abreviacoes_contam_como_mesmo_setor(self):
        self.assertEqual(core_setor("Emp. Adm. Part. - Energia Elétrica"), "Energia Elétrica")
        self.assertTrue(mesmo_setor("Energia Elétrica", "Emp. Adm. Part. - Energia Elétrica"))
        self.assertTrue(mesmo_setor("Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração", "Construção Civil, Mat. Constr. e Decoração"))
        self.assertTrue(mesmo_setor("Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças", "Máquinas, Equipamentos, Veículos e Peças"))

    def test_setores_diferentes_nao_casam(self):
        self.assertFalse(mesmo_setor("Petróleo e Gás", "Petroquímicos e Borracha"))
        self.assertFalse(mesmo_setor("Serviços Transporte e Logística", "Serviços Médicos"))
        self.assertFalse(mesmo_setor("", "Bancos"))

    def test_nome_do_lucro_liquido(self):
        import re as _re

        for ds in (
            "Lucro/Prejuízo Consolidado do Período",
            "Lucro/Prejuízo do Período",
            "Lucro ou Prejuízo Líquido Consolidado do Período",
        ):
            self.assertTrue(_re.search(LL_RX, ds, _re.I), ds)
        self.assertFalse(_re.search(LL_RX, "Lucro ou Prejuízo das Operações Continuadas", _re.I))
        self.assertFalse(_re.search(LL_RX, "Lucro por Ação (R$/Ação)", _re.I))

    def test_parecer_texto_padrao_nao_dispara_alerta(self):
        padrao = (
            "Concluímos sobre a adequação do uso, pela Administração, da base contábil de continuidade "
            "operacional e, com base nas evidências de auditoria obtidas, se existe incerteza relevante em "
            "relação a eventos ou condições que possam levantar dúvida significativa"
        ).lower()
        self.assertIsNone(INCERTEZA_RX.search(padrao))
        self.assertIsNone(ENFASE_RX.search(padrao))
        real = "Incerteza relevante relacionada com a continuidade operacional\nChamamos a atenção...".lower()
        self.assertIsNotNone(INCERTEZA_RX.search(real))
        self.assertIsNotNone(ENFASE_RX.search("ênfase\nconforme nota 2".lower()) or ENFASE_RX.search("ênfase: conforme nota 2"))
        self.assertIsNotNone(ENFASE_RX.search("parágrafo de ênfase"))
        # caso real (Itaú 3T25): título colado no texto, sem quebra de linha
        itau = ("mobiliários.Ênfase - Informações comparativasChamamos a atenção para a Nota 2(a) às informações "
                "contábeis intermediárias condensadas que descreve...")
        self.assertIsNotNone(ENFASE_RX.search(itau))
        from cvm_cia import ENFASE_TEMA_RX
        self.assertEqual(ENFASE_TEMA_RX.search(itau).group(1).strip(" .-"), "Informações comparativas")
        from cvm_cia import tema_enfase
        self.assertEqual(tema_enfase(itau), "Informações comparativas")
        bb_dfp = "fundamentar nossa opinião.Chamamos a atenção para a Nota Explicativa nº 2 às demonstrações contábeis"
        self.assertEqual(tema_enfase(bb_dfp), "ver Nota Explicativa nº 2")
        # texto de responsabilidades do auditor não é ênfase
        self.assertIsNone(ENFASE_RX.search("se concluirmos que existe incerteza relevante, devemos chamar atenção em nosso relatório"))

    def test_pareceres_do_mesmo_periodo_sao_combinados(self):
        ps = [
            {"ref": "2025-03-31", "tipo": "Sem Ressalva", "enfase": True, "enfase_tema": "Valores comparativos", "incerteza": False},
            {"ref": "2025-03-31", "tipo": "Sem Ressalva", "enfase": False, "incerteza": False},  # linha vazia depois
            {"ref": "2025-06-30", "tipo": "Sem Ressalva", "enfase": False, "incerteza": False},
            {"ref": "2025-06-30", "tipo": "Com Ressalva", "enfase": False, "incerteza": True},
        ]
        out = resumir_pareceres(ps)
        self.assertEqual(out["2025-03-31"], "2025-03 Sem Ressalva (ênfase: Valores comparativos)")
        self.assertEqual(out["2025-06-30"], "2025-06 Com Ressalva (incerteza relevante sobre continuidade)")

    def test_ticker_valido(self):
        self.assertTrue(TICKER_RX.fullmatch("SANB11"))
        self.assertTrue(TICKER_RX.fullmatch("PETR4"))
        self.assertFalse(TICKER_RX.fullmatch("000000"))


class TermosPdfTest(unittest.TestCase):
    def test_sigla_curta_exige_palavra_inteira(self):
        try:
            from pdf_texto import norm, term_regex
        except SystemExit:
            self.skipTest("pdfplumber não instalado (venv da skill)")
        self.assertIsNone(term_regex("arr").search(norm("barris de petróleo")))
        self.assertIsNotNone(term_regex("arr").search(norm("o ARR cresceu")))
        self.assertIsNotNone(term_regex("inadimpl").search(norm("Inadimplência de 2%")))
        self.assertIsNotNone(term_regex("vacância").search(norm("VACANCIA fisica")))


if __name__ == "__main__":
    unittest.main()
