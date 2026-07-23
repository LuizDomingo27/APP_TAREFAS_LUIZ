"""Cliente Supabase, um por sessão de navegador."""

from __future__ import annotations

import os
from typing import Any, Protocol

import httpx
import streamlit as st
from dotenv import load_dotenv
from postgrest.exceptions import APIError
from supabase import Client, create_client

load_dotenv()


def _credenciais() -> tuple[str, str]:
    """st.secrets no deploy, .env no local."""
    url = key = None
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_ANON_KEY")
    except Exception:
        # Sem .streamlit/secrets.toml o acesso a st.secrets levanta exceção
        # em vez de devolver vazio — daí o try em volta de um .get().
        pass

    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        st.error(
            "Faltam as credenciais do Supabase. Crie um `.env` a partir do "
            "`.env.example` (local) ou preencha os secrets no Streamlit Cloud."
        )
        st.stop()
    return url, key


def get_client() -> Client:
    """O cliente fica no session_state, nunca em cache_resource.

    `sign_in_with_password` guarda o token dentro da instância; um cliente
    em `st.cache_resource` é compartilhado por todos os navegadores, então
    dois usuários simultâneos acabariam com a sessão um do outro.
    """
    if "sb_client" not in st.session_state:
        url, key = _credenciais()
        st.session_state.sb_client = create_client(url, key)
    return st.session_state.sb_client


# ------------------------------------------------------------------ falhas


class ErroDeConexao(Exception):
    """O Supabase não respondeu: internet caída, projeto pausado ou fora do ar.

    Separado dos demais erros de propósito. Um `APIError` de RLS significa
    "o banco entendeu e recusou" — isso cada tela trata do seu jeito. Já a
    conexão que não fecha não é problema de nenhuma tela específica, e sobe
    até o `app.py`, que troca a página inteira pelo aviso de reconexão.
    """


class SessaoExpirada(Exception):
    """O JWT venceu no meio do uso — só resta refazer o login."""


class _Consulta(Protocol):
    def execute(self) -> Any: ...


# Erros de transporte do httpx: DNS que não resolve, TCP recusado, timeout.
# Todos herdam de TransportError, então uma checagem cobre o conjunto.
_REDE = (httpx.TransportError,)

# Códigos que o PostgREST devolve quando o problema é infraestrutura, não a
# consulta em si. `PGRST301` é o JWT vencido; os `08*` vêm do próprio Postgres.
_CODIGOS_SEM_CONEXAO = {"08000", "08003", "08006", "57P01", "57P03"}


def executar(consulta: _Consulta) -> Any:
    """`.execute()` com as falhas de infraestrutura traduzidas.

    Todo acesso ao banco passa por aqui em vez de chamar `.execute()` direto,
    para que uma queda de rede vire `ErroDeConexao` num ponto só, em vez de
    um traceback do httpx no meio da tela.
    """
    try:
        return consulta.execute()
    except _REDE as exc:
        raise ErroDeConexao(str(exc)) from exc
    except APIError as exc:
        codigo = (exc.code or "").upper()
        mensagem = (exc.message or "").lower()
        if codigo == "PGRST301" or "jwt expired" in mensagem:
            raise SessaoExpirada(exc.message or "") from exc
        if codigo in _CODIGOS_SEM_CONEXAO:
            raise ErroDeConexao(exc.message or "") from exc
        raise
