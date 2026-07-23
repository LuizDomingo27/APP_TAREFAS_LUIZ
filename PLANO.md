# Plano — Gerenciador de Tarefas da Equipe (Streamlit + Supabase)

Baseado em `manager_ui_prototype.html`. Equipe de 5 pessoas, uso diário.

## Decisões fechadas

| Item | Decisão |
|---|---|
| Autenticação | Supabase Auth (e-mail/senha) + RLS no Postgres |
| Autenticação | Cadastro aberto (a pessoa cria a própria senha), acesso liberado por allowlist |
| Escopo v1 | Quadro (Kanban), Lista, Detalhe da tarefa e tela de Equipe |
| Visual | Streamlit + CSS custom aproximando o protótipo |
| Hospedagem | Streamlit Community Cloud |
| Fora da v1 | Calendário, Gantt, Metas/OKRs, notificações |

## Stack

- Python 3.11+, Streamlit
- `supabase-py` (cliente oficial)
- `python-dotenv` para desenvolvimento local
- `st.secrets` no deploy

## Modelo de dados (Supabase / Postgres)

```
profiles          id (=auth.users.id), nome, cargo, avatar_url, ativo
spaces            id, nome, cor, criado_em
lists             id, space_id, nome, icone, ordem
tasks             id, list_id, codigo, titulo, descricao, status,
                  prioridade, responsavel_id, criado_por, data_limite,
                  estimativa_horas, ordem, criado_em, atualizado_em
task_tags         task_id, tag              (N tags por tarefa)
subtasks          id, task_id, titulo, concluida, ordem
comments          id, task_id, autor_id, texto, criado_em
```

Enums no banco (evita string solta):
- `task_status`: `A Fazer` | `Em Progresso` | `Em Revisão` | `Concluído`
- `task_priority`: `Urgente` | `Alta` | `Normal` | `Baixa`

Datas: `data_limite` como `date`, os demais campos de tempo como `timestamptz` (ISO-8601).

`codigo` (ex. `DEV-101`) gerado por sequence por space, para bater com o protótipo.

### RLS — política adotada

Equipe pequena e colaborativa, então: **todo membro autenticado lê tudo; escrita controlada.**

- `SELECT`: qualquer usuário autenticado com perfil ativo
- `INSERT` em `tasks`: qualquer autenticado (grava `criado_por = auth.uid()`)
- `UPDATE` em `tasks`: qualquer autenticado (o histórico fica nos comentários)
- `DELETE` em `tasks`: apenas `criado_por` ou perfil com cargo de gestão
- `comments`: autor só edita/apaga o próprio
- `profiles`: cada um edita só o seu

Isso é o essencial — se vocês quiserem restringir por espaço depois, a política troca sem mexer no app.

## Estrutura de arquivos

```
APP_TASK/
├── app.py                  # entrada, roteamento de views, sessão
├── requirements.txt
├── .env.example
├── .streamlit/
│   ├── config.toml         # tema escuro base
│   └── secrets.toml        # (local, no .gitignore)
├── src/
│   ├── db.py               # cliente Supabase + cache de conexão
│   ├── auth.py             # login, logout, guarda de sessão
│   ├── repo/
│   │   ├── tasks.py        # CRUD de tarefas, subtarefas, comentários
│   │   └── catalog.py      # spaces, lists, profiles
│   ├── ui/
│   │   ├── styles.py       # CSS injetado (paleta ClickUp do protótipo)
│   │   ├── sidebar.py      # workspace, espaços/listas, perfil
│   │   ├── board.py        # Kanban
│   │   ├── list_view.py    # tabela
│   │   ├── task_detail.py  # painel de detalhe + subtarefas + comentários
│   │   └── team.py         # tela de Equipe (só gestor): liberar acessos
│   └── models.py           # dataclasses/enums espelhando o banco
├── sql/
│   ├── 01_schema.sql
│   ├── 02_rls.sql
│   └── 03_seed.sql
└── PLANO.md
```

## Como cada tela do protótipo vira Streamlit

**Sidebar** — `st.sidebar` com CSS. Botão "Criar Tarefa", navegação, árvore de espaços via `st.expander`, rodapé com perfil e logout.

