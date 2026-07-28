"""Enums e dataclasses espelhando o schema do Postgres."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    A_FAZER = "A Fazer"
    EM_PROGRESSO = "Em Progresso"
    EM_REVISAO = "Em Revisão"
    CONCLUIDO = "Concluído"


class Prioridade(str, Enum):
    URGENTE = "Urgente"
    ALTA = "Alta"
    NORMAL = "Normal"
    BAIXA = "Baixa"


CORES_PRIORIDADE = {
    Prioridade.URGENTE: "#ef4444",
    Prioridade.ALTA: "#f59e0b",
    Prioridade.NORMAL: "#3b82f6",
    Prioridade.BAIXA: "#64748b",
}


@dataclass
class Perfil:
    id: str
    email: str | None
    nome: str
    cargo: str | None
    gestor: bool
    ativo: bool
    recusado: bool = False
    avatar_url: str | None = None
    criado_em: str | None = None

    @classmethod
    def de_linha(cls, linha: dict) -> "Perfil":
        return cls(
            id=linha["id"],
            email=linha.get("email"),
            nome=linha.get("nome") or "(sem nome)",
            cargo=linha.get("cargo"),
            gestor=bool(linha.get("gestor")),
            ativo=bool(linha.get("ativo")),
            recusado=bool(linha.get("recusado")),
            avatar_url=linha.get("avatar_url"),
            criado_em=linha.get("criado_em"),
        )

    @property
    def iniciais(self) -> str:
        partes = [p for p in self.nome.split() if p]
        if not partes:
            return "?"
        if len(partes) == 1:
            return partes[0][:2].upper()
        return (partes[0][0] + partes[-1][0]).upper()

    @property
    def pode_gerenciar(self) -> bool:
        """Retorna True se o usuário for gestor ou possuir cargo/permissão de admin."""
        if self.gestor:
            return True
        if self.cargo and self.cargo.lower().strip() in ("admin", "administrador"):
            return True
        return False

