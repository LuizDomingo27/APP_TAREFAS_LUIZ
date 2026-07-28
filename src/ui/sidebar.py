"""Sidebar — cabeçalho do workspace, navegação, árvore de espaços e perfil."""

from __future__ import annotations

import streamlit as st

from src.auth import logout
from src.models import ROTULO_PAPEL, Perfil
from src.repo import catalog, tasks
from src.ui import espacos as espacos_ui
from src.ui import task_detail
from src.ui.componentes import avatar, esc, icone, limpar

# 'icone' das listas vem do banco com o nome do ícone do Lucide; 'figma'
# não está no conjunto embutido, então cai em 'palette'.
ICONES = {"list": "list", "bug": "bug", "layers": "layers", "figma": "palette"}


# ---------------------------------------------------------------- escopo

# ("tudo", None) | ("espaco", id) | ("lista", id). Guardado em sessão porque
# a árvore é redesenhada a cada run e o Streamlit não tem estado de navegação.


def escopo() -> tuple[str, str | None]:
    return (
        st.session_state.get("escopo_tipo", "tudo"),
        st.session_state.get("escopo_id"),
    )


def definir_escopo(tipo: str, ident: str | None) -> None:
    st.session_state["escopo_tipo"] = tipo
    st.session_state["escopo_id"] = ident


def listas_do_escopo() -> set[str] | None:
    """Os `list_id` que o escopo atual abrange. `None` = sem filtro."""
    tipo, ident = escopo()
    if tipo == "lista":
        return {ident} if ident else None
    if tipo == "espaco":
        return {l["id"] for l in catalog.listas() if l["space_id"] == ident}
    return None


def contexto() -> tuple[dict | None, dict | None]:
    """(espaço, lista) do escopo atual — o que a barra de migalhas mostra."""
    tipo, ident = escopo()
    if tipo == "espaco":
        return next((e for e in catalog.espacos() if e["id"] == ident), None), None
    if tipo == "lista":
        lista = next((l for l in catalog.listas() if l["id"] == ident), None)
        if lista is None:
            return None, None
        esp = next(
            (e for e in catalog.espacos() if e["id"] == lista["space_id"]), None
        )
        return esp, lista
    return None, None


def _marcar_ativo(chave: str) -> None:
    """Pinta a linha selecionada.

    O Streamlit não tem "botão ativo", e o id do que está aberto só se sabe
    em tempo de execução — daí a regra sair daqui em vez do CSS estático.
    Emitida uma vez só, depois da árvore, para não picotar o layout.
    """
    st.markdown(
        f"<style>.st-key-{chave} button {{"
        "background: var(--roxo-suave) !important;"
        "color: var(--roxo) !important;"
        "}"
        f".st-key-{chave} button p {{ color: var(--roxo) !important; }}</style>",
        unsafe_allow_html=True,
    )


