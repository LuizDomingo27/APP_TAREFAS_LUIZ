"""Regras de prazo, atraso e tempo de ciclo das tarefas.

Módulo puro de propósito: não importa Streamlit nem toca no banco. Quem
calcula prazo é aqui, e só aqui — o dashboard consome. Isso mantém a regra
num lugar só (o painel tinha a própria cópia, que divergiu) e deixa tudo
testável sem subir a aplicação.

Dois cuidados que existem por causa de bugs reais de contagem:

1. **A data da entrega é `concluido_em`, não `atualizado_em`.**
   `atualizado_em` é carimbado pelo trigger `tasks_touch` a *cada* update —
   trocar uma tag, corrigir o título ou mudar o responsável empurra a data
   para frente. Uma tarefa entregue no prazo e editada uma semana depois
   passava a se declarar "Concluído com 7 dia(s) de atraso". `concluido_em`
   (ver `sql/06_concluido_em.sql`) só é carimbado na transição para
   "Concluído", então não anda sozinho. Bancos que ainda não receberam a
   migração caem no `atualizado_em` como antes — pior, mas nunca quebra.

2. **Timestamp do banco é UTC; prazo é calendário local.**
   O Postgres devolve `timestamptz` em UTC (`...T23:30:00+00:00`). Cortar a
   string no "T" pega o dia UTC: quem entregou às 21h de Brasília aparecia
   entregando no dia seguinte, e ganhava "1 dia de atraso" que não existiu.
   Timestamps são convertidos para `FUSO_APP` antes de virarem data.
   `data_limite` é `date` (dia de calendário, sem hora) e por isso **não**
   sofre conversão nenhuma — converter um dia puro é o mesmo bug ao contrário.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import logging

from src.models import Status

logger = logging.getLogger(__name__)

# Fuso em que a equipe enxerga o calendário. Prazo é combinação humana
# ("entrega dia 20"), então a comparação tem que ser no dia local de quem
# combinou, não no dia UTC em que o registro caiu no banco.
FUSO_APP = "America/Sao_Paulo"

# Usado só se a base de fusos do sistema não existir (Windows sem `tzdata`).
# Perde o horário de verão, mas erra no máximo uma hora em vez de derrubar
# o painel inteiro por um `ZoneInfoNotFoundError` no import.
_FUSO_RESERVA = timezone(timedelta(hours=-3), "UTC-03")


def _resolver_fuso():
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(FUSO_APP)
    except Exception as exc:  # ZoneInfoNotFoundError, ImportError
        logger.warning(
            "Fuso '%s' indisponível (%s). Usando UTC-03 fixo — instale o "
            "pacote `tzdata` para ter horário de verão correto.",
            FUSO_APP,
            exc,
        )
        return _FUSO_RESERVA


FUSO = _resolver_fuso()

# Rótulos das situações. Ficam aqui para o teste conferir contra a constante
# em vez de repetir a string e passar mesmo com o texto trocado.
SEM_PRAZO = "Sem data limite"
CONCLUIDO_SEM_PRAZO = "Concluído (sem prazo definido)"
CONCLUIDO_NO_PRAZO = "Concluído no prazo"
VENCE_HOJE = "Vence hoje!"

# Quantos dias antes do vencimento a tarefa já entra em alerta amarelo.
JANELA_ALERTA = 3


def hoje() -> date:
    """Data de hoje no fuso da equipe (não no fuso do servidor)."""
    return datetime.now(FUSO).date()


def para_data(valor: str | date | datetime | None) -> date | None:
    """Converte o que vier do banco em `date` no calendário local.

    Regra central: valor **com hora** é instante no tempo e é convertido para
    `FUSO_APP` antes de virar dia; valor **sem hora** (`date`, `'2026-07-20'`)
    já é um dia de calendário e passa intacto. Devolve `None` quando não dá
    para interpretar — nunca levanta, porque uma linha estranha não pode
    derrubar o painel de quem só queria ver o gráfico.
    """
    if valor is None or valor == "":
        return None

    if isinstance(valor, datetime):
        return _instante_para_data(valor)

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        return _texto_para_data(valor)

    logger.debug("Valor de data em tipo inesperado (%s): %r", type(valor).__name__, valor)
    return None


def _instante_para_data(momento: datetime) -> date:
    """Datetime -> dia local. Naive é tratado como UTC (é o que o banco grava)."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(FUSO).date()


def _texto_para_data(texto: str) -> date | None:
    limpo = texto.strip()
    if not limpo:
        return None

    # Só dia, sem hora: é calendário puro, não converte fuso.
    if len(limpo) == 10 and "T" not in limpo and " " not in limpo:
        try:
            return date.fromisoformat(limpo)
        except ValueError:
            logger.debug("Data ISO inválida: %r", texto)
            return None

    try:
        # O Postgres pode mandar 'Z' no lugar do offset; o fromisoformat do
        # 3.11+ aceita, mas normalizar sai mais barato que depender da versão.
        return _instante_para_data(datetime.fromisoformat(limpo.replace("Z", "+00:00")))
    except ValueError:
        pass

    # Última tentativa: cabeçalho ISO em formato que o parser recusou
    # (offset exótico, microssegundos demais). O dia ainda é aproveitável.
    try:
        return date.fromisoformat(limpo[:10])
    except ValueError:
        logger.debug("Não foi possível interpretar a data: %r", texto)
        return None


def esta_concluida(task: dict) -> bool:
    return (task.get("status") or "") == Status.CONCLUIDO.value


