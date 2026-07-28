"""Travas de acesso da tela de Equipe.

Nasceu de um incidente: o gestor conseguiu se desativar e o workspace ficou
sem nenhum usuário ativo — sem caminho de volta a não ser pelo SQL Editor,
que é justamente o que a tela de Equipe existe para evitar.

A trava antiga só valia para o *último* gestor. Bastava existir um segundo
para o "Desativar" da sua própria linha voltar a ficar clicável; se esse
segundo já tivesse saído antes, o clique zerava a equipe. Os testes abaixo
cobrem os dois lados: a regra no repositório (que é quem barra de verdade) e
o botão na tela (que é quem impede o clique).
"""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from src.models import Perfil
from src.repo import catalog

EU = "g-1"


def _linha(id_: str, nome: str, *, gestor=False, admin=False, ativo=True) -> dict:
    return {
        "id": id_, "nome": nome, "email": f"{id_}@exemplo.com", "cargo": None,
        "gestor": gestor, "admin": admin, "ativo": ativo, "recusado": False,
    }


# --------------------------------------------------------------- o modelo


class TestPapel:
    def test_admin_gerencia_igual_gestor(self):
        assert Perfil.de_linha(_linha("a", "Ana", admin=True)).pode_gerenciar

    def test_membro_nao_gerencia(self):
        assert not Perfil.de_linha(_linha("m", "Beto")).pode_gerenciar

    def test_papel_nomeia_os_tres_niveis(self):
        assert Perfil.de_linha(_linha("a", "A", admin=True)).papel == "admin"
        assert Perfil.de_linha(_linha("g", "G", gestor=True)).papel == "gestor"
        assert Perfil.de_linha(_linha("m", "M")).papel == "membro"

    def test_banco_sem_a_coluna_admin_nao_quebra(self):
        """Antes do 07_admin.sql a coluna não existe; ninguém é admin."""
        linha = _linha("g", "G", gestor=True)
        del linha["admin"]
        assert Perfil.de_linha(linha).papel == "gestor"

    def test_cargo_admin_antigo_continua_valendo(self):
        linha = _linha("c", "Carla") | {"cargo": "Administrador"}
        assert Perfil.de_linha(linha).pode_gerenciar


# ----------------------------------------------------------- o repositório


@pytest.fixture
def equipe(monkeypatch):
    """Devolve uma função que instala a equipe e registra quem está logado."""
    escritas: list[tuple[str, dict]] = []

    def instalar(*linhas: dict) -> list[tuple[str, dict]]:
        monkeypatch.setattr(catalog, "listar_perfis", lambda: list(linhas))
        monkeypatch.setattr(catalog, "_eu_id", lambda: EU)
        monkeypatch.setattr(
            catalog, "_atualizar_perfil",
            lambda uid, campos: escritas.append((uid, campos)) or True,
        )
        return escritas

    return instalar


SOZINHO = (_linha(EU, "Gestor", gestor=True),)
COM_OUTRO_GESTOR = (
    _linha(EU, "Gestor", gestor=True),
    _linha("g-2", "Segundo", gestor=True),
)


class TestNinguemSeRemove:
    def test_gestor_sozinho_nao_se_desativa(self, equipe):
        equipe(*SOZINHO)
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.recusar(EU)

    def test_gestor_nao_se_desativa_nem_havendo_outro(self, equipe):
        """O furo que causou o incidente: um segundo gestor destravava o botão."""
        equipe(*COM_OUTRO_GESTOR)
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.recusar(EU)

    def test_gestor_nao_se_rebaixa(self, equipe):
        equipe(*COM_OUTRO_GESTOR)
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.definir_papel(EU, "membro")

    def test_nem_para_admin_que_e_o_mesmo_poder(self, equipe):
        equipe(*COM_OUTRO_GESTOR)
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.definir_papel(EU, "admin")

    def test_nada_chega_ao_banco_quando_bloqueia(self, equipe):
        escritas = equipe(*SOZINHO)
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.recusar(EU)
        assert escritas == []


