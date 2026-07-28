"""Teste de fumaça do painel: `dashboard.render` roda de ponta a ponta.

O `test_prazos.py` prova que a conta está certa; aqui a pergunta é outra —
o painel consome o resultado sem quebrar e escreve na tela o que a conta
mandou. É o teste que teria pego o selo `alerta` caindo no cinza do `else`.

Roda pelo `AppTest` do Streamlit (headless, sem navegador). O banco é
substituído por dados fixos, então não precisa de Supabase nem credencial.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from streamlit.testing.v1 import AppTest

from src.prazos import CONCLUIDO_NO_PRAZO

USUARIO = "Ana Souza"
PERFIL_ID = "p-1"


def _iso(dias_atras: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias_atras)).isoformat()


def _data(dias_atras: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias_atras)).date().isoformat()


# Uma tarefa por situação de prazo, para o painel exercitar todos os selos.
TAREFAS = [
    {  # o caso relatado: entregue no prazo, editada bem depois
        "id": "t-1", "codigo": "DEV-101", "titulo": "Entregue no prazo e editada depois",
        "list_id": "l-1", "responsavel_id": PERFIL_ID, "status": "Concluído",
        "prioridade": "Normal", "data_limite": _data(10),
        "criado_em": _iso(30), "concluido_em": _iso(12), "atualizado_em": _iso(1),
    },
    {  # atraso verdadeiro, tem que continuar aparecendo
        "id": "t-2", "codigo": "DEV-102", "titulo": "Entregue com atraso real",
        "list_id": "l-1", "responsavel_id": PERFIL_ID, "status": "Concluído",
        "prioridade": "Alta", "data_limite": _data(20),
        "criado_em": _iso(30), "concluido_em": _iso(15), "atualizado_em": _iso(15),
    },
    {  # pendente e vencida -> entra nos KPIs e no painel de alertas
        "id": "t-3", "codigo": "DEV-103", "titulo": "Pendente e vencida",
        "list_id": "l-1", "responsavel_id": PERFIL_ID, "status": "Em Progresso",
        "prioridade": "Urgente", "data_limite": _data(5),
        "criado_em": _iso(25), "concluido_em": None, "atualizado_em": _iso(2),
    },
    {  # sem prazo definido
        "id": "t-4", "codigo": "DEV-104", "titulo": "Sem data limite",
        "list_id": "l-1", "responsavel_id": PERFIL_ID, "status": "A Fazer",
        "prioridade": "Baixa", "data_limite": None,
        "criado_em": _iso(3), "concluido_em": None, "atualizado_em": _iso(3),
    },
    {  # linha corrompida: o painel tem que sobreviver a ela
        "id": "t-5", "codigo": "DEV-105", "titulo": "Datas ilegíveis",
        "list_id": "l-1", "responsavel_id": PERFIL_ID, "status": "A Fazer",
        "prioridade": "Normal", "data_limite": "amanhã de manhã",
        "criado_em": "???", "concluido_em": None, "atualizado_em": None,
    },
]

PERFIS = [{"id": PERFIL_ID, "nome": USUARIO, "ativo": True, "gestor": False,
           "email": "ana@exemplo.com", "cargo": None, "recusado": False}]
ESPACOS = [{"id": "e-1", "nome": "Desenvolvimento", "cor": "#7b68ee", "prefixo": "DEV"}]
LISTAS = [{"id": "l-1", "space_id": "e-1", "nome": "Sprint atual"}]


# O script que o AppTest executa: troca o banco por dados fixos e chama o painel.
SCRIPT = """
import streamlit as st
from src.models import Perfil
from src.repo import catalog, tasks
from src.ui import dashboard

tasks.listar = lambda **kw: st.session_state["_tarefas"]
catalog.listar_perfis = lambda: st.session_state["_perfis"]
catalog.espacos = lambda: st.session_state["_espacos"]
catalog.listas = lambda: st.session_state["_listas"]

dashboard.render(Perfil(
    id="p-1", email="ana@exemplo.com", nome="Ana Souza",
    cargo=None, gestor=True, ativo=True,
))
"""


@pytest.fixture
def painel() -> AppTest:
    at = AppTest.from_string(SCRIPT, default_timeout=30)
    at.session_state["_tarefas"] = TAREFAS
    at.session_state["_perfis"] = PERFIS
    at.session_state["_espacos"] = ESPACOS
    at.session_state["_listas"] = LISTAS
    return at.run()


def _todo_o_html(at: AppTest) -> str:
    return "\n".join(bloco.value for bloco in at.markdown)


class TestRenderizacao:
    def test_painel_renderiza_sem_excecao(self, painel):
        assert not painel.exception

    def test_nenhum_aviso_de_falha_de_calculo(self, painel):
        """Nem a linha com datas ilegíveis deve virar erro de cálculo."""
        assert [w.value for w in painel.warning] == []

    def test_tabela_do_usuario_aparece(self, painel):
        html = _todo_o_html(painel)
        assert "Lista de Projetos / Tarefas sob responsabilidade" in html
        assert "Situação do Prazo" in html
        assert "Entrega Real" in html


class TestConteudoDaTabela:
    def test_entrega_no_prazo_nao_e_anunciada_como_atraso(self, painel):
        """A regressão relatada, agora observada na tela renderizada."""
        html = _todo_o_html(painel)
        assert "DEV-101" in html
        assert CONCLUIDO_NO_PRAZO in html

    def test_atraso_real_continua_sendo_apontado(self, painel):
        assert "de atraso" in _todo_o_html(painel)

    def test_selo_de_entrega_atrasada_nao_cai_no_cinza(self, painel):
        """`alerta` tem cor própria; antes ficava igual a 'Sem data limite'."""
        from src.ui.dashboard import ESTILO_BADGE_PRAZO

        assert ESTILO_BADGE_PRAZO["alerta"] in _todo_o_html(painel)
        assert ESTILO_BADGE_PRAZO["alerta"] != ESTILO_BADGE_PRAZO["normal"]

    def test_toda_classe_de_selo_tem_estilo_proprio(self):
        from src.ui.dashboard import ESTILO_BADGE_PRAZO

        assert len(set(ESTILO_BADGE_PRAZO.values())) == len(ESTILO_BADGE_PRAZO)


class TestIndicadores:
    def test_kpi_de_atrasadas_conta_so_a_pendente_vencida(self, painel):
        """As duas concluídas não entram, mesmo a que foi entregue tarde."""
        html = _todo_o_html(painel)
        assert "⚠️ 1 atenção" in html

    def test_tarefa_com_dados_ruins_nao_some_do_total(self, painel):
        """Linha inconsistente continua contando — sumir calado é pior."""
        html = _todo_o_html(painel)
        assert f'<div class="kpi-value">{len(TAREFAS)}</div>' in html
