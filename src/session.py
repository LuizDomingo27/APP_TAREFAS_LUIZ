"""Persistência da sessão entre recarregamentos da página.

O `st.session_state` vive na memória do servidor e é indexado pela conexão
websocket. Um F5 abre uma conexão nova, então a sessão se perde e o usuário
cai na tela de login. A saída é guardar o *refresh token* do Supabase num
cookie e trocá-lo por uma sessão nova a cada carregamento.

O cookie é de *sessão do navegador* (sem `max-age`): ele atravessa o F5 e o
restart do servidor, mas some quando a pessoa fecha o navegador. O escopo
combinado com a equipe é esse — nada de conta aberta no dia seguinte.

Streamlit lê cookies (`st.context.cookies`) mas não escreve — o cookie vem
do handshake do websocket, que já aconteceu. Para escrever, um componente
HTML de altura zero roda `document.cookie` no navegador. O iframe de
componente do Streamlit tem `allow-same-origin` no sandbox, então o cookie
vale para o domínio inteiro e volta no próximo handshake.

Escrita e leitura ficam, portanto, defasadas de um carregamento: o cookie
gravado agora só aparece em `st.context.cookies` depois de recarregar. Isso
não atrapalha, porque quem acabou de logar já tem a sessão em memória.

Risco aceito: o cookie é legível por JavaScript, porque é JavaScript que o
escreve. Um XSS no app levaria o refresh token junto — o mesmo perfil de
risco do SDK JS do Supabase, que guarda a sessão em localStorage por padrão.
Em troca, `HttpOnly` exigiria um servidor próprio na frente do Streamlit.
"""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

COOKIE = "tk_refresh"

# Chave do que está esperando para ser gravado. Guardar em session_state em
# vez de escrever na hora é essencial: quem chama `salvar()` normalmente
# dispara `st.rerun()` logo depois, e o componente não chegaria a renderizar.
_PENDENTE = "_cookie_pendente"


def ler() -> str | None:
    """Refresh token do carregamento atual da página, se houver."""
    try:
        valor = st.context.cookies.get(COOKIE)
    except Exception:
        # st.context.cookies pode não existir em versões antigas do Streamlit.
        return None
    return valor or None


def salvar(refresh_token: str) -> None:
    st.session_state[_PENDENTE] = refresh_token


def limpar() -> None:
    st.session_state[_PENDENTE] = None


def sincronizar() -> None:
    """Aplica no navegador a gravação/remoção agendada.

    Precisa ser chamada em todo carregamento, e ANTES de qualquer `st.stop()`
    — senão o logout agendaria a remoção e nunca a executaria, deixando o
    cookie vivo depois de sair.
    """
    if _PENDENTE not in st.session_state:
        return

    token = st.session_state.pop(_PENDENTE)
    valor = json.dumps(token or "")  # escapa aspas e quebras

    # Cookie de sessão: sem `max-age` nem `expires`, o navegador o descarta
    # quando fecha. Sobrevive ao F5 e ao restart do servidor — que é o que o
    # Streamlit exige — mas não deixa a conta aberta na máquina depois que a
    # pessoa termina o dia. Para apagar, aí sim `max-age=0`.
    validade = "; max-age=0" if not token else ""

    components.html(
        f"""
        <script>
          const seguro = location.protocol === 'https:' ? '; Secure' : '';
          document.cookie = "{COOKIE}=" + encodeURIComponent({valor})
            + "; path=/{validade}; SameSite=Lax" + seguro;
        </script>
        """,
        height=0,
    )
