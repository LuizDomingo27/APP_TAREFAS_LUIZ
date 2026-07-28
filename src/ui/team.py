"""Tela de Equipe — só gestor. Libera acessos sem passar pelo SQL Editor.

O desenho segue o resto do app: painéis brancos sobre o fundo slate, uma
linha por pessoa com avatar à esquerda e as ações à direita. Os widgets são
do Streamlit; o que o HTML desenha é só a identidade (avatar, nome, e-mail,
selo), porque rótulo de botão não aceita marcação.
"""

from __future__ import annotations

import streamlit as st
from postgrest.exceptions import APIError

from src.models import PAPEIS, ROTULO_PAPEL, Perfil
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


def _aplicar(escrita, sucesso: str) -> None:
    """Roda a escrita e trata as recusas possíveis, que são três coisas
    diferentes e mereciam mensagens diferentes.

    `AcaoBloqueada` é regra nossa, e já vem com a explicação pronta. O
    `APIError` traz as travas equivalentes do banco (`sql/07_admin.sql`),
    cuja mensagem também é escrita para ser lida. Já `False` é o RLS
    recusando em silêncio — devolve zero linhas, sem erro nenhum.
    """
    try:
        ok = escrita()
    except catalog.AcaoBloqueada as exc:
        st.error(str(exc))
        return
    except APIError as exc:
        if (exc.code or "").upper() == "PGRST204":
            # Coluna que o banco ainda não tem: falta aplicar a migração.
            st.error(
                "O banco ainda não conhece o papel de administrador. Rode "
                "`sql/07_admin.sql` no SQL Editor do Supabase e tente de novo."
            )
        else:
            st.error(exc.message or str(exc))
        return
    if not ok:
        _falhou()
        return
    st.toast(sucesso)
    st.rerun()


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


def _identidade(p: Perfil, marca: str = "", papel: str | None = None) -> str:
    """Avatar + nome + e-mail. Os selos entram na mesma linha do nome."""
    selos = ""
    if marca:
        selos += f'<span class="selo-voce">{esc(marca)}</span>'
    if papel and papel != "membro":
        selos += f'<span class="selo-gestor">{esc(ROTULO_PAPEL[papel].lower())}</span>'
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
                    _aplicar(lambda p=p: catalog.liberar(p.id), f"{p.nome} liberado.")

                if c_rec.button(
                    "Recusar", key=f"rec_{p.id}", use_container_width=True
                ):
                    _aplicar(lambda p=p: catalog.recusar(p.id), f"{p.nome} recusado.")


def _secao_equipe(eu: Perfil) -> None:
    lista = catalog.equipe()
    outros_gerentes = [p for p in lista if p.pode_gerenciar and p.id != eu.id]

    with st.container(key="painel_equipe"):
        _topo("Equipe ativa", len(lista), "Quem pode entrar e mexer nas tarefas.")

        for p in lista:
            with st.container(key=f"linha_{p.id}"):
                c_nome, c_papel, c_acao = st.columns(
                    [6, 2, 1.6], vertical_alignment="center"
                )
                sou_eu = p.id == eu.id
                c_nome.markdown(
                    _identidade(p, marca="você" if sou_eu else "", papel=p.papel),
                    unsafe_allow_html=True,
                )

                # Ninguém mexe na própria linha. A trava antiga só valia para
                # o *último* gestor, então bastava existir um segundo para
                # você conseguir se desativar — e foi assim que o workspace
                # ficou sem nenhum usuário, sem caminho de volta pelo app.
                # Rebaixar e desativar você mesmo é sempre pedido a outro
                # gestor; a mesma regra está repetida no `catalog`, que é
                # quem realmente barra.
                aviso_proprio = (
                    "Você não pode alterar o próprio acesso. Peça a outro "
                    "gestor ou administrador."
                    if sou_eu
                    else None
                )
                # Já o último gerente do workspace não pode ser rebaixado nem
                # desativado por ninguém — nem por outro gestor, se ele for o
                # único que sobrou depois desta mudança.
                ultimo_gerente = p.pode_gerenciar and not outros_gerentes and not sou_eu
                if ultimo_gerente:
                    aviso_proprio = (
                        f"{p.nome} é quem sobrou com acesso de gestão. "
                        "Promova outra pessoa antes."
                    )
                travado = sou_eu or ultimo_gerente

                novo = c_papel.selectbox(
                    "Acesso",
                    PAPEIS,
                    index=PAPEIS.index(p.papel),
                    format_func=lambda x: ROTULO_PAPEL[x],
                    key=f"papel_{p.id}",
                    disabled=travado,
                    label_visibility="collapsed",
                    help=aviso_proprio or "Gestor e Admin têm os mesmos poderes.",
                )
                if novo != p.papel:
                    _aplicar(
                        lambda p=p, novo=novo: catalog.definir_papel(p.id, novo),
                        f"{p.nome}: {ROTULO_PAPEL[novo]}.",
                    )

                if c_acao.button(
                    "Desativar",
                    key=f"des_{p.id}",
                    use_container_width=True,
                    disabled=travado,
                    help=aviso_proprio,
                ):
                    _aplicar(
                        lambda p=p: catalog.recusar(p.id), f"{p.nome} desativado."
                    )