def data_conclusao(task: dict) -> date | None:
    """Dia em que a tarefa foi realmente entregue.

    `concluido_em` primeiro; `atualizado_em` só como reserva, para bancos que
    ainda não rodaram `sql/06_concluido_em.sql`. Devolve `None` se a tarefa
    não está concluída — perguntar a data de entrega de algo não entregue é
    erro de quem chama, e um `None` explícito revela isso melhor que um dia
    inventado.
    """
    if not esta_concluida(task):
        return None
    return para_data(task.get("concluido_em")) or para_data(task.get("atualizado_em"))


def calcular_dias_em_andamento(task: dict, referencia: date | None = None) -> int:
    """Dias entre a criação e a entrega (ou hoje, se ainda está aberta)."""
    ref = referencia or hoje()

    inicio = para_data(task.get("criado_em"))
    if inicio is None:
        logger.debug("Tarefa %s sem `criado_em` legível.", task.get("id"))
        return 0

    fim = (data_conclusao(task) or ref) if esta_concluida(task) else ref

    dias = (fim - inicio).days
    if dias < 0:
        # Entrega antes da criação só acontece com dado inconsistente; o
        # painel mostra 0 em vez de um número negativo sem sentido.
        logger.debug(
            "Tarefa %s com fim (%s) anterior à criação (%s).", task.get("id"), fim, inicio
        )
        return 0
    return dias


def calcular_prazo(task: dict, referencia: date | None = None) -> dict:
    """Situação do prazo da tarefa.

    Campos devolvidos:

    | Campo | Significado |
    |---|---|
    | `status_prazo` | Frase exibida na coluna "Situação do Prazo" |
    | `badge_class` | Cor do selo (`normal`/`alta`/`urgente`/`concluido`/`alerta`) |
    | `dias_restantes` | Dias até vencer. **`None` em tarefa concluída** |
    | `dias_atraso` | Dias de atraso (`0` = no prazo, `None` = sem prazo) |
    | `dias_adiantamento` | Dias de antecedência na entrega (só concluídas) |
    | `atrasado` | Está **pendente e vencida** agora |
    | `entregue_com_atraso` | Foi entregue depois do prazo (fato histórico) |
    | `data_conclusao` | Dia real da entrega, ou `None` |

    `atrasado` e `entregue_com_atraso` são separados de propósito. Antes um
    campo só acumulava os dois sentidos, e cada consumidor precisava lembrar
    de escrever `and status != "Concluído"` para não contar entrega antiga no
    KPI de atrasadas — três lugares, três chances de esquecer.
    """
    ref = referencia or hoje()
    limite = para_data(task.get("data_limite"))
    concluida = esta_concluida(task)

    base = {
        "dias_restantes": None,
        "dias_atraso": None,
        "dias_adiantamento": None,
        "atrasado": False,
        "entregue_com_atraso": False,
        "data_conclusao": data_conclusao(task) if concluida else None,
    }

    if limite is None:
        return {
            **base,
            "status_prazo": CONCLUIDO_SEM_PRAZO if concluida else SEM_PRAZO,
            "badge_class": "concluido" if concluida else "normal",
        }

    if concluida:
        return {**base, **_prazo_de_concluida(base["data_conclusao"] or ref, limite)}

    return {**base, **_prazo_de_pendente(ref, limite)}


def _prazo_de_concluida(entrega: date, limite: date) -> dict:
    """Compara a entrega real com o prazo. Nada aqui depende de 'hoje'."""
    atraso = (entrega - limite).days

    if atraso > 0:
        return {
            "dias_atraso": atraso,
            "dias_adiantamento": 0,
            "entregue_com_atraso": True,
            "status_prazo": f"Concluído com {atraso} dia(s) de atraso",
            "badge_class": "alerta",
        }

    return {
        "dias_atraso": 0,
        "dias_adiantamento": -atraso,
        "entregue_com_atraso": False,
        "status_prazo": CONCLUIDO_NO_PRAZO,
        "badge_class": "concluido",
    }


def _prazo_de_pendente(ref: date, limite: date) -> dict:
    """Compara o prazo com hoje. Só para tarefa ainda em aberto."""
    dias = (limite - ref).days

    if dias < 0:
        return {
            "dias_restantes": dias,
            "dias_atraso": -dias,
            "atrasado": True,
            "status_prazo": f"Atrasado há {-dias} dia(s)",
            "badge_class": "urgente",
        }

    if dias == 0:
        return {
            "dias_restantes": 0,
            "dias_atraso": 0,
            "status_prazo": VENCE_HOJE,
            "badge_class": "alta",
        }

    if dias <= JANELA_ALERTA:
        return {
            "dias_restantes": dias,
            "dias_atraso": 0,
            "status_prazo": f"Vence em {dias} dia(s)",
            "badge_class": "alta",
        }

    return {
        "dias_restantes": dias,
        "dias_atraso": 0,
        "status_prazo": f"Faltam {dias} dia(s)",
        "badge_class": "normal",
    }


def esta_critica(task: dict) -> bool:
    """Tarefa pendente que já venceu ou vence dentro da janela de alerta.

    Alimenta o painel de alertas. Concluída nunca é crítica — o que passou
    virou histórico, e misturar as duas coisas enche o painel de tarefa que
    já foi entregue.
    """
    if esta_concluida(task):
        return False
    if task.get("atrasado"):
        return True
    restantes = task.get("dias_restantes")
    return restantes is not None and 0 <= restantes <= JANELA_ALERTA
