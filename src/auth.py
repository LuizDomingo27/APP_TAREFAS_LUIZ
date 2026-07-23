"""Registro, login, logout e guarda de sessão."""

from __future__ import annotations

import httpx
import streamlit as st

from src import session
from src.db import executar, get_client
from src.models import Perfil
from src.ui.componentes import limpar


# --------------------------------------------------------------------- estado


def perfil_atual() -> Perfil | None:
    return st.session_state.get("perfil")


def carregar_perfil(user_id: str) -> Perfil | None:
    """Lê o profile criado pelo trigger tk_handle_new_user."""
    sb = get_client()
    resp = executar(sb.table("profiles").select("*").eq("id", user_id).limit(1))
    if not resp.data:
        return None
    return Perfil.de_linha(resp.data[0])


def logout() -> None:
    try:
        get_client().auth.sign_out()
    except Exception:
        # Token já expirado no servidor: o que importa é limpar o lado do app.
        pass
    for chave in ("sb_client", "perfil", "user_id"):
        st.session_state.pop(chave, None)
    session.limpar()
    st.rerun()


def _guardar_sessao(resp) -> None:
    """Grava sessão em memória e agenda o cookie do refresh token."""
    st.session_state.user_id = resp.user.id
    st.session_state.perfil = carregar_perfil(resp.user.id)
    if resp.session and resp.session.refresh_token:
        session.salvar(resp.session.refresh_token)


def restaurar_sessao() -> Perfil | None:
    """Troca o cookie por uma sessão nova. Devolve None se não der."""
    token = session.ler()
    if not token:
        return None

    try:
        resp = get_client().auth.refresh_session(token)
    except Exception:
        # Token expirado, revogado ou já usado. Descarta e cai no login.
        session.limpar()
        return None

    if not resp or not resp.session or not resp.user:
        session.limpar()
        return None

    # O Supabase rotaciona o refresh token a cada uso: sem regravar o novo,
    # o cookie viraria lixo e o F5 seguinte cairia no login.
    _guardar_sessao(resp)
    return st.session_state.get("perfil")


# ------------------------------------------------------------------- telas


def _mensagem_erro(exc: Exception) -> str:
    bruto = str(exc).lower()
    if isinstance(exc, httpx.TransportError):
        return (
            "Não consegui falar com o servidor. Verifique sua conexão e "
            "tente de novo."
        )
    if "invalid login credentials" in bruto:
        return "E-mail ou senha incorretos."
    if "email not confirmed" in bruto:
        return (
            "Este e-mail ainda não foi confirmado. Confirme pelo link enviado, "
            "ou desative *Confirm email* em Authentication → Providers → Email "
            "no painel do Supabase."
        )
    if "user already registered" in bruto or "already been registered" in bruto:
        return "Já existe uma conta com este e-mail. Use a aba Entrar."
    if "password should be at least" in bruto:
        return "A senha precisa ter pelo menos 6 caracteres."
    return f"Não foi possível concluir: {exc}"


def _form_login() -> None:
    with st.form("login"):
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")
        enviou = st.form_submit_button(
            "Entrar", use_container_width=True, type="primary"
        )

    if not enviou:
        return
    if not email or not senha:
        st.warning("Preencha e-mail e senha.")
        return

    try:
        resp = get_client().auth.sign_in_with_password(
            {"email": email.strip(), "password": senha}
        )
    except Exception as exc:
        st.error(_mensagem_erro(exc))
        return

    _guardar_sessao(resp)
    st.rerun()


def _form_registro() -> None:
    with st.form("registro"):
        nome = st.text_input("Seu nome")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password", help="Mínimo de 6 caracteres.")
        senha2 = st.text_input("Repita a senha", type="password")
        enviou = st.form_submit_button(
            "Criar conta", use_container_width=True, type="primary"
        )

    if not enviou:
        return
    if not (nome and email and senha):
        st.warning("Preencha todos os campos.")
        return
    if senha != senha2:
        st.warning("As duas senhas não conferem.")
        return

    try:
        resp = get_client().auth.sign_up(
            {
                "email": email.strip(),
                "password": senha,
                "options": {"data": {"nome": nome.strip()}},
            }
        )
    except Exception as exc:
        st.error(_mensagem_erro(exc))
        return

    # Com "Confirm email" ligado no Supabase, sign_up devolve user sem session.
    if resp.session is None:
        st.success(
            "Conta criada. Confirme o e-mail pelo link que enviamos e depois "
            "entre pela aba **Entrar**."
        )
        return

    _guardar_sessao(resp)
    st.rerun()


def tela_de_acesso() -> None:
    # Um cartão de 400px centrado, em vez das três colunas de antes: com
    # colunas a largura acompanhava a janela, e numa tela larga o formulário
    # de duas linhas ficava esparramado. A caixa fixa é o que dá ao login
    # cara de tela de produto e não de rascunho. O CSS mora em
    # `.st-key-login_card`.
    with st.container(key="login_card"):
        st.markdown(
            limpar("""
            <div class="login-marca">
              <div class="ws-logo">T</div>
              <div>
                <p class="login-titulo">Tarefas da Equipe</p>
                <p class="login-sub">Acesso liberado por um gestor.</p>
              </div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        aba_entrar, aba_criar = st.tabs(["Entrar", "Criar conta"])
        with aba_entrar:
            _form_login()
        with aba_criar:
            _form_registro()

        st.markdown(
            '<p class="login-rodape">Crie a conta e aguarde a liberação.</p>',
            unsafe_allow_html=True,
        )


def tela_pendente(perfil: Perfil) -> None:
    st.markdown("## Acesso pendente")
    st.info(
        f"Olá, **{perfil.nome}**. Sua conta foi criada, mas ainda precisa ser "
        "liberada por um gestor da equipe. Assim que isso acontecer, é só "
        "recarregar esta página."
    )
    if st.button("Sair"):
        logout()


def exigir_login() -> Perfil:
    """Barra a passagem até existir um perfil ativo. Devolve o perfil."""
    perfil = perfil_atual()

    # Sem sessão em memória: pode ser um F5. Tenta o cookie antes de
    # mandar a pessoa para a tela de login.
    if perfil is None and "user_id" not in st.session_state:
        perfil = restaurar_sessao()

    if perfil is None:
        if "user_id" in st.session_state:
            # Autenticou mas o profile não veio — trigger não rodou ou o
            # 01_schema.sql ainda não foi aplicado.
            st.error(
                "Login feito, mas não encontrei seu perfil. Confirme que os "
                "scripts de `sql/` foram aplicados no Supabase."
            )
            if st.button("Sair"):
                logout()
        else:
            tela_de_acesso()
        st.stop()

    if not perfil.ativo:
        tela_pendente(perfil)
        st.stop()

    _garantir_cookie()
    return perfil


def _garantir_cookie() -> None:
    """Preenche o cookie de quem já estava logado quando o recurso subiu.

    Sem isto, toda sessão aberta antes desta versão continuaria caindo no
    login a cada F5 até a pessoa sair e entrar de novo.
    """
    # `session.ler()` só enxerga o cookie no próximo carregamento da página,
    # então sem esta trava o backfill se repetiria a cada rerun.
    if st.session_state.get("_cookie_backfill"):
        return
    if session.ler() or "_cookie_pendente" in st.session_state:
        return
    try:
        atual = get_client().auth.get_session()
    except Exception:
        return
    if atual and atual.refresh_token:
        session.salvar(atual.refresh_token)
        st.session_state["_cookie_backfill"] = True