def _cabecalho() -> None:
    st.markdown(
        limpar("""
        <div class="ws-header">
          <div class="ws-logo">T</div>
          <div>
            <div class="ws-nome">Tarefas da Equipe</div>
            <div class="ws-plano">Workspace</div>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def _acoes_gestor(tem_espacos: bool, espaco_sel: dict | None) -> None:
    """Botões de criar espaço/lista, no rodapé da árvore, só para gestor.

    "Nova lista" fica desabilitado enquanto não houver espaço — lista sem
    espaço não tem onde morar.

    A exclusão é contextual: só aparece quando há um espaço selecionado, e
    apaga justamente esse. Fica fora da linha da árvore de propósito — mexer
    no layout dela (o ponto colorido é posicionado por CSS sobre o botão)
    arriscaria quebrar o visual; aqui embaixo o gatilho é seguro e claro.
    """
    if st.button(":material/add:  Novo espaço", key="btn_novo_espaco", use_container_width=True):
        espacos_ui.abrir_criar_espaco()
        st.rerun()
    if st.button(
        ":material/add:  Nova lista", key="btn_nova_lista",
        use_container_width=True, disabled=not tem_espacos,
    ):
        espacos_ui.abrir_criar_lista()
        st.rerun()
    if espaco_sel is not None:
        if st.button(
            f":material/delete:  Excluir “{espaco_sel['nome']}”",
            key="btn_excluir_espaco", use_container_width=True,
            help="Apaga o espaço e tudo dentro dele",
        ):
            espacos_ui.abrir_excluir_espaco(espaco_sel["id"])
            st.rerun()


def _arvore(eu: Perfil) -> None:
    """Espaços e listas como botões — clicar troca o escopo do quadro.

    Cada linha é um `st.button` com o visual da árvore do protótipo, e não um
    bloco de HTML: sem widget de verdade não há clique, e a navegação por
    espaço era o que faltava para a sidebar deixar de ser enfeite.
    """
    espacos = catalog.espacos()
    listas = catalog.listas()
    contagens = tasks.contagem_por_espaco(listas)
    tipo, ident = escopo()
    chave_ativa = "esc_tudo"

    with st.container(key="nav_arvore"):
        st.markdown(
            '<div class="side-titulo">Espaços de trabalho</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            f"Todas as tarefas  :gray[{len(tasks.listar())}]",
            key="esc_tudo", use_container_width=True,
        ):
            definir_escopo("tudo", None)
            st.rerun()

        if not espacos:
            st.markdown(
                '<div class="lista-linha">Nenhum espaço cadastrado</div>',
                unsafe_allow_html=True,
            )

        for esp in espacos:
            # O ponto colorido do espaço não cabe num rótulo de botão (que só
            # aceita markdown), então vem como um <span> posicionado por CSS
            # sobre a linha, ancorado no contêiner com `key`.
            with st.container(key=f"esp_wrap_{esp['id']}"):
                st.markdown(
                    f'<span class="ponto-espaco" style="background:'
                    f'{esc(esp.get("cor") or "#7b68ee")}"></span>',
                    unsafe_allow_html=True,
                )
                chave = f"esp_{esp['id']}"
                if st.button(
                    f"{esp['nome']}  :gray[{contagens.get(esp['id'], 0)}]",
                    key=chave, use_container_width=True,
                ):
                    definir_escopo("espaco", esp["id"])
                    st.rerun()
                if tipo == "espaco" and ident == esp["id"]:
                    chave_ativa = chave

            for l in [x for x in listas if x["space_id"] == esp["id"]]:
                chave = f"lst_{l['id']}"
                with st.container(key=f"lst_wrap_{l['id']}"):
                    st.markdown(
                        f'<span class="icone-lista">'
                        f'{icone(ICONES.get(l.get("icone") or "list", "list"), 14)}'
                        "</span>",
                        unsafe_allow_html=True,
                    )
                    if st.button(l["nome"], key=chave, use_container_width=True):
                        definir_escopo("lista", l["id"])
                        st.rerun()
                if tipo == "lista" and ident == l["id"]:
                    chave_ativa = chave

        if eu.pode_gerenciar:
            espaco_sel = (
                next((e for e in espacos if e["id"] == ident), None)
                if tipo == "espaco"
                else None
            )
            _acoes_gestor(bool(espacos), espaco_sel)

    _marcar_ativo(chave_ativa)


def _rodape(eu: Perfil) -> None:
    # Perfil e "Sair" dividem a mesma linha: o botão vira um ícone discreto no
    # canto, como no protótipo, em vez de uma barra que competia com o
    # "Criar Tarefa". O contêiner com `key` dá o gancho `.st-key-...` que o CSS
    # usa para afinar só este botão.
    with st.container(key="rodape_perfil"):
        col_perfil, col_sair = st.columns([1, 0.28], vertical_alignment="center")

        col_perfil.markdown(
            limpar(f"""
            <div class="perfil-rodape">
              {avatar(eu.nome)}
              <div class="perfil-texto">
                <div class="perfil-nome">{esc(eu.nome)}</div>
                <div class="perfil-cargo">{esc(eu.cargo or ROTULO_PAPEL[eu.papel])}</div>
              </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        if col_sair.button(":material/logout:", key="btn_sair", help="Sair da conta"):
            logout()


def render(eu: Perfil) -> str:
    """Desenha a sidebar e devolve a view escolhida."""
    with st.sidebar:
        _cabecalho()

        if eu.pode_gerenciar:
            if st.button(":material/add:  Criar tarefa", type="primary", use_container_width=True,
                         key="btn_criar"):
                task_detail.abrir_criacao()
                st.rerun()

        # Quadro/Lista viraram abas na área de conteúdo, como no protótipo.
        # Aqui fica só a navegação entre telas. Para quem não é gestor sobra
        # uma opção só, e um rádio de item único é ruído — vira um link fixo.
        opcoes_nav = ["Início", "Dashboard"]
        if eu.pode_gerenciar:
            opcoes_nav.append("Equipe")

        view = st.radio(
            "Navegação", opcoes_nav,
            label_visibility="collapsed", key="nav",
        )

        _arvore(eu)
        _rodape(eu)

    return view
