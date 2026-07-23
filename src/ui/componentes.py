"""Pedaços de HTML reaproveitados entre o Quadro e a Lista.

Tudo aqui devolve string para ser injetado com `unsafe_allow_html=True`.
Como os dados vêm do banco (título, tag, nome digitado por outra pessoa),
todo texto passa por `esc` antes de entrar no HTML.
"""

from __future__ import annotations

from datetime import date, datetime
from html import escape

# Cores dos pontos das colunas do Kanban — mesmas do protótipo.
CORES_STATUS = {
    "A Fazer": ("#94a3b8", "#e2e8f0", "#334155"),      # ponto, fundo, texto
    "Em Progresso": ("#3b82f6", "#dbeafe", "#1d4ed8"),
    "Em Revisão": ("#f59e0b", "#fef3c7", "#b45309"),
    "Concluído": ("#10b981", "#d1fae5", "#047857"),
}

STATUS_ORDEM = ["A Fazer", "Em Progresso", "Em Revisão", "Concluído"]

CLASSES_PRIORIDADE = {
    "Urgente": "urgente",
    "Alta": "alta",
    "Normal": "normal",
    "Baixa": "baixa",
}


def esc(valor: object) -> str:
    return escape(str(valor or ""))


def limpar(html: str) -> str:
    """Achata o HTML em uma linha só.

    `st.markdown` roda o texto pelo parser de markdown antes de soltar o HTML.
    Linha indentada com 4+ espaços vira bloco de código, e aí o card aparece
    como fonte crua na tela. Achatar remove a categoria inteira do problema —
    todas as quebras de linha destes templates ficam entre tags, então juntar
    sem separador não gruda palavra nenhuma.
    """
    return "".join(linha.strip() for linha in html.splitlines())


# Traçados do Lucide (viewBox 24), os mesmos ícones que o protótipo usa.
# Emoji não serve aqui: 🗓 e ☑ caem em tofu no Windows, e mesmo quando
# renderizam vêm coloridos, destoando do traço fino do resto da tela.
_TRACADOS = {
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/>'
                '<path d="M16 2v4M8 2v4M3 10h18"/>',
    "check-square": '<path d="M21 10.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'
                    '<path d="m9 11 3 3L22 4"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "bug": '<path d="M8 2v3M16 2v3M9 20a6 6 0 0 1-3-5v-4a6 6 0 0 1 12 0v4a6 6 0 0 1-3 5"/>'
           '<path d="M12 9v11M3 12h3M18 12h3M4 7l3 2M20 7l-3 2M4 18l3-2M20 18l-3-2"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    "palette": '<circle cx="13.5" cy="6.5" r="1"/><circle cx="17.5" cy="10.5" r="1"/>'
               '<circle cx="6.5" cy="12.5" r="1"/>'
               '<path d="M12 2a10 10 0 0 0 0 20 2 2 0 0 0 2-2v-1a2 2 0 0 1 2-2h2a4 4 0 0 0 4-4 10 10 0 0 0-10-11Z"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
}


def icone(nome: str, tamanho: int = 12) -> str:
    tracado = _TRACADOS.get(nome)
    if not tracado:
        return ""
    return (
        f'<svg width="{tamanho}" height="{tamanho}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" style="vertical-align:-.12em;flex-shrink:0">'
        f"{tracado}</svg>"
    )


def iniciais(nome: str | None) -> str:
    partes = [p for p in (nome or "").split() if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def data_curta(valor: str | None) -> str:
    """'2026-07-28' -> '28/07'. Devolve '—' se não houver data."""
    if not valor:
        return "—"
    try:
        d = date.fromisoformat(str(valor)[:10])
    except ValueError:
        return esc(valor)
    return f"{d.day:02d}/{d.month:02d}"


def data_longa(valor: str | None) -> str:
    if not valor:
        return "—"
    try:
        d = date.fromisoformat(str(valor)[:10])
    except ValueError:
        return esc(valor)
    return d.strftime("%d/%m/%Y")


def atrasada(valor: str | None, status: str) -> bool:
    if not valor or status == "Concluído":
        return False
    try:
        return date.fromisoformat(str(valor)[:10]) < datetime.now().date()
    except ValueError:
        return False


def badge_prioridade(prioridade: str) -> str:
    classe = CLASSES_PRIORIDADE.get(prioridade, "baixa")
    return f'<span class="badge {classe}">{esc(prioridade)}</span>'


def avatar(nome: str | None, mini: bool = False) -> str:
    classe = "avatar mini" if mini else "avatar"
    return (
        f'<span class="{classe}" title="{esc(nome) or "Sem responsável"}">'
        f"{esc(iniciais(nome))}</span>"
    )


def pill_status(status: str) -> str:
    _, fundo, texto = CORES_STATUS.get(status, ("#94a3b8", "#e2e8f0", "#334155"))
    return (
        f'<span class="pill-status" style="background:{fundo};color:{texto}">'
        f"{esc(status)}</span>"
    )
