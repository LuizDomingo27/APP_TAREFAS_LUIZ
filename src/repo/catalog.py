"""Leitura e escrita de perfis, allowlist, espaços e listas.

Toda escrita aqui passa pelo RLS de `02_rls.sql` — se quem chamou não for
gestor, o Postgres devolve zero linhas em vez de erro. Por isso as funções
de gestão retornam bool: `False` significa "o banco recusou".
"""

from __future__ import annotations

import streamlit as st

from src.db import executar, get_client
from src.models import Perfil

TTL = 30  # segundos; leituras são baratas e a equipe é pequena


def invalidar_cache() -> None:
    st.cache_data.clear()


# ------------------------------------------------------------------ perfis


@st.cache_data(ttl=TTL, show_spinner=False)
def listar_perfis() -> list[dict]:
    resp = executar(get_client().table("profiles").select("*").order("nome"))
    return resp.data or []


def pendentes() -> list[Perfil]:
    return [
        Perfil.de_linha(l)
        for l in listar_perfis()
        if not l.get("ativo") and not l.get("recusado")
    ]


def equipe() -> list[Perfil]:
    return [Perfil.de_linha(l) for l in listar_perfis() if l.get("ativo")]


def recusados() -> list[Perfil]:
    return [
        Perfil.de_linha(l)
        for l in listar_perfis()
        if l.get("recusado") and not l.get("ativo")
    ]


def _atualizar_perfil(user_id: str, campos: dict) -> bool:
    resp = executar(
        get_client().table("profiles").update(campos).eq("id", user_id)
    )
    invalidar_cache()
    return bool(resp.data)


def liberar(user_id: str) -> bool:
    return _atualizar_perfil(user_id, {"ativo": True, "recusado": False})


def recusar(user_id: str) -> bool:
    return _atualizar_perfil(user_id, {"ativo": False, "recusado": True})


def definir_gestor(user_id: str, gestor: bool) -> bool:
    return _atualizar_perfil(user_id, {"gestor": gestor})


# -------------------------------------------------------------- allowlist


@st.cache_data(ttl=TTL, show_spinner=False)
def listar_convites() -> list[dict]:
    resp = executar(
        get_client().table("allowed_emails").select("*").order("email")
    )
    return resp.data or []


def convidar(email: str, nome: str | None, gestor: bool) -> bool:
    resp = executar(
        get_client()
        .table("allowed_emails")
        .upsert(
            {
                "email": email.strip().lower(),
                "nome": (nome or "").strip() or None,
                "gestor": gestor,
            },
            on_conflict="email",
        )
    )
    invalidar_cache()
    return bool(resp.data)


def remover_convite(email: str) -> bool:
    resp = executar(
        get_client().table("allowed_emails").delete().eq("email", email)
    )
    invalidar_cache()
    return bool(resp.data)


# -------------------------------------------------------- espaços e listas


@st.cache_data(ttl=TTL, show_spinner=False)
def espacos() -> list[dict]:
    resp = executar(get_client().table("spaces").select("*").order("ordem"))
    return resp.data or []


@st.cache_data(ttl=TTL, show_spinner=False)
def listas() -> list[dict]:
    resp = executar(get_client().table("lists").select("*").order("ordem"))
    return resp.data or []


def criar_espaco(nome: str, prefixo: str, cor: str) -> bool:
    """Cria um espaço. `ordem` entra no fim da árvore; o RLS barra não-gestor.

    O `prefixo` é único no banco (vira o código das tarefas, tipo DEV-101). A
    tela já checa duplicidade antes de chamar aqui, mas se dois gestores
    correrem juntos o Postgres é quem tem a palavra final — e aí o `APIError`
    de violação de unicidade sobe para a tela tratar.
    """
    ordem = max((e.get("ordem", 0) for e in espacos()), default=-1) + 1
    resp = executar(
        get_client()
        .table("spaces")
        .insert(
            {
                "nome": nome.strip(),
                "prefixo": prefixo.strip().upper(),
                "cor": cor,
                "ordem": ordem,
            }
        )
    )
    invalidar_cache()
    return bool(resp.data)


def criar_lista(space_id: str, nome: str, icone: str = "list") -> bool:
    """Cria uma lista dentro de um espaço, no fim da ordem daquele espaço."""
    irmas = [l for l in listas() if l["space_id"] == space_id]
    ordem = max((l.get("ordem", 0) for l in irmas), default=-1) + 1
    resp = executar(
        get_client()
        .table("lists")
        .insert(
            {
                "space_id": space_id,
                "nome": nome.strip(),
                "icone": icone,
                "ordem": ordem,
            }
        )
    )
    invalidar_cache()
    return bool(resp.data)


def excluir_espaco(space_id: str) -> bool:
    """Apaga o espaço — e, por cascade do banco, todas as suas listas, as
    tarefas dessas listas e as tags, subtarefas e comentários delas.

    A cascata inteira está declarada em `01_schema.sql` (cada FK com
    `on delete cascade`), então um único delete aqui derruba a árvore toda
    numa transação só — sem sobrar registro órfão apontando para o espaço.

    Devolve False quando o RLS recusa: `spaces_write` em `02_rls.sql` só
    libera gestor. A tela já esconde o botão de não-gestor; esta é a segunda
    tranca, a que vale mesmo.
    """
    resp = executar(get_client().table("spaces").delete().eq("id", space_id))
    invalidar_cache()
    return bool(resp.data)