class TestNuncaSemGestor:
    def test_ultimo_gestor_nao_e_desativado_por_outro(self, equipe):
        """`_eu_id` é outro, mas o alvo é o único que gerencia."""
        equipe(_linha("g-9", "Único", gestor=True))
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.recusar("g-9")

    def test_ultimo_gestor_nao_e_rebaixado(self, equipe):
        equipe(_linha("g-9", "Único", gestor=True))
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.definir_papel("g-9", "membro")

    def test_admin_sozinho_tambem_conta_como_gestao(self, equipe):
        """Se admin dá o mesmo poder, admin também segura o workspace."""
        equipe(_linha("a-9", "Admin", admin=True))
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.recusar("a-9")

    def test_havendo_outro_a_desativacao_passa(self, equipe):
        escritas = equipe(
            _linha(EU, "Gestor", gestor=True), _linha("a-2", "Admin", admin=True)
        )
        assert catalog.recusar("a-2")
        assert escritas == [("a-2", {"ativo": False, "recusado": True})]

    def test_membro_comum_sai_sem_cerimonia(self, equipe):
        escritas = equipe(_linha(EU, "Gestor", gestor=True), _linha("m-1", "Membro"))
        assert catalog.recusar("m-1")
        assert escritas == [("m-1", {"ativo": False, "recusado": True})]


class TestPromocao:
    def test_promover_a_admin_grava_as_duas_colunas(self, equipe):
        escritas = equipe(_linha(EU, "Gestor", gestor=True), _linha("m-1", "Membro"))
        assert catalog.definir_papel("m-1", "admin")
        assert escritas == [("m-1", {"gestor": False, "admin": True})]

    def test_promover_a_gestor_limpa_o_admin(self, equipe):
        escritas = equipe(_linha(EU, "Gestor", gestor=True), _linha("a-1", "A", admin=True))
        assert catalog.definir_papel("a-1", "gestor")
        assert escritas == [("a-1", {"gestor": True, "admin": False})]

    def test_papel_inventado_e_recusado(self, equipe):
        equipe(*SOZINHO)
        with pytest.raises(catalog.AcaoBloqueada):
            catalog.definir_papel("m-1", "dono")


# ------------------------------------------------------------------ a tela


SCRIPT = """
import streamlit as st
from src.models import Perfil
from src.repo import catalog
from src.ui import team

catalog.listar_perfis = lambda: st.session_state["_perfis"]
catalog.listar_convites = lambda: []

team.render(Perfil.de_linha(st.session_state["_eu"]))
"""


def _tela(*linhas: dict, eu: dict | None = None) -> AppTest:
    at = AppTest.from_string(SCRIPT, default_timeout=30)
    at.session_state["_perfis"] = list(linhas)
    at.session_state["_eu"] = eu or linhas[0]
    return at.run()


def _botao(at: AppTest, chave: str):
    return next(b for b in at.button if b.key == chave)


class TestTelaDeEquipe:
    def test_desativar_de_si_mesmo_nasce_travado(self):
        at = _tela(*COM_OUTRO_GESTOR)
        assert not at.exception
        assert _botao(at, f"des_{EU}").disabled
        assert not _botao(at, "des_g-2").disabled

    def test_seletor_de_papel_de_si_mesmo_nasce_travado(self):
        at = _tela(*COM_OUTRO_GESTOR)
        seletor = next(s for s in at.selectbox if s.key == f"papel_{EU}")
        assert seletor.disabled

    def test_admin_entra_na_tela(self):
        """Antes, admin via o item na sidebar e batia em 'só para gestores'."""
        at = _tela(_linha("a-1", "Admin", admin=True))
        assert not at.exception
        assert [w.value for w in at.warning] == []

    def test_membro_nao_entra(self):
        at = _tela(_linha("m-1", "Membro"))
        assert len(at.warning) == 1
