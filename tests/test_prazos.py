"""Testes das regras de prazo (`src/prazos.py`).

Cobre principalmente os dois defeitos que motivaram o módulo:

- entrega no prazo virava "Concluído com N dia(s) de atraso" depois de uma
  edição qualquer, porque a data de conclusão saía de `atualizado_em`;
- entrega no fim da tarde ganhava um dia de atraso fantasma, porque o
  timestamp UTC do banco era cortado no "T" sem converter o fuso.

Ambos são testes de regressão: se alguém voltar a ler `atualizado_em` como
data de entrega, ou a fatiar a string do timestamp, eles quebram.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from src.models import Status
from src.prazos import (
    CONCLUIDO_NO_PRAZO,
    CONCLUIDO_SEM_PRAZO,
    JANELA_ALERTA,
    SEM_PRAZO,
    VENCE_HOJE,
    calcular_dias_em_andamento,
    calcular_prazo,
    data_conclusao,
    esta_critica,
    hoje,
    para_data,
)

HOJE = date(2026, 7, 28)


def tarefa(**campos) -> dict:
    """Linha de `tasks` com os campos que o cálculo lê."""
    base = {
        "id": "t-1",
        "status": Status.A_FAZER.value,
        "criado_em": "2026-07-01T09:00:00+00:00",
        "atualizado_em": "2026-07-01T09:00:00+00:00",
        "concluido_em": None,
        "data_limite": None,
    }
    base.update(campos)
    return base


def concluida(**campos) -> dict:
    return tarefa(status=Status.CONCLUIDO.value, **campos)


# ============================================================ para_data


class TestParaData:
    def test_data_pura_nao_sofre_conversao_de_fuso(self):
        """`data_limite` é dia de calendário: converter fuso mudaria o prazo."""
        assert para_data("2026-07-20") == date(2026, 7, 20)
        assert para_data(date(2026, 7, 20)) == date(2026, 7, 20)

    def test_timestamp_utc_vira_dia_local(self):
        """23:30 UTC ainda é dia 20 em Brasília (UTC-3), não dia 21."""
        assert para_data("2026-07-21T01:30:00+00:00") == date(2026, 7, 20)
        assert para_data("2026-07-20T23:30:00+00:00") == date(2026, 7, 20)

    def test_meia_noite_utc_ainda_e_o_dia_anterior_aqui(self):
        assert para_data("2026-07-21T00:10:00+00:00") == date(2026, 7, 20)

    def test_manha_utc_e_o_mesmo_dia(self):
        assert para_data("2026-07-20T12:00:00+00:00") == date(2026, 7, 20)

    def test_aceita_sufixo_z_e_microssegundos(self):
        assert para_data("2026-07-20T12:00:00.123456Z") == date(2026, 7, 20)

    def test_aceita_datetime_com_e_sem_fuso(self):
        aware = datetime(2026, 7, 21, 1, 0, tzinfo=timezone.utc)
        assert para_data(aware) == date(2026, 7, 20)
        # Naive é tratado como UTC, que é o que o banco grava.
        assert para_data(datetime(2026, 7, 21, 1, 0)) == date(2026, 7, 20)

    @pytest.mark.parametrize("entrada", [None, "", "   ", "não é data", 42, [], "2026-13-45"])
    def test_lixo_devolve_none_em_vez_de_levantar(self, entrada):
        """Uma linha estranha não pode derrubar o painel inteiro."""
        assert para_data(entrada) is None


# ==================================================== data de conclusão


class TestDataConclusao:
    def test_usa_concluido_em(self):
        t = concluida(concluido_em="2026-07-18T14:00:00+00:00")
        assert data_conclusao(t) == date(2026, 7, 18)

    def test_edicao_posterior_nao_move_a_entrega(self):
        """O bug original: `atualizado_em` andou, `concluido_em` não."""
        t = concluida(
            concluido_em="2026-07-18T14:00:00+00:00",
            atualizado_em="2026-07-27T10:00:00+00:00",  # alguém trocou uma tag
        )
        assert data_conclusao(t) == date(2026, 7, 18)

    def test_cai_para_atualizado_em_sem_a_coluna_nova(self):
        """Banco que ainda não rodou a migração continua funcionando."""
        t = concluida(concluido_em=None, atualizado_em="2026-07-18T14:00:00+00:00")
        assert data_conclusao(t) == date(2026, 7, 18)

    def test_tarefa_aberta_nao_tem_data_de_entrega(self):
        assert data_conclusao(tarefa(atualizado_em="2026-07-18T14:00:00+00:00")) is None


# ======================================================= tarefa concluída


class TestPrazoDeConcluida:
    def test_entregue_no_prazo(self):
        r = calcular_prazo(
            concluida(data_limite="2026-07-20", concluido_em="2026-07-18T12:00:00+00:00"),
            HOJE,
        )
        assert r["status_prazo"] == CONCLUIDO_NO_PRAZO
        assert r["dias_atraso"] == 0
        assert r["dias_adiantamento"] == 2
        assert r["entregue_com_atraso"] is False
        assert r["atrasado"] is False

    def test_entregue_no_ultimo_dia_conta_como_no_prazo(self):
        r = calcular_prazo(
            concluida(data_limite="2026-07-20", concluido_em="2026-07-20T23:00:00+00:00"),
            HOJE,
        )
        assert r["status_prazo"] == CONCLUIDO_NO_PRAZO
        assert r["dias_atraso"] == 0

    def test_entregue_com_atraso(self):
        r = calcular_prazo(
            concluida(data_limite="2026-07-20", concluido_em="2026-07-23T12:00:00+00:00"),
            HOJE,
        )
        assert r["status_prazo"] == "Concluído com 3 dia(s) de atraso"
        assert r["dias_atraso"] == 3
        assert r["entregue_com_atraso"] is True
        assert r["badge_class"] == "alerta"

    def test_atraso_nao_cresce_com_o_passar_do_tempo(self):
        """Atraso de entrega é fato histórico: não depende de 'hoje'."""
        t = concluida(data_limite="2026-07-20", concluido_em="2026-07-23T12:00:00+00:00")
        for ref in (date(2026, 7, 23), date(2026, 9, 1), date(2027, 1, 1)):
            assert calcular_prazo(t, ref)["dias_atraso"] == 3

    def test_regressao_edicao_tardia_nao_inventa_atraso(self):
        """O caso relatado: entregue no prazo, editada depois, 'com atraso'."""
        t = concluida(
            data_limite="2026-07-20",
            concluido_em="2026-07-19T12:00:00+00:00",
            atualizado_em="2026-07-23T12:00:00+00:00",
        )
        r = calcular_prazo(t, HOJE)
        assert r["status_prazo"] == CONCLUIDO_NO_PRAZO
        assert r["entregue_com_atraso"] is False

    def test_regressao_entrega_noturna_nao_ganha_dia_extra(self):
        """21h em Brasília = 00h UTC do dia seguinte. Não é atraso."""
        t = concluida(data_limite="2026-07-20", concluido_em="2026-07-21T00:30:00+00:00")
        r = calcular_prazo(t, HOJE)
        assert r["status_prazo"] == CONCLUIDO_NO_PRAZO
        assert r["dias_atraso"] == 0

    def test_concluida_sem_prazo(self):
        r = calcular_prazo(concluida(concluido_em="2026-07-18T12:00:00+00:00"), HOJE)
        assert r["status_prazo"] == CONCLUIDO_SEM_PRAZO
        assert r["dias_atraso"] is None
        assert r["atrasado"] is False

    def test_concluida_nunca_conta_como_atrasada_agora(self):
        """`atrasado` = pendente e vencida. Entrega antiga não entra no KPI."""
        t = concluida(data_limite="2026-01-01", concluido_em="2026-06-01T12:00:00+00:00")
        assert calcular_prazo(t, HOJE)["atrasado"] is False

    def test_dias_restantes_e_none_em_concluida(self):
        """Não existe 'faltam N dias' para o que já foi entregue."""
        t = concluida(data_limite="2026-08-30", concluido_em="2026-07-18T12:00:00+00:00")
        assert calcular_prazo(t, HOJE)["dias_restantes"] is None


# ======================================================== tarefa pendente


class TestPrazoDePendente:
    def test_vencida(self):
        r = calcular_prazo(tarefa(data_limite="2026-07-25"), HOJE)
        assert r["status_prazo"] == "Atrasado há 3 dia(s)"
        assert r["dias_atraso"] == 3
        assert r["dias_restantes"] == -3
        assert r["atrasado"] is True
        assert r["badge_class"] == "urgente"

    def test_vence_hoje(self):
        r = calcular_prazo(tarefa(data_limite="2026-07-28"), HOJE)
        assert r["status_prazo"] == VENCE_HOJE
        assert r["dias_restantes"] == 0
        assert r["atrasado"] is False

    def test_vence_dentro_da_janela_de_alerta(self):
        r = calcular_prazo(tarefa(data_limite="2026-07-31"), HOJE)
        assert r["status_prazo"] == f"Vence em {JANELA_ALERTA} dia(s)"
        assert r["badge_class"] == "alta"

    def test_prazo_folgado(self):
        r = calcular_prazo(tarefa(data_limite="2026-08-15"), HOJE)
        assert r["status_prazo"] == "Faltam 18 dia(s)"
        assert r["badge_class"] == "normal"
        assert r["atrasado"] is False

    def test_sem_prazo(self):
        r = calcular_prazo(tarefa(), HOJE)
        assert r["status_prazo"] == SEM_PRAZO
        assert r["dias_restantes"] is None
        assert r["atrasado"] is False

    def test_data_limite_ilegivel_nao_quebra(self):
        r = calcular_prazo(tarefa(data_limite="ontem"), HOJE)
        assert r["status_prazo"] == SEM_PRAZO

    def test_status_ausente_e_tratado_como_pendente(self):
        r = calcular_prazo({"data_limite": "2026-07-25"}, HOJE)
        assert r["atrasado"] is True

    def test_dicionario_vazio_nao_quebra(self):
        assert calcular_prazo({}, HOJE)["status_prazo"] == SEM_PRAZO


# =================================================== dias em andamento


class TestDiasEmAndamento:
    def test_pendente_conta_ate_hoje(self):
        t = tarefa(criado_em="2026-07-20T10:00:00+00:00")
        assert calcular_dias_em_andamento(t, HOJE) == 8

    def test_concluida_para_de_contar_na_entrega(self):
        t = concluida(
            criado_em="2026-07-01T10:00:00+00:00",
            concluido_em="2026-07-11T10:00:00+00:00",
        )
        assert calcular_dias_em_andamento(t, HOJE) == 10

    def test_edicao_posterior_nao_infla_o_tempo_de_ciclo(self):
        t = concluida(
            criado_em="2026-07-01T10:00:00+00:00",
            concluido_em="2026-07-11T10:00:00+00:00",
            atualizado_em="2026-07-27T10:00:00+00:00",
        )
        assert calcular_dias_em_andamento(t, HOJE) == 10

    def test_sem_data_de_criacao_devolve_zero(self):
        assert calcular_dias_em_andamento(tarefa(criado_em=None), HOJE) == 0

    def test_nunca_devolve_negativo(self):
        t = concluida(
            criado_em="2026-07-20T10:00:00+00:00",
            concluido_em="2026-07-10T10:00:00+00:00",  # dado inconsistente
        )
        assert calcular_dias_em_andamento(t, HOJE) == 0


# ============================================================== críticas


class TestEstaCritica:
    def _com_prazo(self, task: dict) -> dict:
        return {**task, **calcular_prazo(task, HOJE)}

    def test_pendente_vencida_e_critica(self):
        assert esta_critica(self._com_prazo(tarefa(data_limite="2026-07-01"))) is True

    def test_pendente_vencendo_e_critica(self):
        assert esta_critica(self._com_prazo(tarefa(data_limite="2026-07-30"))) is True

    def test_pendente_folgada_nao_e_critica(self):
        assert esta_critica(self._com_prazo(tarefa(data_limite="2026-09-01"))) is False

    def test_concluida_com_atraso_nao_polui_o_painel_de_alertas(self):
        t = concluida(data_limite="2026-01-01", concluido_em="2026-06-01T12:00:00+00:00")
        assert esta_critica(self._com_prazo(t)) is False


# ================================================================= hoje


def test_hoje_fica_perto_do_relogio_do_sistema():
    """Sanidade do fuso: no máximo um dia de diferença do UTC do servidor."""
    assert abs((hoje() - datetime.now(timezone.utc).date()).days) <= 1


def test_hoje_e_consistente_com_para_data():
    agora = datetime.now(timezone.utc)
    assert para_data(agora) == hoje()
    assert para_data(agora.isoformat()) == hoje()


def test_ciclo_completo_de_uma_tarefa_entregue_no_prazo():
    """Criada, entregue no prazo e editada depois — do jeito que acontece."""
    t = concluida(
        criado_em="2026-07-01T09:00:00+00:00",
        data_limite="2026-07-15",
        concluido_em="2026-07-14T18:00:00+00:00",
        atualizado_em=(datetime.now(timezone.utc) + timedelta(days=0)).isoformat(),
    )
    prazo = calcular_prazo(t, HOJE)
    assert prazo["status_prazo"] == CONCLUIDO_NO_PRAZO
    assert prazo["entregue_com_atraso"] is False
    assert calcular_dias_em_andamento(t, HOJE) == 13
