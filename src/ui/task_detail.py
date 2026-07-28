"""Painel de detalhe da tarefa — criar, editar, excluir, subtarefas e comentários.

O protótipo usa um drawer lateral; aqui é `st.dialog`, que é o equivalente
nativo. O modal não guarda estado próprio: quem manda é
`st.session_state["tarefa_aberta"]` (id) ou `["criando_tarefa"]` (bool). Assim
qualquer `st.rerun()` depois de uma escrita reabre o modal no mesmo lugar, e
fechar é só limpar a chave.

Daí o `on_dismiss=fechar` nos dois modais. O X, o ESC e o clique fora só
escondem o modal no navegador — por padrão o Streamlit nem avisa o servidor.
A chave continuaria em pé, e o próximo rerun (mudar o status de um card,
filtrar, qualquer coisa) desenharia o modal de novo, do nada.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.models import Perfil, Prioridade, Status
from src.repo import catalog, tasks
from src.ui.componentes import STATUS_ORDEM, avatar, esc, limpar

SEM_RESPONSAVEL = "Sem responsável"


# ------------------------------------------------------------------ estado


def abrir(task_id: str) -> None:
    st.session_state["tarefa_aberta"] = task_id
    st.session_state.pop("confirmar_exclusao", None)


def fechar() -> None:
    st.session_state.pop("tarefa_aberta", None)
    st.session_state.pop("criando_tarefa", None)
    st.session_state.pop("confirmar_exclusao", None)


def abrir_criacao() -> None:
    st.session_state["criando_tarefa"] = True


# ------------------------------------------------------------- auxiliares


def _mapa_responsaveis() -> dict[str, str | None]:
    """Rótulo -> id. A ordem importa: 'Sem responsável' precisa ser o índice 0."""
    ativos = [p for p in catalog.listar_perfis() if p.get("ativo")]
    return {SEM_RESPONSAVEL: None} | {p["nome"]: p["id"] for p in ativos}


def _mapa_listas() -> dict[str, str]:
    """'Espaço / Lista' -> list_id."""
    nomes_espaco = {e["id"]: e["nome"] for e in catalog.espacos()}
    return {
        f"{nomes_espaco.get(l['space_id'], '—')} / {l['nome']}": l["id"]
        for l in catalog.listas()
    }


def _para_date(iso: str | None) -> date | None:
    if not iso:
        return None
    try:
        return date.fromisoformat(str(iso)[:10])
    except ValueError:
        return None


def _campos_comuns(tarefa: dict | None, chave: str, pode_gerenciar: bool = True) -> dict:
    """Os widgets compartilhados pelo criar e pelo editar.

    Devolve o dicionário pronto para o banco — inclusive `tags`, que sai
    separado porque mora em outra tabela.
    """
    tarefa = tarefa or {}
    responsaveis = _mapa_responsaveis()
    rotulos = list(responsaveis)

    atual = tarefa.get("responsavel_id")
    indice = next(
        (i for i, r in enumerate(rotulos) if responsaveis[r] == atual), 0
    )

    # Os pares seguem o modal do protótipo: Status/Prioridade, depois
    # Responsável/Data limite, e Tag e Descrição ocupando a linha inteira.
    col_status, col_prio = st.columns(2)
    status = col_status.selectbox(
        "Status",
        STATUS_ORDEM,
        index=STATUS_ORDEM.index(tarefa.get("status") or Status.A_FAZER.value),
        key=f"{chave}_status",
    )
    prioridade = col_prio.selectbox(
        "Prioridade",
        [p.value for p in Prioridade],
        index=[p.value for p in Prioridade].index(
            tarefa.get("prioridade") or Prioridade.NORMAL.value
        ),
        key=f"{chave}_prioridade",
        disabled=not pode_gerenciar,
    )

    col_resp, col_data = st.columns(2)
    responsavel = col_resp.selectbox(
        "Responsável", rotulos, index=indice, key=f"{chave}_resp",
        disabled=not pode_gerenciar,
    )
    limite = col_data.date_input(
        "Data limite",
        value=_para_date(tarefa.get("data_limite")),
        format="DD/MM/YYYY",
        key=f"{chave}_data",
        disabled=not pode_gerenciar,
    )

    etiquetas = st.multiselect(
        "Tags",
        options=sorted(set(tasks.tags_existentes()) | set(tarefa.get("tags") or [])),
        default=tarefa.get("tags") or [],
        accept_new_options=True,
        placeholder="Frontend, Bug, Design…",
        key=f"{chave}_tags",
        disabled=not pode_gerenciar,
    )

    descricao = st.text_area(
        "Descrição",
        value=tarefa.get("descricao") or "",
        placeholder="Insira detalhes…",
        height=80,
        key=f"{chave}_descricao",
        disabled=not pode_gerenciar,
    )

    return {
        "status": status or tarefa.get("status") or Status.A_FAZER.value,
        "prioridade": prioridade,
        "responsavel_id": responsaveis[responsavel],
        "data_limite": limite.isoformat() if limite else None,
        "descricao": descricao,
        "tags": etiquetas,
    }


# ---------------------------------------------------------------- criação


@st.dialog("Nova tarefa", width="small", on_dismiss=fechar)
def dialog_criar(eu: Perfil | None = None) -> None:
    if eu and not eu.pode_gerenciar:
        st.error("Apenas gestores ou administradores podem criar tarefas.")
        if st.button("Fechar"):
            fechar()
            st.rerun()
        return

    listas = _mapa_listas()
    if not listas:
        st.warning("Nenhuma lista cadastrada — crie um espaço e uma lista antes.")
        return

    with st.form("form_criar", border=False):
        titulo = st.text_input(
            "Título da tarefa", placeholder="Ex: Criar documentação da API"
        )
        onde = st.selectbox("Lista", list(listas), key="criar_lista")
        campos = _campos_comuns(None, "criar", pode_gerenciar=True)

        # Botões encostados à direita, como no protótipo: a primeira coluna é
        # só o espaço vazio que os empurra para lá.
        _, col_cancelar, col_ok = st.columns([2, 1, 1])
        cancelar = col_cancelar.form_submit_button("Cancelar", use_container_width=True)
        criar = col_ok.form_submit_button(
            "Criar tarefa", type="primary", use_container_width=True
        )

    if cancelar:
        fechar()
        st.rerun()

    if criar:
        if not titulo.strip():
            st.warning("Dê um título para a tarefa.")
            return

        etiquetas = campos.pop("tags")
        task_id = tasks.criar(list_id=listas[onde], titulo=titulo, tags=etiquetas, **campos)
        if not task_id:
            st.error("O banco recusou a criação. Recarregue a página e tente de novo.")
            return

        fechar()
        st.toast("Tarefa criada.")
        st.rerun()


# ----------------------------------------------------------- subtarefas


def _secao_subtarefas(task_id: str, pode_gerenciar: bool = True) -> None:
    itens = tasks.listar_subtarefas(task_id)
    feitas = sum(1 for s in itens if s["concluida"])

    st.markdown(
        f'<div class="secao-titulo">Subtarefas '
        f'<span class="contador-simples">{feitas}/{len(itens)}</span></div>',
        unsafe_allow_html=True,
    )

    for s in itens:
        if pode_gerenciar:
            col_check, col_lixo = st.columns([12, 1], vertical_alignment="center")
            marcada = col_check.checkbox(
                s["titulo"], value=s["concluida"], key=f"sub_{s['id']}"
            )
            if marcada != s["concluida"]:
                tasks.alternar_subtarefa(s["id"], marcada)
                st.rerun()

            if col_lixo.button(
                ":material/close:", key=f"delsub_{s['id']}", help="Remover subtarefa"
            ):
                tasks.excluir_subtarefa(s["id"])
                st.rerun()
        else:
            st.checkbox(
                s["titulo"], value=s["concluida"], key=f"sub_{s['id']}", disabled=True
            )

    if pode_gerenciar:
        with st.form(f"add_sub_{task_id}", clear_on_submit=True, border=False):
            col_txt, col_btn = st.columns([3, 1])
            nova = col_txt.text_input(
                "Nova subtarefa", placeholder="Adicionar subtarefa…",
                label_visibility="collapsed",
            )
            if col_btn.form_submit_button("Adicionar", use_container_width=True):
                if nova.strip():
                    tasks.add_subtarefa(task_id, nova)
                    st.rerun()


# ---------------------------------------------------------- comentários


def _secao_comentarios(task_id: str, eu: Perfil) -> None:
    itens = tasks.listar_comentarios(task_id)
    nomes = {p["id"]: p["nome"] for p in catalog.listar_perfis()}

    st.markdown(
        f'<div class="secao-titulo">Comentários '
        f'<span class="contador-simples">{len(itens)}</span></div>',
        unsafe_allow_html=True,
    )

    if not itens:
        st.caption("Nenhum comentário ainda.")

    for c in itens:
        autor = nomes.get(c["autor_id"], "—")
        col_texto, col_lixo = st.columns([12, 1], vertical_alignment="center")
        col_texto.markdown(
            limpar(f"""
            <div class="comentario">
              {avatar(autor, mini=True)}
              <div>
                <div class="comentario-topo">{esc(autor)}
                  <span class="comentario-data">{esc(str(c["criado_em"])[:10])}</span>
                </div>
                <div class="comentario-texto">{esc(c["texto"])}</div>
              </div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if c["autor_id"] == eu.id or eu.pode_gerenciar:
            if col_lixo.button(
                ":material/close:", key=f"delcom_{c['id']}", help="Apagar comentário"
            ):
                tasks.excluir_comentario(c["id"])
                st.rerun()

    with st.form(f"add_com_{task_id}", clear_on_submit=True, border=False):
        texto = st.text_area(
            "Comentário", placeholder="Escreva um comentário…",
            label_visibility="collapsed", height=80,
        )
        if st.form_submit_button("Comentar"):
            if texto.strip():
                tasks.add_comentario(task_id, texto)
                st.rerun()


