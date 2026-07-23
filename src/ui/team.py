"""Tela de Equipe — só gestor. Libera acessos sem passar pelo SQL Editor.

O desenho segue o resto do app: painéis brancos sobre o fundo slate, uma
linha por pessoa com avatar à esquerda e as ações à direita. Os widgets são
do Streamlit; o que o HTML desenha é só a identidade (avatar, nome, e-mail,
selo), porque rótulo de botão não aceita marcação.
"""

from __future__ import annotations

import streamlit as st

from src.models import Perfil
from src.repo import catalog
from src.ui.componentes import avatar, esc, limpar


def _data_curta(iso: str | None) -> str:
    if not iso:
        return "—"
    a, m, d = str(iso)[:10].split("-")
    return f"{d}/{m}/{a}"


def _falhou() -> None:
    st.error(
        "O banco recusou a alteração. Isso acontece quando o seu perfil não "
        "está mais como gestor — recarregue a página e tente de novo."
    )


# ----------------------------------------------------------------- pedaços


def _topo(titulo: str, contagem: int | None = None, sub: str | None = None) -> None:
    selo = (
        f'<span class="contador-simples">{contagem}</span>'
        if contagem is not None
        else ""
    )
    legenda = f'<p class="painel-sub">{esc(sub)}</p>' if sub else ""
    st.markdown(
        limpar(f"""
        <div class="painel-topo">
          <h3>{esc(titulo)}</h3>{selo}
        </div>
        {legenda}
        """),
        unsafe_allow_html=True,
    )


def _identidade(p: Perfil, marca: str = "", selo_gestor: bool = False) -> str:
    """Avatar + nome + e-mail. Os selos entram na mesma linha do nome."""
    selos = ""
    if marca:
        selos += f'<span class="selo-voce">{esc(marca)}</span>'
    if selo_gestor:
        selos += '<span class="selo-gestor">gestor</span>'
    return limpar(f"""
    <div class="pessoa">
      {avatar(p.nome)}
      <div class="pessoa-texto">
        <div class="pessoa-nome">{esc(p.nome)}{selos}</div>
        <div class="pessoa-email">{esc(p.email) or "—"}</div>
      </div>
    </div>
    """)


# ------------------------------------------------------------------ seções


def _secao_pendentes() -> None:
    lista = catalog.pendentes()

    with st.container(key="painel_pendentes"):
        _topo("Aguardando liberação", len(lista))

        if not lista:
            st.markdown(
                '<div class="vazio">Ninguém na fila. Novos cadastros aparecem aqui.</div>',
                unsafe_allow_html=True,
            )
            return

        for p in lista:
            with st.container(key=f"linha_{p.id}"):
                c_nome, c_data, c_lib, c_rec = st.columns(
                    [5, 2, 1.6, 1.6], vertical_alignment="center"
                )
                c_nome.markdown(_identidade(p), unsafe_allow_html=True)
                c_data.markdown(
                    f'<span class="pessoa-quando">desde {_data_curta(p.criado_em)}</span>',
                    unsafe_allow_html=True,
                )

                if c_lib.button(
                    "Liberar", key=f"lib_{p.id}", type="primary",
                    use_container_width=True,
                ):
                    if catalog.liberar(p.id):
                        st.toast(f"{p.nome} liberado.", icon="✅")
                        st.rerun()
                    else:
                        _falhou()

                if c_rec.button(
                    "Recusar", key=f"rec_{p.id}", use_container_width=True
                ):
                    if catalog.recusar(p.id):
                        st.toast(f"{p.nome} recusado.", icon="🚫")
                        st.rerun()
                    else:
                        _falhou()


