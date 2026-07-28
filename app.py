"""Gerenciador de Tarefas da Equipe — entrada do app."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Tarefas da Equipe",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src import session  # noqa: E402
from src.auth import exigir_login, logout  # noqa: E402
from src.db import ErroDeConexao, SessaoExpirada  # noqa: E402
from src.models import Perfil  # noqa: E402
from src.repo import catalog, tasks  # noqa: E402
from src.ui import (  # noqa: E402
    board,
    dashboard,
    espacos,
    list_view,
    sidebar,
    styles,
    task_detail,
    team,
    topbar,
)


def _tela_tarefas() -> None:
    espaco, lista = sidebar.contexto()
    perfis = catalog.listar_perfis()
    nomes = {p["id"]: p["nome"] for p in perfis}

    topbar.migalhas(espaco, lista)
    busca, prioridade, responsavel_id = topbar.filtros(perfis)

    itens = tasks.listar(
        list_ids=sidebar.listas_do_escopo(),
        busca=busca,
        prioridade=prioridade,
        responsavel_id=responsavel_id,
    )

    aba_quadro, aba_lista = st.tabs(["Quadro", "Lista"])
    with aba_quadro:
        board.render(itens, nomes)
    with aba_lista:
        list_view.render(itens, nomes)


def _tela_sem_conexao(detalhe: str) -> None:
    """Substitui a página inteira quando o banco não responde.

    Nada de meia tela: se a leitura falhou, o que estivesse desenhado até ali
    seria um quadro pela metade, que engana mais do que informa.
    """
    st.markdown("## Sem conexão com o servidor")
    st.warning(
        "Não consegui falar com o banco de dados. Costuma ser internet "
        "oscilando — o projeto no Supabase também pausa sozinho depois de "
        "alguns dias sem uso no plano gratuito."
    )
    if st.button("Tentar de novo", type="primary"):
        st.cache_data.clear()
        st.rerun()
    with st.expander("Detalhe técnico"):
        st.code(detalhe or "sem detalhe", language=None)


def _tela_sessao_expirada() -> None:
    st.markdown("## Sessão expirada")
    st.info("Seu acesso venceu por inatividade. Entre de novo para continuar.")
    if st.button("Entrar de novo", type="primary"):
        logout()  # limpa cookie e session_state, e já faz o rerun


def main() -> None:
    styles.aplicar()
    # Antes do exigir_login, que pode chamar st.stop(): é o que garante que
    # a remoção do cookie no logout chegue a ser executada no navegador.
    session.sincronizar()
    eu: Perfil = exigir_login()          # barra aqui se não logado / não liberado
    view = sidebar.render(eu)

    if view == "Equipe":
        team.render(eu)
    elif "Dashboard" in view:
        dashboard.render(eu)
    else:
        _tela_tarefas()

    # Depois das telas: o modal precisa ser o último a desenhar para aparecer
    # sobre o conteúdo já renderizado deste run. Só um `st.dialog` por run, então
    # se o de espaço/lista abriu, o de tarefa fica de fora.
    if not espacos.render_modais(eu):
        task_detail.render_modais(eu)

    # De novo no fim: o que foi agendado durante ESTE run (o preenchimento
    # do cookie de quem já estava logado) seria escrito só num rerun futuro,
    # que pode nunca acontecer se a pessoa não clicar em nada.
    session.sincronizar()


if __name__ == "__main__":
    # A guarda envolve o main inteiro: a queda de rede pode acontecer no
    # primeiro `listar_perfis()` ou no último comentário do modal, e a resposta
    # é a mesma em qualquer ponto.
    try:
        main()
    except ErroDeConexao as exc:
        _tela_sem_conexao(str(exc))
    except SessaoExpirada:
        _tela_sessao_expirada()
