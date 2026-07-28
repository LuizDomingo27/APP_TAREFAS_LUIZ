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


# Os três níveis de acesso. `admin` e `gestor` têm exatamente os mesmos
# poderes — a diferença é só de nomenclatura, para a equipe distinguir quem
# administra o sistema de quem coordena o trabalho. Quem decide o que a
# pessoa pode fazer é sempre `Perfil.pode_gerenciar`, nunca o rótulo.
PAPEIS = ("membro", "gestor", "admin")

ROTULO_PAPEL = {"membro": "Membro", "gestor": "Gestor", "admin": "Admin"}


@dataclass
class Perfil:
    id: str
    email: str | None
    nome: str
    cargo: str | None
    gestor: bool
    ativo: bool
    admin: bool = False
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
            # `.get` com default: banco que ainda não rodou o 07_admin.sql
            # não devolve a coluna, e aí todo mundo é simplesmente não-admin.
            admin=bool(linha.get("admin")),
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
    def papel(self) -> str:
        """Um dos valores de `PAPEIS`. É o que a tela de Equipe edita."""
        if self.admin:
            return "admin"
        if self.gestor:
            return "gestor"
        return "membro"

    @property
    def pode_gerenciar(self) -> bool:
        """True para gestor e admin — os dois níveis com poder de gestão.

        O ramo do `cargo` é compatibilidade: antes de existir a coluna
        `admin`, quem administrava era marcado escrevendo "admin" no cargo,
        que é texto livre. Continua valendo para não tirar o acesso de quem
        já estava assim, mas cadastro novo usa o papel.
        """
        if self.gestor or self.admin:
            return True
        if self.cargo and self.cargo.lower().strip() in ("admin", "administrador"):
            return True
        return False