def _secao_convites() -> None:
    with st.container(key="painel_convites"):
        _topo(
            "Pré-autorizar e-mail",
            sub="Opcional. Quem estiver nesta lista já entra liberado ao se "
                "cadastrar, sem esperar aprovação.",
        )

        with st.form("convite", clear_on_submit=True, border=False):
            c1, c2, c3, c4 = st.columns([4, 3, 2, 1.6], vertical_alignment="bottom")
            email = c1.text_input("E-mail", placeholder="pessoa@empresa.com")
            nome = c2.text_input("Nome (opcional)", placeholder="Opcional")
            papel = c3.selectbox(
                "Acesso",
                PAPEIS,
                format_func=lambda x: ROTULO_PAPEL[x],
                help="Gestor e Admin têm os mesmos poderes.",
            )
            enviou = c4.form_submit_button(
                "Adicionar", type="primary", use_container_width=True
            )
            if enviou:
                if not email.strip():
                    st.warning("Informe o e-mail.")
                else:
                    _aplicar(
                        lambda: catalog.convidar(email, nome, papel),
                        f"{email.strip().lower()} pré-autorizado como "
                        f"{ROTULO_PAPEL[papel]}.",
                    )

        convites = catalog.listar_convites()
        if not convites:
            return

        for c in convites:
            with st.container(key=f"conv_linha_{c['email']}"):
                col_a, col_b = st.columns([8, 1.6], vertical_alignment="center")
                rotulo = "admin" if c.get("admin") else "gestor" if c.get("gestor") else ""
                selo = f'<span class="selo-gestor">{rotulo}</span>' if rotulo else ""
                col_a.markdown(
                    f'<div class="convite-linha"><span class="convite-email">'
                    f'{esc(c["email"])}</span>{selo}</div>',
                    unsafe_allow_html=True,
                )
                if col_b.button(
                    "Remover", key=f"conv_{c['email']}", use_container_width=True
                ):
                    _aplicar(
                        lambda c=c: catalog.remover_convite(c["email"]),
                        "Convite removido.",
                    )


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
                    _aplicar(lambda p=p: catalog.liberar(p.id), f"{p.nome} reativado.")


# -------------------------------------------------------------------- view


def render(eu: Perfil) -> None:
    # `pode_gerenciar`, não `gestor`: admin tem o mesmo poder, e a sidebar já
    # oferecia esta tela por `pode_gerenciar` — quem entrasse como admin batia
    # neste aviso e ficava sem entender por quê.
    if not eu.pode_gerenciar:
        st.warning("Esta tela é só para gestores e administradores.")
        return

    # Tudo dentro de um container com `key`: é ele que o CSS estreita para
    # 80% (`.st-key-pagina_usuarios`). Esta tela é formulário de administração,
    # não painel de dados — na largura toda cada linha virava uma travessia de
    # ponta a ponta com o avatar de um lado e o botão do outro.
    with st.container(key="pagina_usuarios"):
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
