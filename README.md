# 🚀 Gerenciador de Tarefas e Monitoramento de Entregas da Equipe

Aplicativo web completo para gerenciamento de tarefas, projetos, cronogramas temporais e acompanhamento de desempenho por integrante da equipe. Desenvolvido em **Python**, **Streamlit**, **Apache ECharts** (via CDN) e integrado ao **Supabase** (PostgreSQL com RLS e autenticação).

---

## 📋 Sumário
- [Visão Geral](#-visão-geral)
- [Controle de Acesso e Regras de Permissão (RBAC)](#-controle-de-acesso-e-regras-de-permissão-rbac)
- [Design da Tabela de Tarefas (UI/UX Profissional)](#-design-da-tabela-de-tarefas-uiux-profissional)
- [Painel de Indicadores e Gráficos (Apache ECharts)](#-painel-de-indicadores-e-gráficos-apache-echarts)
  - [1. 📅 Cronograma (Gráfico de Gantt Interativo)](#1-📅-cronograma-gráfico-de-gantt-interativo)
  - [2. 👤 Situação e Carga por Usuário](#2-👤-situação-e-carga-por-usuário)
  - [3. 📂 Saúde das Entregas por Projeto (Barras + Donut)](#3-📂-saúde-das-entregas-por-projeto-barras--donut)
  - [4. ⏱️ Aging & Alertas de Prazos Críticos](#4-⏱️-aging--alertas-de-prazos-críticos)
- [Regras de Cálculo de Prazos e Datas](#-regras-de-cálculo-de-prazos-e-datas)
- [Testes](#-testes)
- [Arquitetura e Boas Práticas Técnicas](#-arquitetura-e-boas-práticas-técnicas)
- [Guia de Manutenção e Atualização da Documentação](#-guia-de-manutenção-e-atualização-da-documentação)
- [Como Executar o Projeto Localmente](#-como-executar-o-projeto-localmente)

---

## 🎯 Visão Geral

O sistema permite organizar demandas da equipe em **Espaços/Projetos** e **Listas**, oferecendo visualizações interativas em **Quadro (Kanban)**, **Lista Profissional**, **Tela de Equipe** e um completo **Painel de Indicadores e Gráficos (Dashboard ECharts)**.

### Stack Tecnológica:
- **Linguagem**: Python 3.11+
- **Interface**: Streamlit com temas e CSS customizados inspirados em softwares SaaS modernos (Linear, Notion, ClickUp).
- **Gráficos Interativos**: **Apache ECharts** v5.4.3 via CDN (com tooltips em dark glassmorphism, gradientes e animações).
- **Banco de Dados & Autenticação**: Supabase (PostgreSQL + RLS com controle de permissões por perfil).

---

## 🔐 Controle de Acesso e Regras de Permissão (RBAC)

O sistema possui um controle de permissões granular baseado no perfil do usuário (`gestor` / `admin` vs `membro` comum):

### 👑 Perfil Gestor / Admin (`gestor = True` ou cargo `"admin"`):
- **Acesso Total**: Pode criar, editar todos os campos (título, descrição, responsável, prioridade, data limite, tags), alterar status e excluir tarefas.
- **Subtarefas**: Adição, marcação de conclusão e remoção de subtarefas liberados.
- **Espaços & Equipe**: Acesso exclusivo para criar e excluir Espaços/Listas de trabalho e gerenciar integrantes na aba de Equipe.

### 👤 Perfil Membro Comum (Sem permissão de Gestor/Admin):
- **Ações Permitidas**:
  1. **Modificar Status da Tarefa**: Alteração livre do status da tarefa (no Quadro Kanban, Visão em Lista e Modal de Detalhes).
  2. **Comentários**: Leitura, envio de novos comentários e exclusão dos próprios comentários.
- **Restrições Aplicadas (UI & Banco)**:
  - **Criar Tarefas**: Botão *"＋ Criar Tarefa"* ocultado na barra lateral.
  - **Edição de Tarefas**: Campos de Título, Descrição, Responsável, Prioridade, Data Limite e Tags ficam em modo leitura (`disabled=True`).
  - **Subtarefas**: Exibidas em modo somente leitura (sem permissão de marcação, inclusão ou exclusão).
  - **Exclusão de Tarefas**: Botão *"Excluir Tarefa"* ocultado.
  - **Segurança Nativa (RLS)**: Restrições validadas diretamente no PostgreSQL via *Row Level Security* (RLS) no Supabase.

---

## 🎨 Design da Tabela de Tarefas (UI/UX Profissional)

A Visão em Lista (`src/ui/list_view.py` e `src/ui/styles.py`) foi desenhada com alto padrão visual:

1. **Container Glassmorphism (`.tabela-wrap`)**: Moldura com cantos arredondados (`16px`), borda translúcida e sombra multicamadas.
2. **Badges de Alta Visibilidade (`.badge-destaque`)**: Pílulas de destaque em **Roxo Escuro em Gradiente (`#6452db` a `#4c1d95`) com Fonte Branco Neve (`#ffffff`)** aplicadas nas contagens superiores e no rodapé.
3. **Barra de Resumo por Status (`.tabela-resumo`)**: Exibe no topo da tabela mini-contadores dinâmicos para cada status (*A Fazer*, *Em Progresso*, *Em Revisão*, *Concluído*).
4. **Alerta de Atraso Pulsante (`.data-atrasada`)**: Prazos estourados são destacados em vermelho com uma bolinha animada (`@keyframes pulso-atraso`).
5. **Rodapé com Progresso (`.tabela-rodape`)**: Barra de progresso visual exibindo a porcentagem (%) e contagem de tarefas concluídas.

---

## 📊 Painel de Indicadores e Gráficos (Apache ECharts)

O módulo de **Dashboard** (`src/ui/dashboard.py`) utiliza a biblioteca **Apache ECharts** via CDN com renderização interativa.

### Cards KPI Customizados
Os indicadores do topo do dashboard (Projetos/Tarefas, Entregas Concluídas, Entregas Atrasadas, Média Dias em Andamento) utilizam **cards HTML customizados** em vez do `st.metric()` padrão do Streamlit.

- **CSS**: Classe `.kpi-card` definida em `src/ui/styles.py` (seção `kpi cards`).
- **Design**: Borda lateral colorida de 4px (variável CSS `--kpi-accent`), `border-radius: 12px`, sombra multi-camada e hover com elevação (`translateY(-2px)`).
- **Cores de Acento**: Roxo (`#6452db`) para Projetos, Verde (`#10b981`) para Concluídas, Vermelho (`#ef4444`) para Atrasadas, Azul (`#3b82f6`) para Média.
- **Valor**: Fonte `28px`, peso `800`, cor `#0f172a` (Slate 900). Subtítulo contextual com classes `.kpi-delta--positive` / `.kpi-delta--negative`.
- **Manutenção**: Para alterar cores ou layout, editar `.kpi-card` e `.kpi-row` em `src/ui/styles.py`. Para alterar rótulos/valores, editar o bloco `kpi_html` em `src/ui/dashboard.py`.

### Recursos Visuais dos Gráficos:
- **Dark Glassmorphism Tooltips**: Popups em fundo Slate 900 (`rgba(15, 23, 42, 0.92)`) com `backdrop-filter: blur(10px)`, bordas neon em roxo e texto **Branco Neve**.
- **Gradientes de Cores Vibrantes**: Barras e fatias com gradientes e cantos arredondados (`borderRadius`).
- **Eixos de Alto Contraste**: Rótulos dos eixos X e Y usam cor escura `#0f172a` (Slate 900), peso `600`, tamanho `12px`, família `Inter`. Linhas de eixo em `#94a3b8` e gridlines em `#e2e8f0` garantem legibilidade total dos valores numéricos. Alteração feita em `src/ui/dashboard.py` nas propriedades `axisLabel`, `axisLine` e `splitLine` de todos os 4 gráficos (Gantt, Usuários, Projetos e Aging).

---

### 1. 📅 Cronograma (Gráfico de Gantt Interativo)
- **O que é**: Linha do tempo horizontal contínua das tarefas a partir da data de criação até a data limite.
- **Para que serve**: Planejamento temporal, identificação de gargalos e alternância dinâmica de cores por **Status** ou por **Projeto**.

### 2. 👤 Situação e Carga por Usuário
- **O que é**: Gráfico de barras empilhadas com cantos superiores arredondados por integrante da equipe.
- **Detalhamento**: Seleção individual do integrante para abrir tabela detalhada de suas entregas.

### 3. 📂 Saúde das Entregas por Projeto (Barras + Donut)
- **Status por Projeto**: Gráfico de barras empilhadas comparando a carga entre os Espaços/Projetos.
- **Gráfico de Rosca por Prioridade (Donut Chart)**: Anel com raio vazado (`48%` a `75%`), bordas separadoras brancas e contador central em destaque.

### 4. ⏱️ Aging & Alertas de Prazos Críticos
- **Histograma de Aging**: Barras verticais categorizando tarefas pendentes por faixas de tempo (`0-7d`, `8-15d`, `16-30d`, `+30d`).
- **Alerta de Vencimento e Atrasos**: Painel proativo listando **exclusivamente tarefas pendentes** que estejam atrasadas ou prestes a vencer nos próximos 3 dias.

---

## 📐 Regras de Cálculo de Prazos e Datas

> **Onde mora a regra:** toda a matemática de prazo está em **`src/prazos.py`**,
> um módulo puro (sem Streamlit, sem banco) coberto por `tests/test_prazos.py`.
> O dashboard só consome o resultado. Se precisar mudar uma regra de prazo,
> mude lá — e só lá.

### 1. As duas datas que o cálculo usa (e a que ele **não** usa)

| Coluna | O que é | Usar como data de entrega? |
|---|---|---|
| `data_limite` | `date` — o dia combinado. Sem hora, sem fuso. | — |
| `concluido_em` | `timestamptz` — instante em que a tarefa entrou em "Concluído". Escrito só pelo trigger `tasks_set_concluido_em`, e apagado se a tarefa for reaberta. | ✅ **Sim** |
| `atualizado_em` | `timestamptz` — carimbado pelo trigger `tasks_touch` a **cada** `UPDATE`. Serve para detectar edição concorrente (`visto_em`). | ❌ **Não** |

### 2. Dias em Andamento
Indica quantos dias o projeto/tarefa permaneceu ativo desde a criação:
- **Para Tarefas em Aberto**:
  $$\text{Dias em Andamento} = \text{Hoje} - \text{Data de Criação (\texttt{criado\_em})}$$
- **Para Tarefas Concluídas** (o relógio para na entrega):
  $$\text{Dias em Andamento} = \text{Data da Entrega (\texttt{concluido\_em})} - \text{Data de Criação (\texttt{criado\_em})}$$

Nunca é negativo: dado inconsistente (entrega antes da criação) exibe `0`.

### 3. Situação do Prazo e Atrasos
- **Tarefas Concluídas**: a data limite é comparada contra a **Data Real da Entrega (`concluido_em`)**.
  - Se $\text{Entrega} \le \text{Data Limite} \rightarrow$ **"Concluído no prazo"** (selo verde).
  - Se $\text{Entrega} > \text{Data Limite} \rightarrow$ **"Concluído com X dia(s) de atraso"** (selo laranja).
  - Sem `data_limite` $\rightarrow$ **"Concluído (sem prazo definido)"**.
  - O número **não cresce com o tempo**: atraso de entrega é fato histórico, congelado na data em que aconteceu.
- **Tarefas em Aberto**: a data limite é comparada contra **Hoje**.
  - Se $\text{Hoje} > \text{Data Limite} \rightarrow$ **"Atrasado há X dia(s)"** (selo vermelho).
  - Se $\text{Hoje} = \text{Data Limite} \rightarrow$ **"Vence hoje!"**.
  - Se faltam até **3 dias** (`JANELA_ALERTA`) $\rightarrow$ **"Vence em X dia(s)"** (selo amarelo).
  - Caso contrário $\rightarrow$ **"Faltam X dia(s)"**.

### 4. `atrasado` × `entregue_com_atraso` — não são a mesma coisa

`calcular_prazo` devolve dois campos distintos, e a diferença define o que entra em cada indicador:

| Campo | Significa | Onde entra |
|---|---|---|
| `atrasado` | Está **pendente e vencida agora** | KPI "Entregas Atrasadas", KPI por usuário, Painel de Alertas |
| `entregue_com_atraso` | Foi entregue depois do prazo (**histórico**) | Só o selo da coluna "Situação do Prazo" |

Uma tarefa concluída **nunca** tem `atrasado = True`. Antes um campo só
acumulava os dois sentidos e cada consumidor precisava lembrar de escrever
`and status != "Concluído"` — três lugares, três chances de esquecer.

### 5. Fuso horário: por que não basta cortar a string no "T"

O Postgres devolve `timestamptz` em **UTC** (`2026-07-21T00:30:00+00:00`), e o
Streamlit Cloud roda o servidor em UTC. Duas consequências tratadas em
`src/prazos.py`:

- **Timestamps** (`concluido_em`, `criado_em`, `atualizado_em`) são convertidos
  para `FUSO_APP` (`America/Sao_Paulo`) **antes** de virarem dia. Uma entrega às
  21h de Brasília é `00:30` UTC do dia seguinte: pegar o dia UTC dava um dia de
  atraso que não existiu.
- **`data_limite` é `date`** — dia de calendário, sem hora. **Não** sofre
  conversão nenhuma; converter um dia puro produziria o mesmo erro ao contrário.
- **"Hoje" é `prazos.hoje()`**, não `date.today()`: o dia local da equipe, não o
  dia do servidor.

> Dependência: o pacote **`tzdata`** está no `requirements.txt` porque o Windows
> não traz base de fusos. Sem ele o módulo cai num offset fixo de `UTC-03` e
> registra um `WARNING` — erra no máximo uma hora no horário de verão, em vez de
> derrubar o painel.

### 6. Histórico da correção (jul/2026)

A coluna "Situação do Prazo" da tabela *Lista de Projetos / Tarefas sob
responsabilidade* (aba **👤 Situação por Usuário**) exibia
`"Concluído com 3d de atraso"` em tarefas entregues **no prazo**. Três causas:

1. **A data de entrega saía de `atualizado_em`.** Como o trigger `tasks_touch` o
   carimba a cada `UPDATE`, trocar uma tag ou corrigir o título empurrava a
   "entrega" para frente. Uma tarefa entregue no dia 19 com prazo dia 20 e
   editada no dia 23 passava a acusar 3 dias de atraso. **Correção:** coluna
   `concluido_em` + trigger `tasks_set_concluido_em`
   (`sql/06_concluido_em.sql`), escrita só na transição para "Concluído".
2. **Timestamp UTC cortado no "T", sem conversão de fuso.** Entrega no fim da
   tarde ganhava um dia de atraso fantasma. **Correção:** `prazos.para_data()`
   converte instantes para o fuso local e deixa datas puras intactas.
3. **O selo `alerta` não existia na tabela de cores** e caía no cinza do `else`,
   ficando visualmente igual a "Sem data limite". **Correção:**
   `ESTILO_BADGE_PRAZO` no `dashboard.py`, um dicionário no lugar da escada de
   ternários.

Também nesta correção: a tabela ganhou a coluna **"Entrega Real"** ao lado de
"Prazo Limite", para a conta ser conferível na própria tela, e as datas passaram
a ser exibidas em `dd/mm/aaaa` em vez do ISO cru.

**Migração obrigatória em bancos existentes:** rode `sql/06_concluido_em.sql`
uma vez no SQL Editor do Supabase. Ele cria a coluna, o trigger e preenche o
histórico com o `atualizado_em` que existia (a melhor estimativa disponível —
exata para tarefas que não foram editadas depois de concluídas). Enquanto a
migração não roda, o cálculo cai automaticamente no comportamento antigo, sem
quebrar.

---

## 🧪 Testes

A suíte cobre as regras de prazo — o cálculo que não pode errar, porque é dele
que saem os indicadores de desempenho da equipe.

```bash
pip install -r requirements-dev.txt
pytest
```

| Arquivo | Cobre |
|---|---|
| `tests/test_prazos.py` | Conversão de datas e fuso, situação do prazo (concluída e pendente), dias em andamento, painel de críticas e os testes de regressão dos bugs descritos acima |

**Padrão dos testes:** `src/prazos.py` não importa Streamlit nem toca no banco,
então a suíte roda em menos de um segundo, sem servidor, sem credencial e sem
mock. Regra prática ao mexer em regra de negócio: se para testar você precisa
subir a aplicação, a regra está no lugar errado — mova-a para um módulo puro.

Todo teste de regressão referencia o defeito que o originou no próprio nome
(`test_regressao_edicao_tardia_nao_inventa_atraso`, por exemplo), para que
quem quebrá-lo entenda de imediato o que deixou de funcionar.

---

## 🛠️ Arquitetura e Boas Práticas Técnicas

### ⚠️ Regra de Ouro para Renderização HTML no Streamlit:
O Streamlit executa a função `st.markdown(html, unsafe_allow_html=True)` passando o texto primeiro pelo parser de Markdown. **Linhas indentadas com 4 ou mais espaços de recuo são convertidas automaticamente em blocos de código texto (`<pre><code>`)**.

Para prevenir que tabelas HTML apareçam como texto cru no navegador:
- **Sempre utilize a função `limpar(html_string)`** de `src.ui.componentes`.
- A função `limpar()` remove a indentação de cada linha (`"".join(linha.strip() for linha in html.splitlines())`), garantindo renderização 100% limpa com CSS.

---

## 📖 Guia de Manutenção e Atualização da Documentação

Este repositório adota a prática de **Documentação Contínua**. Toda modificação no código-fonte, adição de dependências ou criação de regras de negócio deve ser refletida imediatamente neste arquivo.

### 📌 1. Onde Fica a Documentação?
- **Arquivo Único da Verdade**: [`README.md`](file:///d:/APP_TAREFAS_LUIZ/README.md) (na raiz do projeto).
- **Scripts SQL de Banco de Dados**: A pasta [`sql/`](file:///d:/APP_TAREFAS_LUIZ/sql) armazena os scripts de esquema e políticas RLS (`01_schema.sql`, `02_rls.sql`, etc.). Mudança de schema entra em **dois** lugares: no `01_schema.sql` (para instalação nova) e num arquivo de migração numerado (para os bancos que já existem) — ver `06_concluido_em.sql` como modelo.
- **Regras de Negócio Testáveis**: cálculo puro fica em módulo próprio (ex.: `src/prazos.py`) com teste em `tests/`, fora da camada de UI.

### 📝 2. O que Deve Ser Documentado?
Sempre que você ou um agente de IA realizar uma das alterações abaixo, atualize o `README.md`:
1. **Novas Funcionalidades / Telas**: Registrar na seção *Visão Geral* e na seção técnica correspondente.
2. **Regras de Permissão / RBAC**: Atualizar a seção *Controle de Acesso e Regras de Permissão*.
3. **Mudanças Visuais / UI**: Registrar novas classes CSS ou bibliotecas de frontend (ex: ECharts, componentes HTML).
4. **Fórmulas e Regras de Negócio**: Atualizar a seção *Regras de Cálculo de Prazos e Datas* — e o teste correspondente em `tests/`.
5. **Alterações no Banco / Supabase**: Documentar campos adicionados ou modificações nas políticas RLS, indicando qual script de migração precisa ser rodado.
6. **Correção de Bug de Cálculo**: registrar a causa raiz no histórico da seção afetada e cobrir com um teste de regressão nomeado `test_regressao_*`.

### 🔧 3. Como Realizar a Manutenção da Documentação (Passo a Passo)

1. **Localizar as Seções Afetadas**:
   Abra o `README.md` e verifique o **Sumário** para identificar quais seções serão impactadas pelas mudanças no código.

2. **Manter o Padrão de Formatação**:
   - Utilize marcas de títulos Markdown (`##` para seções principais, `###` para subseções).
   - Mantenha emojis temáticos no início dos títulos para facilidade de navegação visual.
   - Use blocos de código (````python ... ````) e sintaxe LaTeX (`$$...$$`) para fórmulas de cálculo.

3. **Atualizar o Sumário**:
   Se adicionar uma nova seção com `##`, insira o link correspondente na lista do `## 📋 Sumário` no topo do arquivo.

4. **Validar os Links Internos**:
   Certifique-se de que as ancoragens do sumário (ex: `#1-📅-cronograma-gráfico-de-gantt-interativo`) casem exatamente com a formatação dos títulos.

---

## 💻 Como Executar o Projeto Localmente

1. **Clonar o Repositório e Criar Ambiente Virtual**:
   ```bash
   python -m venv .venv
   # No Windows:
   .venv\Scripts\activate
   # No Linux/Mac:
   source .venv/bin/activate
   ```

2. **Instalar Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar o Arquivo `.env`**:
   Copie o arquivo `.env.example` para `.env` e preencha com as credenciais do seu projeto Supabase:
   ```env
   SUPABASE_URL="https://sua-url.supabase.co"
   SUPABASE_ANON_KEY="sua-chave-anon-aqui"
   ```

4. **Aplicar os Scripts SQL no Supabase**:
   No SQL Editor do projeto, rode os arquivos da pasta `sql/` **em ordem**:
   `01_schema.sql` → `02_rls.sql` → `03_seed.sql` → `04_extras.sql` →
   `05_seed_tasks.sql` → `06_concluido_em.sql`.
   Em bancos que já existiam antes da correção de prazos, o `06_concluido_em.sql`
   é obrigatório (ver *Regras de Cálculo de Prazos e Datas*). Todos são
   idempotentes: rodar de novo não faz mal.

5. **Executar a Aplicação**:
   ```bash
   streamlit run app.py
   ```

6. **Rodar os Testes** (opcional, mas recomendado antes de subir alteração):
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```