"""Quadro Kanban — 4 colunas, uma por status."""

from __future__ import annotations

import streamlit as st

from src.repo import tasks
from src.ui import task_detail
from src.ui.componentes import (
    CORES_STATUS,
    STATUS_ORDEM,
    atrasada,
    avatar,
    badge_prioridade,
    data_curta,
    esc,
    icone,
    limpar,
)


def _card(tarefa: dict, nome_responsavel: str | None) -> str:
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in tarefa["tags"][:2])

    progresso = ""
    if tarefa["sub_total"]:
        progresso = (
            f'<span class="meta-item">{icone("check-square")}'
            f'{tarefa["sub_feitas"]}/{tarefa["sub_total"]}</span>'
        )

    venceu = atrasada(tarefa.get("data_limite"), tarefa["status"])
    cor_data = "color:#dc2626;font-weight:600" if venceu else ""

    # Sem <div class="card"> em volta: quem desenha a moldura branca é o
    # próprio container do Streamlit (`.st-key-card_…`), para que o botão de
    # abrir e o seletor de status caiam dentro da caixa, e não embaixo dela.
    return limpar(f"""
    <div class="card-topo">
      <span class="card-codigo">{esc(tarefa.get("codigo") or "—")}</span>
      {badge_prioridade(tarefa["prioridade"])}
    </div>
    <h4>{esc(tarefa["titulo"])}</h4>
    <div>{tags}</div>
    <div class="card-rodape">
      <div class="meta">
        {progresso}
        <span class="meta-item" style="{cor_data}">{icone("calendar")}{data_curta(tarefa.get("data_limite"))}</span>
      </div>
      {avatar(nome_responsavel, mini=True)}
    </div>
    """)


def _seletor_status(tarefa: dict) -> None:
    """O substituto do arrastar-e-soltar, decidido no PLANO.

    Fica acima do botão que cobre o card (z-index no CSS), senão o clique
    abriria o detalhe em vez de abrir a lista de status.

    O status entra na `key` de propósito: se outra pessoa mover a tarefa, a
    chave muda e o seletor renasce já na coluna certa. Com chave fixa, o
    valor velho guardado na sessão venceria o `index` e o app desfaria a
    mudança do colega no primeiro rerun.
    """
    atual = tarefa["status"]
    with st.container(key=f"status_{tarefa['id']}"):
        novo = st.selectbox(
            "Mover para",
            STATUS_ORDEM,
            index=STATUS_ORDEM.index(atual) if atual in STATUS_ORDEM else 0,
            label_visibility="collapsed",
            key=f"sel_status_{tarefa['id']}_{atual}",
        )
    if novo != atual:
        tasks.mudar_status(tarefa["id"], novo)
        st.toast(f"Movida para {novo}.", icon="↔️")
        st.rerun()


def _card_clicavel(tarefa: dict, nome_responsavel: str | None) -> None:
    """Card + um botão transparente esticado por cima dele.

    Streamlit não deixa embutir um widget dentro de um bloco de HTML, então o
    caminho é o inverso: o botão vem depois do card e o CSS o joga em
    `position:absolute` sobre o container. O rótulo continua sendo o título
    da tarefa (escondido com `font-size:0`), que é o que o leitor de tela
    anuncia — um botão sem texto não diria nada.
    """
    with st.container(key=f"card_{tarefa['id']}"):
        st.markdown(_card(tarefa, nome_responsavel), unsafe_allow_html=True)
        if st.button(tarefa["titulo"], key=f"abrir_{tarefa['id']}"):
            task_detail.abrir(tarefa["id"])
            st.rerun()
        _seletor_status(tarefa)


def render(tarefas: list[dict], nomes: dict[str, str]) -> None:
    por_status: dict[str, list[dict]] = {s: [] for s in STATUS_ORDEM}
    for t in tarefas:
        por_status.setdefault(t["status"], []).append(t)

    colunas = st.columns(len(STATUS_ORDEM), gap="small")

    for indice, (coluna, status) in enumerate(zip(colunas, STATUS_ORDEM)):
        itens = por_status.get(status, [])
        ponto, fundo, texto = CORES_STATUS[status]

        with coluna:
            st.markdown(
                limpar(f"""
                <div class="col-topo">
                  <span class="ponto" style="background:{ponto}"></span>
                  <h3>{esc(status)}</h3>
                  <span class="contador" style="background:{fundo};color:{texto}">
                    {len(itens)}
                  </span>
                </div>
                """),
                unsafe_allow_html=True,
            )

            # O fundo da coluna sai de um container com `key` (CSS em
            # `.st-key-coluna_N`) porque agora cada card carrega um botão
            # de verdade dentro — não dá mais para desenhar a coluna inteira
            # como um bloco de HTML só.
            with st.container(key=f"coluna_{indice}"):
                if not itens:
                    st.markdown(
                        '<div class="vazio">Nenhuma tarefa aqui</div>',
                        unsafe_allow_html=True,
                    )
                for t in itens:
                    _card_clicavel(t, nomes.get(t.get("responsavel_id") or ""))
