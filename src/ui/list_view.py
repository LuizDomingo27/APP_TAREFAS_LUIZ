"""Visão em Lista — a tabela do protótipo, montada em HTML.

`st.dataframe` não aceita HTML nas células, então os badges de prioridade e
status ficariam como texto cru. Uma tabela própria é o que mantém a lista
idêntica ao Quadro em linguagem visual.
"""

from __future__ import annotations

import streamlit as st

from src.ui import task_detail
from src.ui.componentes import (
    atrasada,
    avatar,
    badge_prioridade,
    data_longa,
    esc,
    icone,
    limpar,
    pill_status,
)

CABECALHO = ["", "Nome da Tarefa", "Status", "Prioridade", "Responsável", "Data Limite", "Tags"]


def _linha(tarefa: dict, nome_responsavel: str | None) -> str:
    concluida = tarefa["status"] == "Concluído"
    marca = (
        f'<span class="check feito">{icone("check-square", 14)}</span>'
        if concluida
        else '<span class="check"></span>'
    )

    venceu = atrasada(tarefa.get("data_limite"), tarefa["status"])
    estilo_data = ' style="color:#dc2626;font-weight:600"' if venceu else ""

    tags = "".join(f'<span class="tag">{esc(t)}</span> ' for t in tarefa["tags"])

    return limpar(f"""
    <tr>
      <td>{marca}</td>
      <td class="nome">
        <span class="card-codigo">{esc(tarefa.get("codigo") or "")}</span>
        &nbsp;{esc(tarefa["titulo"])}
      </td>
      <td>{pill_status(tarefa["status"])}</td>
      <td>{badge_prioridade(tarefa["prioridade"])}</td>
      <td>
        <span style="display:inline-flex;align-items:center;gap:.4rem">
          {avatar(nome_responsavel, mini=True)}
          {esc(nome_responsavel or "Sem responsável")}
        </span>
      </td>
      <td class="data"{estilo_data}>{data_longa(tarefa.get("data_limite"))}</td>
      <td>{tags or "—"}</td>
    </tr>
    """)


def _seletor_abrir(tarefas: list[dict]) -> None:
    """Ponte para o detalhe.

    A tabela é um bloco de HTML único, então não há onde encaixar um botão
    por linha sem desmontá-la. Um seletor acima resolve o caso real — achar
    uma tarefa pelo código e abrir — sem sacrificar o visual do protótipo.
    """
    rotulos = {
        f"{t.get('codigo') or '—'} · {t['titulo']}": t["id"] for t in tarefas
    }
    col_sel, col_btn = st.columns([4, 1], vertical_alignment="bottom")
    escolhido = col_sel.selectbox(
        "Abrir tarefa",
        ["Selecione uma tarefa…", *rotulos],
        label_visibility="collapsed",
        key="lista_abrir",
    )
    if col_btn.button("Abrir", use_container_width=True, disabled=escolhido not in rotulos):
        task_detail.abrir(rotulos[escolhido])
        st.rerun()


def render(tarefas: list[dict], nomes: dict[str, str]) -> None:
    if tarefas:
        _seletor_abrir(tarefas)

    if not tarefas:
        st.markdown(
            '<div class="tabela-wrap"><div class="vazio" style="border:none">'
            "Nenhuma tarefa encontrada com os filtros atuais.</div></div>",
            unsafe_allow_html=True,
        )
        return

    ths = "".join(f"<th>{esc(c)}</th>" for c in CABECALHO)
    linhas = "".join(
        _linha(t, nomes.get(t.get("responsavel_id") or "")) for t in tarefas
    )

    st.markdown(
        limpar(f"""
        <div class="tabela-wrap">
          <div class="tabela-topo">
            <span>Lista de Tarefas</span>
            <span class="sub">{len(tarefas)} tarefa(s)</span>
          </div>
          <div style="overflow-x:auto">
            <table class="tarefas">
              <thead><tr>{ths}</tr></thead>
              <tbody>{linhas}</tbody>
            </table>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )
