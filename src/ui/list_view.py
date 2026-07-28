"""Visão em Lista — tabela profissional com layout moderno.

`st.dataframe` não aceita HTML nas células, então os badges de prioridade e
status ficariam como texto cru. Uma tabela própria é o que mantém a lista
idêntica ao Quadro em linguagem visual.

Inclui barra de resumo por status, indicador visual de atraso com pulsação,
rodapé com barra de progresso e contagem de conclusão.
"""

from __future__ import annotations

import streamlit as st

from src.ui import task_detail
from src.ui.componentes import (
    CORES_STATUS,
    STATUS_ORDEM,
    atrasada,
    avatar,
    badge_prioridade,
    data_longa,
    esc,
    icone,
    limpar,
    pill_status,
)

CABECALHO = [
    ("", "check-col"),
    ("Tarefa", "nome-col"),
    ("Status", "status-col"),
    ("Prioridade", "prio-col"),
    ("Responsável", "resp-col"),
    ("Prazo", "data-col"),
    ("Tags", "tags-col"),
]


def _resumo_status(tarefas: list[dict]) -> str:
    """Barra de mini-contadores por status acima da tabela."""
    contagens = {s: 0 for s in STATUS_ORDEM}
    for t in tarefas:
        contagens[t["status"]] = contagens.get(t["status"], 0) + 1

    itens = []
    for status in STATUS_ORDEM:
        ponto, _, _ = CORES_STATUS.get(status, ("#8d95a3", "", ""))
        itens.append(
            f'<span class="tabela-resumo-item">'
            f'<span class="ponto-mini" style="background:{ponto}"></span>'
            f'{esc(status)} <strong>{contagens[status]}</strong></span>'
        )
    return f'<div class="tabela-resumo">{"".join(itens)}</div>'


def _rodape_tabela(tarefas: list[dict]) -> str:
    """Rodapé com contagem de conclusão e barra de progresso."""
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t["status"] == "Concluído")
    pct = int(concluidas / total * 100) if total else 0

    return limpar(f"""
    <div class="tabela-rodape">
      <span><span class="numero-destaque">{total}</span> tarefa(s)</span>
      <span class="concluidas">
        <span>Concluídas <span class="numero-destaque">{concluidas}/{total}</span></span>
        <span class="barra-progresso">
          <span class="barra-progresso-fill" style="width:{pct}%"></span>
        </span>
        <span class="numero-destaque">{pct}%</span>
      </span>
    </div>
    """)


def _linha(tarefa: dict, nome_responsavel: str | None) -> str:
    concluida = tarefa["status"] == "Concluído"
    marca = (
        f'<span class="check feito">{icone("check-square", 16)}</span>'
        if concluida
        else '<span class="check"></span>'
    )

    venceu = atrasada(tarefa.get("data_limite"), tarefa["status"])
    data_txt = data_longa(tarefa.get("data_limite"))
    if venceu:
        celula_data = f'<span class="data-atrasada">{data_txt}</span>'
    else:
        celula_data = data_txt

    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in tarefa["tags"])

    resp_cls = "responsavel-cell" if nome_responsavel else "responsavel-cell sem"
    resp_txt = esc(nome_responsavel or "Sem responsável")

    return limpar(f"""
    <tr>
      <td>{marca}</td>
      <td class="nome">
        <span class="card-codigo">{esc(tarefa.get("codigo") or "")}</span>
        {esc(tarefa["titulo"])}
      </td>
      <td>{pill_status(tarefa["status"])}</td>
      <td>{badge_prioridade(tarefa["prioridade"])}</td>
      <td>
        <span class="{resp_cls}">
          {avatar(nome_responsavel, mini=True)}
          {resp_txt}
        </span>
      </td>
      <td class="data">{celula_data}</td>
      <td><span class="tags-cell">{tags or "—"}</span></td>
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

    ths = "".join(f"<th>{esc(titulo)}</th>" for titulo, _ in CABECALHO)
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
          {_resumo_status(tarefas)}
          <div style="overflow-x:auto">
            <table class="tarefas">
              <thead><tr>{ths}</tr></thead>
              <tbody>{linhas}</tbody>
            </table>
          </div>
          {_rodape_tabela(tarefas)}
        </div>
        """),
        unsafe_allow_html=True,
    )