**Barra de views** — `st.tabs` ou `st.segmented_control` para Quadro/Lista. Busca em `st.text_input`, filtro de prioridade e responsável em `st.selectbox`.

**Kanban** — 4 `st.columns`. Cada card é um bloco HTML estilizado (código, badge de prioridade, título, tag, contador de subtarefas, data, avatar) com um `st.button` discreto para abrir o detalhe.
*Ponto de atenção:* Streamlit não tem drag-and-drop nativo. Em vez de arrastar, cada card ganha um `selectbox` de status inline — muda a coluna na hora. Funciona bem e é mais rápido que arrastar no dia a dia.

**Lista** — `st.dataframe` com colunas configuradas (checkbox de concluído, badges) e seleção de linha abrindo o detalhe.

**Detalhe** — o protótipo usa um drawer lateral. Em Streamlit, `st.dialog` (modal) é o equivalente mais próximo e nativo. Contém título editável, atributos, descrição, subtarefas com checkbox, comentários e os botões Salvar/Excluir.

**Equipe** — tela que não existe no protótipo, aparece na sidebar só para gestor. Duas seções:
- *Pendentes* — quem se cadastrou e ainda não foi liberado. Cada linha com nome, e-mail, data e um botão **Liberar** (marca `ativo`) e um **Recusar** (mantém inativo e remove da lista de pendentes).
- *Equipe* — quem já tem acesso, com toggle de ativo e de gestor, e um campo para pré-autorizar um e-mail antes mesmo da pessoa se cadastrar (grava em `allowed_emails`).

Com isso o `03_seed.sql` deixa de ser o caminho normal para liberar alguém — vira só o bootstrap do primeiro gestor.

**Toast** — `st.toast`, direto.

**Dark mode** — configurado em `.streamlit/config.toml` com a paleta do protótipo (`#7b68ee`, `#0f172a`, `#1e293b`). Tema fixo escuro na v1; alternância clara/escura é ajuste de fase 2.

## Fases de execução

**Fase 1 — Fundação**
Projeto Supabase criado, `01_schema.sql` e `02_rls.sql` aplicados, seed com os 5 usuários e os espaços. Esqueleto Streamlit rodando com login funcionando e sessão persistida.
*Entrega:* consigo logar e ver meu nome no rodapé da sidebar.

**Fase 2 — Leitura**
Sidebar com espaços/listas, Kanban e Lista renderizando dados reais do Supabase, com busca e filtros.
*Entrega:* o quadro mostra as tarefas reais da equipe.

**Fase 3 — Escrita**
Criar tarefa (modal), editar pelo detalhe, mudar status pelo card, excluir. Subtarefas e comentários.
*Entrega:* o app substitui a planilha/quadro atual.

**Fase 4 — Acabamento**
CSS refinado para aproximar do protótipo, estados vazios, tratamento de erro de rede, avatares, contadores por coluna.

**Fase 5 — Deploy**
Repositório no GitHub, secrets no Streamlit Cloud, convite dos 5 usuários, teste com a equipe.

## Riscos e como tratamos

| Risco | Tratamento |
|---|---|
| Sem drag-and-drop no Kanban | `selectbox` de status no card (decidido acima) |
| Streamlit recarrega a página inteira a cada clique | `st.cache_data` com TTL curto nas leituras e invalidação explícita após escrita |
| Chave do Supabase vazar no repositório | Só a chave `anon` no app, protegida por RLS. `service_role` nunca entra no código. `.gitignore` cobrindo `secrets.toml` e `.env` |
| Perda de dados sem backup no free tier | Rotina simples de export para CSV, manual ou agendada |
| Concorrência (dois editam a mesma tarefa) | `atualizado_em` verificado no update; avisa se mudou desde a leitura |

## O que preciso de você para começar

1. Projeto criado no Supabase — me passe a **URL** e a chave **anon** (nunca a `service_role`).
2. Nome e e-mail das 5 pessoas da equipe.
3. Os espaços e listas reais de vocês (o protótipo usa "Engenharia & Dev", "Marketing & Vendas", "Design & UI/UX" — quero os verdadeiros).

Com isso rodo a Fase 1 inteira.
