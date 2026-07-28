"""Leitura e escrita de perfis, allowlist, espaços e listas.

Toda escrita aqui passa pelo RLS de `02_rls.sql` — se quem chamou não for
gestor, o Postgres devolve zero linhas em vez de erro. Por isso as funções
de gestão retornam bool: `False` significa "o banco recusou".
"""

from __future__ import annotations

import streamlit as st

from src.db import executar, get_client
from src.models import PAPEIS, Perfil

TTL = 30  # segundos; leituras são baratas e a equipe é pequena


class AcaoBloqueada(RuntimeError):
    """Regra do app barrou a alteração antes de ela chegar ao banco.

    Diferente do `False` que as funções devolvem: `False` é o Postgres
    recusando (RLS), isto aqui é o app recusando. A mensagem já vem pronta
    para a tela mostrar.
    """


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


# ------------------------------------------------------------------ travas
#
# As duas regras que não podem ser quebradas por caminho nenhum:
#
#   1. ninguém tira o próprio acesso;
#   2. o workspace nunca fica sem alguém que possa gerenciar.
#
# Ficam aqui, e não só na tela, porque a tela erra: a versão anterior
# desabilitava o "Desativar" apenas quando você era o *último* gestor, então
# bastava existir um segundo gestor para você conseguir se desativar — e se
# esse segundo tivesse saído antes, o workspace ficava sem ninguém. Sem
# usuário ativo não há como reentrar pelo app: só pelo SQL Editor, que é
# exatamente o que a tela de Equipe existe para evitar.


def _eu_id() -> str | None:
    """Id de quem está logado.

    Lido direto do `session_state` de propósito: importar `src.auth` aqui
    puxaria a camada de UI para dentro do repositório.
    """
    perfil = st.session_state.get("perfil")
    return getattr(perfil, "id", None)


def _proibir_alvo_proprio(user_id: str, acao: str) -> None:
    if _eu_id() is not None and user_id == _eu_id():
        raise AcaoBloqueada(
            f"Você não pode {acao} da sua própria conta. Peça a outro gestor "
            "ou administrador."
        )


def _proibir_ultimo_gestor(user_id: str, acao: str) -> None:
    """Barra a mudança que deixaria o workspace sem nenhum gestor/admin."""
    alvo = next((p for p in equipe() if p.id == user_id), None)
    if alvo is None or not alvo.pode_gerenciar:
        return  # não é quem gerencia: a saída dele não muda a contagem
    if any(p.pode_gerenciar for p in equipe() if p.id != user_id):
        return
    raise AcaoBloqueada(
        f"{alvo.nome} é a única pessoa com acesso de gestão. Promova outra "
        f"antes de {acao}."
    )


# ------------------------------------------------------------------ escrita


def liberar(user_id: str) -> bool:
    return _atualizar_perfil(user_id, {"ativo": True, "recusado": False})


def recusar(user_id: str) -> bool:
    _proibir_alvo_proprio(user_id, "remover o acesso")
    _proibir_ultimo_gestor(user_id, "desativá-la")
    return _atualizar_perfil(user_id, {"ativo": False, "recusado": True})


def definir_papel(user_id: str, papel: str) -> bool:
    """Grava membro / gestor / admin.

    Gestor e admin dão o mesmo poder (ver `Perfil.pode_gerenciar`); são duas
    colunas e não uma só para o RLS do Postgres poder decidir sem interpretar
    texto, e para o rótulo continuar visível na tela.
    """
    if papel not in PAPEIS:
        raise AcaoBloqueada(f"Papel desconhecido: {papel!r}.")
    _proibir_alvo_proprio(user_id, "mudar o nível de acesso")
    if papel == "membro":
        _proibir_ultimo_gestor(user_id, "rebaixá-la")
    return _atualizar_perfil(
        user_id, {"gestor": papel == "gestor", "admin": papel == "admin"}
    )


# -------------------------------------------------------------- allowlist


@st.cache_data(ttl=TTL, show_spinner=False)
def listar_convites() -> list[dict]:
    resp = executar(
        get_client().table("allowed_emails").select("*").order("email")
    )
    return resp.data or []


def convidar(email: str, nome: str | None, papel: str = "membro") -> bool:
    """Pré-autoriza um e-mail já com o papel que ele terá ao se cadastrar.

    Quem lê estas colunas é o trigger `tk_handle_new_user`, no cadastro.
    """
    if papel not in PAPEIS:
        raise AcaoBloqueada(f"Papel desconhecido: {papel!r}.")
    resp = executar(
        get_client()
        .table("allowed_emails")
        .upsert(
            {
                "email": email.strip().lower(),
                "nome": (nome or "").strip() or None,
                "gestor": papel == "gestor",
                "admin": papel == "admin",
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
