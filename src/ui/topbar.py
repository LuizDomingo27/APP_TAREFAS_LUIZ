"""Barra superior — migalhas de pão, busca e filtros."""

from __future__ import annotations

import streamlit as st

from src.models import Prioridade
from src.ui.componentes import esc


def migalhas(espaco: dict | None, lista: dict | None) -> None:
    if espaco is None:
        trilha = '<span class="atual">Todas as tarefas</span>'
    else:
        atual = lista["nome"] if lista else espaco["nome"]
        trilha = (
            f'<span>{esc(espaco["nome"])}</span>'
            f'<span class="sep">/</span>'
            f'<span class="atual">'
            f'<span class="ponto" style="background:{esc(espaco.get("cor") or "#7b68ee")}"></span>'
            f"{esc(atual)}</span>"
        )

    st.markdown(
        f'<div class="topbar"><div class="migalhas">{trilha}</div></div>',
        unsafe_allow_html=True,
    )


def filtros(perfis: list[dict]) -> tuple[str, str, str | None]:
    """Devolve (busca, prioridade, responsavel_id)."""
    # A busca fica com a sobra: os dois seletores têm largura fixa de 140px
    # (CSS), então uma coluna maior que isso só viraria vão vazio.
    col_busca, col_prio, col_resp = st.columns([6, 1.5, 1.5], gap="small")

    busca = col_busca.text_input(
        "Buscar", placeholder="Buscar tarefas...", label_visibility="collapsed",
        key="filtro_busca",
    )

    prioridade = col_prio.selectbox(
        "Prioridade",
        ["Todas", *[p.value for p in Prioridade]],
        label_visibility="collapsed",
        key="filtro_prioridade",
    )

    nomes = {"Todos": None} | {p["nome"]: p["id"] for p in perfis if p.get("ativo")}
    escolhido = col_resp.selectbox(
        "Responsável", list(nomes), label_visibility="collapsed", key="filtro_resp",
    )

    return busca, prioridade, nomes[escolhido]
