"""Leitura e escrita de tarefas, tags, subtarefas e comentários.

As buscas trazem tudo de uma vez e o filtro acontece em memória — com 5
pessoas e algumas centenas de tarefas isso é mais rápido que uma ida ao
banco por filtro, e evita invalidar cache a cada tecla.

A escrita é o oposto: nada de cache, e toda função que grava chama
`invalidar()` no fim, senão o quadro continuaria mostrando o estado velho
por até `TTL` segundos.
"""

from __future__ import annotations

from collections import defaultdict

import streamlit as st

from src.db import executar, get_client

TTL = 30


def invalidar() -> None:
    """Derruba o cache de leitura. Chamada depois de toda escrita."""
    st.cache_data.clear()


@st.cache_data(ttl=TTL, show_spinner=False)
def _linhas() -> list[dict]:
    resp = executar(
        get_client().table("tasks").select("*").order("ordem").order("criado_em")
    )
    return resp.data or []


@st.cache_data(ttl=TTL, show_spinner=False)
def _tags() -> dict[str, list[str]]:
    resp = executar(get_client().table("task_tags").select("task_id, tag"))
    agrupado: dict[str, list[str]] = defaultdict(list)
    for linha in resp.data or []:
        agrupado[linha["task_id"]].append(linha["tag"])
    return dict(agrupado)


@st.cache_data(ttl=TTL, show_spinner=False)
def _subtarefas() -> dict[str, tuple[int, int]]:
    """task_id -> (concluídas, total)."""
    resp = executar(get_client().table("subtasks").select("task_id, concluida"))
    contagem: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for linha in resp.data or []:
        par = contagem[linha["task_id"]]
        par[1] += 1
        if linha["concluida"]:
            par[0] += 1
    return {k: (v[0], v[1]) for k, v in contagem.items()}


def listar(
    *,
    list_ids: set[str] | None = None,
    busca: str = "",
    prioridade: str = "Todas",
    responsavel_id: str | None = None,
) -> list[dict]:
    """Tarefas já enriquecidas com tags e progresso de subtarefas."""
    tags = _tags()
    subs = _subtarefas()
    termo = busca.strip().lower()

    resultado: list[dict] = []
    for linha in _linhas():
        if list_ids is not None and linha["list_id"] not in list_ids:
            continue
        if prioridade != "Todas" and linha["prioridade"] != prioridade:
            continue
        if responsavel_id and linha.get("responsavel_id") != responsavel_id:
            continue

        etiquetas = tags.get(linha["id"], [])
        if termo:
            alvo = " ".join(
                [linha["titulo"], linha.get("codigo") or "", *etiquetas]
            ).lower()
            if termo not in alvo:
                continue

        feitas, total = subs.get(linha["id"], (0, 0))
        resultado.append(
            {**linha, "tags": etiquetas, "sub_feitas": feitas, "sub_total": total}
        )

    return resultado


def tags_existentes() -> list[str]:
    """Vocabulário de tags já usado, para sugerir em vez de digitar de novo."""
    todas = {t for lista in _tags().values() for t in lista}
    return sorted(todas)


def obter(task_id: str) -> dict | None:
    """Tarefa única, já enriquecida. Lê da mesma lista em cache do quadro."""
    for t in listar():
        if t["id"] == task_id:
            return t
    return None


def contagem_por_espaco(listas: list[dict]) -> dict[str, int]:
    """space_id -> número de tarefas, para o contador da árvore da sidebar."""
    lista_para_espaco = {l["id"]: l["space_id"] for l in listas}
    total: dict[str, int] = defaultdict(int)
    for linha in _linhas():
        space_id = lista_para_espaco.get(linha["list_id"])
        if space_id:
            total[space_id] += 1
    return dict(total)


# =========================================================== escrita


class ConflitoDeEdicao(Exception):
    """Alguém salvou a mesma tarefa entre a leitura e o seu clique em Salvar."""


def criar(
    *,
    list_id: str,
    titulo: str,
    descricao: str = "",
    status: str = "A Fazer",
    prioridade: str = "Normal",
    responsavel_id: str | None = None,
    data_limite: str | None = None,
    tags: list[str] | None = None,
) -> str | None:
    """Insere a tarefa e devolve o id. `codigo` vem do trigger do banco."""
    resp = executar(
        get_client()
        .table("tasks")
        .insert(
            {
                "list_id": list_id,
                "titulo": titulo.strip(),
                "descricao": descricao.strip(),
                "status": status,
                "prioridade": prioridade,
                "responsavel_id": responsavel_id,
                "data_limite": data_limite,
            }
        )
    )
    if not resp.data:
        return None

    task_id = resp.data[0]["id"]
    if tags:
        _gravar_tags(task_id, tags)
    invalidar()
    return task_id