def _secao_equipe(eu: Perfil) -> None:
    lista = catalog.equipe()
    outros_gestores = [p for p in lista if p.gestor and p.id != eu.id]

    with st.container(key="painel_equipe"):
        _topo("Equipe ativa", len(lista), "Quem pode entrar e mexer nas tarefas.")

        for p in lista:
            with st.container(key=f"linha_{p.id}"):
                c_nome, c_gestor, c_acao = st.columns(
                    [6, 2, 1.6], vertical_alignment="center"
                )
                c_nome.markdown(
                    _identidade(p, marca="você" if p.id == eu.id else "",
                                selo_gestor=p.gestor),
                    unsafe_allow_html=True,
                )

                # Sem esta trava, o único gestor consegue se rebaixar e o
                # workspace fica sem ninguém que possa liberar acessos — só o
                # SQL Editor sairia dessa, que é exatamente o que esta tela
                # existe para evitar.
                ultimo_gestor = p.gestor and p.id == eu.id and not outros_gestores

                novo = c_gestor.toggle(
                    "Gestor",
                    value=p.gestor,
                    key=f"gestor_{p.id}",
                    disabled=ultimo_gestor,
                    help="Você é o único gestor — promova outra pessoa antes de sair."
                    if ultimo_gestor
                    else None,
                )
                if novo != p.gestor:
                    if catalog.definir_gestor(p.id, novo):
                        st.toast(
                            f"{p.nome}: {'agora é gestor' if novo else 'não é mais gestor'}."
                        )
                        st.rerun()
                    else:
                        _falhou()

                if c_acao.button(
                    "Desativar",
                    key=f"des_{p.id}",
                    use_container_width=True,
                    disabled=ultimo_gestor,
                ):
                    if catalog.recusar(p.id):
                        st.toast(f"{p.nome} desativado.")
                        st.rerun()
                    else:
                        _falhou()


def _secao_convites() -> None:
    with st.container(key="painel_convites"):
        _topo(
            "Pré-autorizar e-mail",
            sub="Opcional. Quem estiver nesta lista já entra liberado ao se "
                "cadastrar, sem esperar aprovação.",
        )

        with st.form("convite", clear_on_submit=True, border=False):
            c1, c2, c3, c4 = st.columns([4, 3, 1.6, 1.6], vertical_alignment="bottom")
            email = c1.text_input("E-mail", placeholder="pessoa@empresa.com")
            nome = c2.text_input("Nome (opcional)", placeholder="Opcional")
            gestor = c3.checkbox("Gestor")
            enviou = c4.form_submit_button(
                "Adicionar", type="primary", use_container_width=True
            )
            if enviou:
                if not email.strip():
                    st.warning("Informe o e-mail.")
                elif catalog.convidar(email, nome, gestor):
                    st.toast(f"{email.strip().lower()} pré-autorizado.", icon="✉️")
                    st.rerun()
                else:
                    _falhou()

        convites = catalog.listar_convites()
        if not convites:
            return

        for c in convites:
            with st.container(key=f"conv_linha_{c['email']}"):
                col_a, col_b = st.columns([8, 1.6], vertical_alignment="center")
                selo = '<span class="selo-gestor">gestor</span>' if c.get("gestor") else ""
                col_a.markdown(
                    f'<div class="convite-linha"><span class="convite-email">'
                    f'{esc(c["email"])}</span>{selo}</div>',
                    unsafe_allow_html=True,
                )
                if col_b.button(
                    "Remover", key=f"conv_{c['email']}", use_container_width=True
                ):
                    if catalog.remover_convite(c["email"]):
                        st.toast("Convite removido.")
                        st.rerun()
                    else:
                        _falhou()


def _secao_recusados() -> None:
    lista = catalog.recusados()
    if not lista:
        return
    with st.expander(f"Recusados e desativados ({len(lista)})"):
        for p in lista:
            with st.container(key=f"linha_{p.id}"):
                col_a, col_b = st.columns([8, 1.6], vertical_alignment="center")
                col_a.markdown(_identidade(p), unsafe_allow_html=True)
                if col_b.button(
                    "Reativar", key=f"reat_{p.id}", use_container_width=True
                ):
                    if catalog.liberar(p.id):
                        st.toast(f"{p.nome} reativado.", icon="✅")
                        st.rerun()
                    else:
                        _falhou()


# -------------------------------------------------------------------- view


def render(eu: Perfil) -> None:
    if not eu.gestor:
        st.warning("Esta tela é só para gestores.")
        return

    st.markdown(
        limpar("""
        <div class="topbar">
          <div class="migalhas"><span class="atual">Equipe</span></div>
        </div>
        """),
        unsafe_allow_html=True,
    )
    _secao_pendentes()
    _secao_equipe(eu)
    _secao_convites()
    _secao_recusados()
