"""Modais de criação de espaço e lista — gestão da árvore do workspace.

Segue o mesmo padrão do `task_detail`: o modal não guarda estado próprio; quem
manda é uma chave em `session_state`, e `render_modais` abre o que estiver
pedido. Só gestor chega aqui — os botões que disparam ficam atrás de
`eu.gestor`, e o RLS de `02_rls.sql` é a segunda tranca.
"""

from __future__ import annotations

import streamlit as st
from postgrest.exceptions import APIError

from src.models import Perfil
from src.repo import catalog, tasks

# Ícones que a sidebar sabe desenhar (nome guardado no banco -> rótulo humano).
# Espelha o dicionário ICONES da sidebar; 'figma' cai em 'palette' lá na hora
# de desenhar, mas no banco guardamos a chave 'figma'.
ICONES_LISTA = {
    "list": "Lista",
    "bug": "Bug",
    "layers": "Camadas",
    "figma": "Design",
}


# ------------------------------------------------------------------ estado


def abrir_criar_espaco() -> None:
    st.session_state["criando_espaco"] = True


def abrir_criar_lista() -> None:
    st.session_state["criando_lista"] = True


def abrir_excluir_espaco(space_id: str) -> None:
    st.session_state["excluindo_espaco"] = space_id


def _fechar() -> None:
    st.session_state.pop("criando_espaco", None)
    st.session_state.pop("criando_lista", None)
    st.session_state.pop("excluindo_espaco", None)
    # Sem isto, o nome digitado numa exclusão sobra pré-preenchido na próxima.
    st.session_state.pop("confirma_nome_espaco", None)


# ------------------------------------------------------------------ espaço


@st.dialog("Novo espaço", width="small", on_dismiss=_fechar)
def _dialog_criar_espaco() -> None:
    with st.form("form_criar_espaco", border=False):
        nome = st.text_input("Nome do espaço", placeholder="Ex: Desenvolvimento")

        col_pref, col_cor = st.columns([2, 1])
        prefixo = col_pref.text_input(
            "Prefixo",
            placeholder="DEV",
            max_chars=6,
            help="Vira o código das tarefas (ex.: DEV-101). Só letras, único.",
        )
        cor = col_cor.color_picker("Cor", value="#7b68ee")

        _, col_cancelar, col_ok = st.columns([2, 1, 1])
        cancelar = col_cancelar.form_submit_button("Cancelar", use_container_width=True)
        criar = col_ok.form_submit_button(
            "Criar", type="primary", use_container_width=True
        )

    if cancelar:
        _fechar()
        st.rerun()

    if criar:
        nome_limpo = nome.strip()
        pref_limpo = prefixo.strip().upper()
        if not nome_limpo:
            st.warning("Dê um nome ao espaço.")
            return
        if not pref_limpo:
            st.warning("Escolha um prefixo (ex.: DEV).")
            return
        if not pref_limpo.isalpha():
            st.warning("O prefixo deve ter só letras.")
            return
        existentes = {(e.get("prefixo") or "").upper() for e in catalog.espacos()}
        if pref_limpo in existentes:
            st.warning(f"Já existe um espaço com o prefixo {pref_limpo}.")
            return

        try:
            ok = catalog.criar_espaco(nome_limpo, pref_limpo, cor)
        except APIError:
            # Corrida entre dois gestores: o unique do banco chegou primeiro.
            st.error("O banco recusou — o prefixo pode já estar em uso.")
            return
        if not ok:
            st.error("O banco recusou a criação. Só gestor pode criar espaços.")
            return

        _fechar()
        st.toast("Espaço criado.", icon="✅")
        st.rerun()


# ------------------------------------------------------------------- lista


@st.dialog("Nova lista", width="small", on_dismiss=_fechar)
def _dialog_criar_lista() -> None:
    espacos = catalog.espacos()
    if not espacos:
        st.warning("Crie um espaço antes de criar uma lista.")
        if st.button("Fechar"):
            _fechar()
            st.rerun()
        return

    rotulos = {e["nome"]: e["id"] for e in espacos}
    icones = list(ICONES_LISTA.values())

    with st.form("form_criar_lista", border=False):
        nome = st.text_input("Nome da lista", placeholder="Ex: Sprint atual")
        onde = st.selectbox("Espaço", list(rotulos), key="lista_espaco")
        icone_rotulo = st.selectbox("Ícone", icones, key="lista_icone")

        _, col_cancelar, col_ok = st.columns([2, 1, 1])
        cancelar = col_cancelar.form_submit_button("Cancelar", use_container_width=True)
        criar = col_ok.form_submit_button(
            "Criar", type="primary", use_container_width=True
        )

    if cancelar:
        _fechar()
        st.rerun()

    if criar:
        if not nome.strip():
            st.warning("Dê um nome à lista.")
            return
        icone = next(k for k, v in ICONES_LISTA.items() if v == icone_rotulo)
        if not catalog.criar_lista(rotulos[onde], nome, icone):
            st.error("O banco recusou a criação. Só gestor pode criar listas.")
            return

        _fechar()
        st.toast("Lista criada.", icon="✅")
        st.rerun()


# ---------------------------------------------------------------- exclusão


@st.dialog("Excluir espaço", width="small", on_dismiss=_fechar)
def _dialog_excluir_espaco() -> None:
    space_id = st.session_state.get("excluindo_espaco")
    espaco = next((e for e in catalog.espacos() if e["id"] == space_id), None)
    if espaco is None:
        # Sumiu entre o clique e o rerun — outro gestor apagou primeiro.
        _fechar()
        st.rerun()
        return

    nome = espaco["nome"]
    listas_dentro = [l for l in catalog.listas() if l["space_id"] == space_id]
    n_tarefas = tasks.contagem_por_espaco(catalog.listas()).get(space_id, 0)

    # Mostrar o raio de destruição antes de tudo: excluir espaço é a única
    # ação do app que apaga em massa. O gestor tem de ver o tamanho do estrago
    # — quantas listas e tarefas somem junto — antes de conseguir confirmar.
    st.warning(
        f"Excluir **{nome}** também apaga, sem volta, **{len(listas_dentro)} "
        f"lista(s)** e **{n_tarefas} tarefa(s)**, com todas as subtarefas e "
        "comentários dessas tarefas."
    )
    st.caption(f"Para confirmar, digite o nome do espaço: **{nome}**")

    # A trava é digitar o nome exato: um clique por reflexo não basta para uma
    # exclusão desse tamanho. Enquanto não bater, o botão fica desabilitado.
    digitado = st.text_input(
        "Nome do espaço",
        placeholder=nome,
        label_visibility="collapsed",
        key="confirma_nome_espaco",
    )
    confere = digitado.strip() == nome

    col_cancelar, col_ok = st.columns(2)
    if col_cancelar.button("Cancelar", use_container_width=True):
        _fechar()
        st.rerun()

    if col_ok.button(
        "Excluir definitivamente",
        type="primary",
        use_container_width=True,
        disabled=not confere,
    ):
        if not catalog.excluir_espaco(space_id):
            st.error("O banco recusou a exclusão. Só gestor pode excluir espaços.")
            return

        # Se o quadro estava filtrado por este espaço (ou por uma lista dele),
        # o filtro apontaria para algo que não existe mais: volta para "tudo".
        afetados = {space_id} | {l["id"] for l in listas_dentro}
        if st.session_state.get("escopo_id") in afetados:
            st.session_state.pop("escopo_tipo", None)
            st.session_state.pop("escopo_id", None)

        _fechar()
        st.toast("Espaço excluído.", icon="🗑️")
        st.rerun()


# ------------------------------------------------------------- despachante


def render_modais(eu: Perfil) -> bool:
    """Abre o modal de espaço/lista se houver pedido. Devolve True se abriu.

    Só um `st.dialog` pode existir por run; o `app.py` usa o retorno para não
    tentar abrir o modal de tarefa por cima. Como criar é privilégio de gestor,
    uma chave em pé num não-gestor (rerun teimoso) é apagada sem abrir nada.
    """
    if not eu.gestor:
        _fechar()
        return False

    if st.session_state.get("criando_espaco"):
        _dialog_criar_espaco()
        return True
    if st.session_state.get("criando_lista"):
        _dialog_criar_lista()
        return True
    if st.session_state.get("excluindo_espaco"):
        _dialog_excluir_espaco()
        return True
    return False