def atualizar(task_id: str, campos: dict, *, visto_em: str | None = None) -> dict:
    """Grava os campos alterados.

    `visto_em` é o `atualizado_em` que estava na tela quando o formulário foi
    aberto. Com ele no WHERE, quem chega em segundo lugar não sobrescreve
    calado o trabalho do primeiro: o update não casa nenhuma linha e vira
    `ConflitoDeEdicao`.
    """
    consulta = get_client().table("tasks").update(campos).eq("id", task_id)
    if visto_em:
        consulta = consulta.eq("atualizado_em", visto_em)

    resp = executar(consulta)
    invalidar()

    if not resp.data:
        if visto_em:
            raise ConflitoDeEdicao
        return {}
    return resp.data[0]


def mudar_status(task_id: str, status: str) -> None:
    """Atalho do card e da lista — sem trava de concorrência de propósito.

    Mudar de coluna é uma ação de um clique; barrar com "alguém editou antes"
    seria pior que sobrescrever um campo que a outra pessoa também mexeu.
    """
    executar(
        get_client().table("tasks").update({"status": status}).eq("id", task_id)
    )
    invalidar()


def excluir(task_id: str) -> bool:
    """Apaga a tarefa. Tags, subtarefas e comentários caem por cascade.

    Devolve False quando o RLS recusa — só quem criou ou um gestor exclui.
    """
    resp = executar(get_client().table("tasks").delete().eq("id", task_id))
    invalidar()
    return bool(resp.data)


# ------------------------------------------------------------------- tags


def _gravar_tags(task_id: str, tags: list[str]) -> None:
    cliente = get_client()
    executar(cliente.table("task_tags").delete().eq("task_id", task_id))
    limpas = []
    for t in tags:
        t = t.strip()
        if t and t not in limpas:
            limpas.append(t)
    if limpas:
        executar(
            cliente.table("task_tags").insert(
                [{"task_id": task_id, "tag": t} for t in limpas]
            )
        )


def definir_tags(task_id: str, tags: list[str]) -> None:
    """Substitui o conjunto de tags. A chave primária é (task_id, tag), então
    apagar e reinserir é mais simples — e mais barato — que diferenciar."""
    _gravar_tags(task_id, tags)
    invalidar()


# ------------------------------------------------------------- subtarefas


def listar_subtarefas(task_id: str) -> list[dict]:
    """Sem cache: o painel de detalhe precisa refletir o clique anterior."""
    resp = executar(
        get_client()
        .table("subtasks")
        .select("*")
        .eq("task_id", task_id)
        .order("ordem")
        .order("criado_em")
    )
    return resp.data or []


def add_subtarefa(task_id: str, titulo: str) -> bool:
    resp = executar(
        get_client().table("subtasks").insert({"task_id": task_id, "titulo": titulo.strip()})
    )
    invalidar()
    return bool(resp.data)


def alternar_subtarefa(subtask_id: str, concluida: bool) -> None:
    executar(
        get_client().table("subtasks").update({"concluida": concluida}).eq("id", subtask_id)
    )
    invalidar()


def excluir_subtarefa(subtask_id: str) -> None:
    executar(get_client().table("subtasks").delete().eq("id", subtask_id))
    invalidar()


# ------------------------------------------------------------ comentários


def listar_comentarios(task_id: str) -> list[dict]:
    resp = executar(
        get_client()
        .table("comments")
        .select("*")
        .eq("task_id", task_id)
        .order("criado_em")
    )
    return resp.data or []


def add_comentario(task_id: str, texto: str) -> bool:
    resp = executar(
        get_client().table("comments").insert({"task_id": task_id, "texto": texto.strip()})
    )
    return bool(resp.data)


def excluir_comentario(comment_id: str) -> bool:
    """RLS deixa só o autor (ou um gestor) apagar."""
    resp = executar(get_client().table("comments").delete().eq("id", comment_id))
    return bool(resp.data)