# ----------------------------------------------------------------- edição


@st.dialog("Detalhe da tarefa", width="small", on_dismiss=fechar)
def dialog_detalhe(tarefa: dict, eu: Perfil) -> None:
    pode_gerenciar = eu.pode_gerenciar

    st.markdown(
        f'<div class="detalhe-codigo">{esc(tarefa.get("codigo") or "—")}</div>',
        unsafe_allow_html=True,
    )

    with st.form(f"form_editar_{tarefa['id']}", border=False):
        titulo = st.text_input(
            "Título da tarefa", value=tarefa["titulo"], key="edit_titulo",
            disabled=not pode_gerenciar,
        )
        campos = _campos_comuns(tarefa, "edit", pode_gerenciar=pode_gerenciar)

        _, col_salvar = st.columns([1, 1])
        salvar = col_salvar.form_submit_button(
            "Salvar alterações", type="primary", use_container_width=True
        )

    if salvar:
        if not pode_gerenciar:
            # Membro comum só pode alterar o status
            if campos["status"] != tarefa.get("status"):
                tasks.mudar_status(tarefa["id"], campos["status"])
                st.toast("Status alterado.")
            fechar()
            st.rerun()
        else:
            if not titulo.strip():
                st.warning("O título não pode ficar vazio.")
            else:
                etiquetas = campos.pop("tags")
                try:
                    tasks.atualizar(
                        tarefa["id"],
                        {"titulo": titulo.strip(), **campos},
                        visto_em=tarefa.get("atualizado_em"),
                    )
                except tasks.ConflitoDeEdicao:
                    st.error(
                        "Outra pessoa salvou esta tarefa enquanto você editava. "
                        "Feche e abra de novo para ver a versão atual."
                    )
                else:
                    if set(etiquetas) != set(tarefa.get("tags") or []):
                        tasks.definir_tags(tarefa["id"], etiquetas)
                    st.toast("Tarefa salva.")
                    fechar()
                    st.rerun()

    st.divider()
    _secao_subtarefas(tarefa["id"], pode_gerenciar=pode_gerenciar)
    st.divider()
    _secao_comentarios(tarefa["id"], eu)
    st.divider()

    # Exclusão só disponível para quem possui permissão de gestão
    if pode_gerenciar:
        if st.session_state.get("confirmar_exclusao") == tarefa["id"]:
            st.warning(f"Excluir **{tarefa['titulo']}**? Isso não tem volta.")
            col_sim, col_nao = st.columns(2)
            if col_sim.button(
                "Sim, excluir", type="primary", key="btn_confirmar_exclusao",
                use_container_width=True,
            ):
                if tasks.excluir(tarefa["id"]):
                    fechar()
                    st.toast("Tarefa excluída.")
                    st.rerun()
                else:
                    st.error(
                        "O banco recusou a exclusão."
                    )
            if col_nao.button("Cancelar", use_container_width=True):
                st.session_state.pop("confirmar_exclusao", None)
                st.rerun()
        elif st.button("Excluir tarefa", key="btn_excluir", use_container_width=True):
            st.session_state["confirmar_exclusao"] = tarefa["id"]
            st.rerun()


# ------------------------------------------------------------- despachante


def render_modais(eu: Perfil) -> None:
    """Chamada uma vez por run, depois das telas: abre o modal que estiver pedido."""
    if st.session_state.get("criando_tarefa"):
        dialog_criar(eu)
        return

    task_id = st.session_state.get("tarefa_aberta")
    if not task_id:
        return

    tarefa = tasks.obter(task_id)
    if tarefa is None:
        # Sumiu do banco entre o clique e o rerun (alguém excluiu).
        fechar()
        return

    dialog_detalhe(tarefa, eu)
