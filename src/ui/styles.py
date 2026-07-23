"""CSS injetado — aproxima o Streamlit do manager_ui_prototype.html.

O protótipo é Tailwind puro. Aqui as classes viraram variáveis CSS com os
mesmos valores de slate/purple, e os seletores atacam os `data-testid` do
Streamlit — que é o único gancho estável que ele expõe.

Regras de acabamento seguidas ao longo do arquivo:
  - raio concêntrico: raio externo = raio interno + padding
  - `transition-property` explícito (nunca `transition: all`)
  - `tabular-nums` em tudo que é contador
  - alvo de clique mínimo de 40px nos controles
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  /* paleta ClickUp do protótipo */
  --roxo:        #7b68ee;
  --roxo-escuro: #6452db;
  --roxo-suave:  #f5f3ff;   /* purple-50 */
  --rosa:        #ff007a;

  /* slate */
  --s50:  #f8fafc;
  --s100: #f1f5f9;
  --s200: #e2e8f0;
  --s300: #cbd5e1;
  --s400: #94a3b8;
  --s500: #64748b;
  --s600: #475569;
  --s700: #334155;
  --s800: #1e293b;
  --s900: #0f172a;

  --sombra-card:  0 1px 2px rgba(15, 23, 42, .06), 0 1px 3px rgba(15, 23, 42, .04);
  --sombra-hover: 0 4px 6px -1px rgba(15, 23, 42, .07), 0 2px 4px -2px rgba(15, 23, 42, .05);
}

html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

html, body, [class*="st-"], [class*="css-"] {
  font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}

/* Os ícones do Streamlit são ligaduras da Material Symbols, e a classe
   deles casa com o [class*="st-"] acima. Sem esta exceção a fonte cai
   para a Inter e o ícone aparece como o texto "keyboard_double_arrow_left". */
[data-testid="stIconMaterial"] {
  font-family: 'Material Symbols Rounded' !important;
}

/* ---------------------------------------------------------- cromo do Streamlit */

footer, [data-testid="stDecoration"],
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"] { display: none; }

/* O header some da vista, mas NÃO com `display:none`: é ele que hospeda o
   indicador de conexão do Streamlit. Escondendo o header inteiro, um app
   desconectado — em que o Streamlit desabilita todos os widgets — ficava
   idêntico a um app normal, só que sem responder a nada. Custou uma sessão
   inteira de diagnóstico; o indicador fica. */
header[data-testid="stHeader"] {
  background: transparent !important;
  height: 0; min-height: 0;
  pointer-events: none;
}
[data-testid="stToolbar"] { right: .5rem; top: .5rem; }
[data-testid="stToolbarActions"] { pointer-events: auto; }

/* "Connecting" / "Running" com o peso visual do resto da interface. */
[data-testid="stStatusWidget"] {
  background: #fff;
  border: 1px solid var(--s200);
  border-radius: 9999px;
  padding: .125rem .625rem .125rem .25rem;
  box-shadow: var(--sombra-card);
  font-size: 11px; font-weight: 500; color: var(--s600);
}

[data-testid="stAppViewContainer"] { background: var(--s100); }

.block-container {
  padding: 1.25rem 1.5rem 3rem;
  max-width: 100%;
}

/* barra de rolagem fina, igual ao protótipo */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, .4); border-radius: 9999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, .7); }

/* ------------------------------------------------------------------- sidebar */

[data-testid="stSidebar"] {
  background: #fff;
  border-right: 1px solid var(--s200);
  width: 260px !important;
}
[data-testid="stSidebar"] > div { padding-top: 0; }
[data-testid="stSidebarContent"] { padding: 0 .75rem 1rem; }
[data-testid="stSidebarCollapseButton"] button { color: var(--s400); }

.ws-header {
  display: flex; align-items: center; gap: .625rem;
  padding: .875rem .25rem;
  border-bottom: 1px solid var(--s200);
  margin: 0 -.25rem .75rem;
}
.ws-logo {
  width: 32px; height: 32px; border-radius: 10px;
  background: linear-gradient(to top right, var(--roxo), var(--rosa));
  color: #fff; font-weight: 700; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 6px -1px rgba(123, 104, 238, .25);
  flex-shrink: 0;
}
.ws-nome  { font-size: 13px; font-weight: 700; color: var(--s900); line-height: 1.2; }
.ws-plano { font-size: 11px; color: var(--s500); }

/* Espaçamento em `padding`, não em `margin`: o contêiner de elemento do
   Streamlit mede só a caixa de texto, então a margem vazava para fora dele
   e o botão seguinte subia por cima do título. */
.side-titulo {
  font-size: 11px; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: var(--s400);
  margin: 0; padding: .875rem .25rem .375rem;
}

/* árvore de espaços */
.espaco-linha {
  display: flex; align-items: center; justify-content: space-between;
  padding: .375rem .5rem; border-radius: 6px;
  font-size: 12px; font-weight: 500; color: var(--s700);
}
.espaco-linha .ponto {
  width: 10px; height: 10px; border-radius: 50%;
  display: inline-block; flex-shrink: 0; margin-right: .5rem;
}
.espaco-linha .contador {
  font-size: 10px; color: var(--s400); font-weight: 400;
  font-variant-numeric: tabular-nums;
}
.lista-linha {
  display: flex; align-items: center; gap: .5rem;
  padding: .25rem .5rem .25rem 1.5rem; border-radius: 6px;
  font-size: 12px; font-weight: 500; color: var(--s500);
}

/* Os itens da árvore são botões de verdade (o clique troca o escopo), mas
   precisam parecer linhas de navegação: sem moldura, texto à esquerda e
   fundo só no hover. */
.st-key-nav_arvore { gap: .0625rem; }
/* O Streamlit fecha todo bloco de markdown com `margin-bottom: -1rem` para
   comer a margem do <p> que ele geraria. Aqui o conteúdo é um <div> sem
   margem nenhuma, então os -16px viravam sobreposição: o botão "Todas as
   tarefas" subia por cima do título "Espaços de trabalho". */
.st-key-nav_arvore [data-testid="stMarkdownContainer"],
.st-key-nav_arvore [data-testid="stMarkdown"] {
  margin-bottom: 0 !important;
}
.st-key-nav_arvore .stButton button {
  border: none; box-shadow: none; background: transparent;
  justify-content: flex-start; text-align: left;
  min-height: 32px; padding: .25rem .5rem;
  border-radius: 6px; color: var(--s700);
}
/* O `justify-content` do <button> não basta: o Streamlit embrulha o rótulo
   num <div> próprio que recentraliza o texto. O alinhamento à esquerda tem
   de descer até ele e até o <p>. */
.st-key-nav_arvore .stButton button > div {
  width: 100%; justify-content: flex-start; text-align: left;
}
.st-key-nav_arvore .stButton button p {
  font-size: 12px; font-weight: 500; text-align: left; width: 100%;
}
.st-key-nav_arvore .stButton button:hover { background: var(--s100); }

/* Espaço e lista: um recuo à esquerda abre a canaleta onde o ponto colorido
   (ou o ícone) é posicionado por cima, já que rótulo de botão só aceita
   markdown — SVG e cor arbitrária não passam por ali. */
[class*="st-key-esp_wrap_"], [class*="st-key-lst_wrap_"] {
  position: relative; gap: 0;
}
/* 2.5rem, não 2rem: o ícone ocupa de 20px a 34px dentro da canaleta, então
   o texto precisa começar depois disso — com 2rem as duas coisas se
   encostavam. */
[class*="st-key-lst_wrap_"] .stButton button {
  padding-left: 2.5rem; color: var(--s500);
}
[class*="st-key-esp_wrap_"] .stButton button { padding-left: 1.375rem; }
/* `top: 16px`, e não `50%`: o <span> é filho de um stElementContainer que o
   Streamlit já deixa `position: relative`, então a porcentagem resolveria
   contra a altura DELE — que é zero por definição aqui. 16px é meia altura
   da linha de 32px, medida do topo do contêiner, que começa junto com ela. */
.ponto-espaco, .icone-lista {
  position: absolute; top: 16px; transform: translateY(-50%);
  z-index: 1; pointer-events: none;
}
.ponto-espaco {
  left: .5rem; width: 10px; height: 10px; border-radius: 50%;
}
.icone-lista {
  left: 1.25rem; color: var(--s400);
  display: inline-flex; align-items: center;
}
/* O <span> solto vira um elemento de altura zero para não empurrar o botão:
   ele existe só como âncora visual. */
[class*="st-key-esp_wrap_"] [data-testid="stElementContainer"]:has(.ponto-espaco),
[class*="st-key-lst_wrap_"] [data-testid="stElementContainer"]:has(.icone-lista) {
  height: 0; margin: 0; overflow: visible;
}

/* rodapé de perfil */
.perfil-rodape {
  display: flex; align-items: center; gap: .625rem;
  min-width: 0;
}
/* A borda mora no contêiner, não no bloco do perfil: com as duas colunas
   (perfil + botão) ela precisa atravessar a sidebar inteira. */
.st-key-rodape_perfil {
  padding-top: 1rem; margin-top: .75rem; margin-bottom: .875rem;
  border-top: 1px solid var(--s200);
}
.st-key-rodape_perfil [data-testid="stHorizontalBlock"] { align-items: center; }
/* O markdown do Streamlit carrega um `margin-bottom: -16px` que existe para
   comer a margem do <p>. Como aqui o conteúdo é um flex de 32px, a margem
   negativa encolhia a coluna e o botão subia 8px em relação ao avatar. */
.st-key-rodape_perfil .stMarkdown div { margin-bottom: 0 !important; }
/* Os dois <span> de tooltip que o `help=` insere encolhem em torno do botão
   e o empurram para fora da coluna. Esticá-los devolve o alinhamento à
   direita, e o botão fica com a largura fixa do quadrado. */
.st-key-rodape_perfil .stButton,
.st-key-rodape_perfil .stTooltipIcon,
.st-key-rodape_perfil .stTooltipHoverTarget {
  display: flex; width: 100%; justify-content: flex-end;
}
/* botão discreto de sair — só ícone, sem moldura, fundo só no hover */
.st-key-rodape_perfil .stButton button {
  min-height: 32px; height: 32px; flex: 0 0 32px; padding: 0;
  border: none; box-shadow: none; background: transparent;
  color: var(--s400); border-radius: 8px;
}
.st-key-rodape_perfil .stButton button:hover {
  background: var(--s100); color: var(--s700);
}
.st-key-rodape_perfil [data-testid="stIconMaterial"] { font-size: 18px; }
/* O bloco de texto vira flex-column para que o avatar centre contra as
   DUAS linhas juntas. Com os <div> soltos, o align-items do pai alinhava
   pela caixa de linha do primeiro filho e o avatar subia alguns pixels. */
.perfil-texto {
  display: flex; flex-direction: column; justify-content: center;
  min-width: 0;
}
.perfil-nome  { font-size: 12px; font-weight: 600; color: var(--s800); line-height: 1.35; }
.perfil-cargo { font-size: 10px; color: var(--s400); line-height: 1.35; }

.avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--roxo); color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600; letter-spacing: .02em;
  box-shadow: 0 0 0 2px rgba(123, 104, 238, .25);
  flex-shrink: 0;
}
.avatar.mini {
  width: 20px; height: 20px; font-size: 9px; box-shadow: 0 0 0 1px #fff;
}

/* ------------------------------------------------------------------- topo */

.topbar {
  background: #fff;
  border: 1px solid var(--s200);
  border-radius: 12px;
  padding: .75rem 1rem;
  margin-bottom: .75rem;
}
.migalhas {
  display: flex; align-items: center; gap: .5rem;
  font-size: 12px; color: var(--s400);
}
.migalhas .sep   { color: var(--s300); }
.migalhas .atual {
  font-weight: 600; color: var(--s800);
  display: inline-flex; align-items: center; gap: .375rem;
}
.migalhas .atual .ponto { width: 8px; height: 8px; border-radius: 50%; }

/* ------------------------------------------------------------------- kanban */

.col-topo {
  display: flex; align-items: center; gap: .5rem;
  padding: 0 .25rem .625rem;
}
.col-topo .ponto { width: 10px; height: 10px; border-radius: 50%; }
.col-topo h3 {
  font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .04em; color: var(--s700); margin: 0;
}
.col-topo .contador {
  border-radius: 9999px; padding: .1rem .5rem;
  font-size: 10px; font-weight: 700;
  font-variant-numeric: tabular-nums;
}

/* coluna: raio 12px = raio do card (8px) + padding (4px)… arredondado
   para 12/8, que é o par do protótipo (rounded-xl sobre rounded-lg).
   `.coluna` é a versão em HTML puro; `.st-key-coluna_N` é o container
   Streamlit que a substituiu quando os cards ganharam botão. */
.coluna,
[class*="st-key-coluna_"] {
  background: rgba(226, 232, 240, .5);
  border: 1px solid rgba(226, 232, 240, .8);
  border-radius: 12px;
  padding: .75rem;
  min-height: 180px;
}
[class*="st-key-coluna_"] { gap: .625rem; }

/* Card clicável: o container É o card — moldura branca, sombra e âncora de
   posicionamento — e o botão que veio depois é esticado por cima. Com a
   caixa aqui e não num <div> do markdown, o seletor de status também cai
   dentro dela. O rótulo do botão continua no DOM (é o título da tarefa,
   para leitor de tela), só que sem tamanho. */
[class*="st-key-card_"] {
  position: relative;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, .8);
  border-radius: 8px;
  padding: .75rem;
  box-shadow: var(--sombra-card);
  gap: 0;
  transition-property: box-shadow, border-color;
  transition-duration: 150ms;
  transition-timing-function: ease-out;
}
/* O `width` do contêiner de elemento vem do Streamlit e não é `auto`, então
   `inset: 0` sozinho não o estica: sem o 100% explícito ele encolhe até o
   rótulo (que está clipado) e sobra uma tira de 16px clicável. */
[class*="st-key-card_"] [class*="st-key-abrir_"] {
  position: absolute; inset: 0; z-index: 1;
  width: 100% !important; height: 100%;
}
[class*="st-key-card_"] [class*="st-key-abrir_"] .stButton,
[class*="st-key-card_"] [class*="st-key-abrir_"] .stButton button {
  width: 100%; height: 100%;
}
[class*="st-key-card_"] [class*="st-key-abrir_"] .stButton button {
  background: transparent; border: none; box-shadow: none;
  padding: 0; min-height: 0; border-radius: 8px;
}
/* O título fica invisível mas continua no DOM e acessível ao leitor de tela.
   `font-size: 0` no botão não bastaria: o Streamlit embrulha o rótulo num
   <p> com tamanho próprio, e o texto reaparecia por cima do card. */
[class*="st-key-card_"] [class*="st-key-abrir_"] .stButton button p {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; white-space: nowrap; clip-path: inset(50%);
}
[class*="st-key-card_"] [class*="st-key-abrir_"] .stButton button:hover {
  background: rgba(123, 104, 238, .05);
}
[class*="st-key-card_"]:hover {
  box-shadow: var(--sombra-hover);
  border-color: rgba(123, 104, 238, .5);
}
/* O Streamlit fecha todo bloco de markdown com `margin-bottom: -1rem`. Aqui
   isso comeria o espaço entre o corpo do card e o seletor de status. */
[class*="st-key-card_"] [data-testid="stMarkdownContainer"] {
  margin-bottom: 0 !important;
}

/* Seletor de status — o "arrastar para outra coluna" do protótipo.
   Precisa vencer o botão invisível que cobre o card (z-index 1), senão o
   clique abriria o detalhe. */
[class*="st-key-status_"] {
  position: relative; z-index: 2;
  margin-top: .5rem;
  max-width: 140px;
}
[class*="st-key-status_"] [data-baseweb="select"] > div {
  min-height: 28px !important;
  border-radius: 6px !important;
  font-size: 10px !important;
  background: var(--s50) !important;
}
/* A coluna do Kanban é estreita: sem apertar o padding interno, "Em Progresso"
   e "Concluído" chegavam truncados como "Em Pro…" na largura padrão. */
[class*="st-key-status_"] [data-baseweb="select"] > div > div:first-child {
  padding-left: .5rem; padding-right: 0;
}
[class*="st-key-status_"] [data-baseweb="select"] svg { width: 13px; height: 13px; }
/* A lista suspensa é um portal no <body>, fora do card, e nasce com a
   largura do seletor — que aqui é estreito de propósito, e daí saía
   "Em Prog…" na hora de escolher.
   A largura tem de entrar no <div> do popover, não na lista: o dropdown é
   virtualizado e o Streamlit põe `width:100%` INLINE em cada nível de dentro
   (ul, viewport e li), então nada lá dentro consegue crescer sozinho — e
   `max-content` daria zero, porque mede filhos que só sabem dizer "100%".
   O `:has()` limita a regra aos popovers de selectbox, deixando tooltips e
   menus em paz. Os filtros do topo já passam de 150px, então não mudam. */
[data-baseweb="popover"]:has([data-testid="stSelectboxVirtualDropdown"]) {
  min-width: 150px;
}
/* O corpo do popover não acompanha sozinho: o BaseWeb mede o seletor e crava
   a largura nele, então o `min-width` de cima esticaria só a casca. Esticado
   o corpo, o `width:100%` inline de ul/viewport/li cai em cascata sozinho. */
[data-baseweb="popover"]:has([data-testid="stSelectboxVirtualDropdown"])
  > div > div { width: 100%; }
[class*="st-key-status_"] [data-baseweb="select"] > div > div:last-child {
  padding-left: 0; padding-right: .125rem;
}

/* -------------------------------------------------------- modal de detalhe */

/* Os dois modais (criar e detalhe) usam a mesma largura, a do modal de tarefa
   do protótipo (max-w-md = 448px). O `width` do `st.dialog` sozinho não serve:
   mesmo no "small" o Streamlit dimensiona por porcentagem da viewport, então
   numa tela larga o formulário esticava até quase a borda. */
/* `> div`, e não `div[role="dialog"]`: nesta versão o Streamlit não põe role
   nenhum na caixa do modal, e a regra antiga não casava com nada — era por
   isso que o detalhe abria com os 500px e a altura livre do padrão.
   O detalhe cresce com o conteúdo (subtarefas e comentários não têm teto),
   então sem um limite o modal virava uma página. Com a altura travada, quem
   rola é o miolo. */
[data-testid="stDialog"] > div {
  width: 640px !important;
  max-width: calc(100vw - 2rem) !important;
  max-height: min(660px, calc(100vh - 4rem)) !important;
  overflow-y: auto;
}

/* Modal compacto: o espaçamento padrão do Streamlit é pensado para uma
   página inteira, e dentro de 448px ele dobra a altura do formulário. */
[data-testid="stDialog"] [data-testid="stVerticalBlock"] { gap: .5rem; }
[data-testid="stDialog"] [data-testid="stElementContainer"] { margin-bottom: 0; }
[data-testid="stDialog"] hr,
[data-testid="stDialog"] [data-testid="stDivider"] { margin: .375rem 0; }
[data-testid="stDialog"] [data-testid="stTextArea"] textarea { min-height: 72px; }
[data-testid="stDialog"] label[data-testid="stWidgetLabel"] { margin-bottom: .125rem; }

/* Botões de excluir: roxo bem suave, com um leve brilho neon. Fundo lavanda
   claro e texto/borda roxos em vez do vermelho de perigo — o app inteiro é
   roxo, então a exclusão pede confirmação em dois passos e não precisa gritar.
   O "Sim, excluir" nasce `primary` (roxo cheio); aqui ele também vira o suave,
   para os dois botões de exclusão falarem a mesma língua. */
.st-key-btn_excluir button,
.st-key-btn_confirmar_exclusao button {
  background: var(--roxo-suave) !important;
  color: var(--roxo) !important;
  border: 1px solid #ddd6fe !important;   /* violet-200 */
  box-shadow: 0 0 0 1px rgba(123, 104, 238, .12),
              0 0 12px rgba(123, 104, 238, .28) !important;
  transition: background-color 150ms, box-shadow 150ms;
}
.st-key-btn_excluir button:hover,
.st-key-btn_confirmar_exclusao button:hover {
  background: #ede9fe !important;          /* violet-100 */
  border-color: var(--roxo) !important;
  box-shadow: 0 0 0 1px rgba(123, 104, 238, .2),
              0 0 16px rgba(123, 104, 238, .45) !important;
}
.st-key-btn_excluir button p,
.st-key-btn_confirmar_exclusao button p { color: var(--roxo) !important; }

.detalhe-codigo {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 11px; color: var(--s400); letter-spacing: .04em;
  margin-bottom: .25rem;
}
.secao-titulo {
  display: flex; align-items: center; gap: .5rem;
  font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .04em; color: var(--s700);
  margin-bottom: .5rem;
}
.contador-simples {
  font-size: 10px; font-weight: 600; color: var(--s500);
  background: var(--s100); border-radius: 9999px; padding: .1rem .45rem;
  font-variant-numeric: tabular-nums;
}
.comentario { display: flex; gap: .5rem; padding: .25rem 0; }
.comentario-topo {
  font-size: 11px; font-weight: 600; color: var(--s700);
  display: flex; align-items: baseline; gap: .5rem;
}
.comentario-data { font-size: 10px; font-weight: 400; color: var(--s400); }
.comentario-texto {
  font-size: 12px; color: var(--s600); line-height: 1.5;
  text-wrap: pretty;
}

/* A moldura do card mora em `[class*="st-key-card_"]`, lá em cima; daqui
   para baixo é só o miolo. */
.card-topo {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: .5rem;
}
.card-codigo {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 10px; font-weight: 500; color: var(--s400);
  font-variant-numeric: tabular-nums;
}
[class*="st-key-card_"] h4 {
  font-size: 12px; font-weight: 600; color: var(--s800);
  line-height: 1.4; margin: 0 0 .5rem; padding: 0;
  text-wrap: pretty;
}
.card-rodape {
  display: flex; align-items: center; justify-content: space-between;
  padding-top: .5rem; margin-top: .75rem;
  border-top: 1px solid var(--s100);
  font-size: 11px; color: var(--s400);
  font-variant-numeric: tabular-nums;
}
.card-rodape .meta { display: flex; align-items: center; gap: .625rem; }
.meta-item { display: inline-flex; align-items: center; gap: .25rem; }

/* badges */
.badge {
  display: inline-flex; align-items: center; gap: .25rem;
  font-size: 10px; font-weight: 600;
  padding: .125rem .5rem; border-radius: 4px;
  white-space: nowrap;
}
.badge.urgente { background: #fee2e2; color: #dc2626; }
.badge.alta    { background: #fef3c7; color: #d97706; }
.badge.normal  { background: #dbeafe; color: #2563eb; }
.badge.baixa   { background: var(--s100); color: var(--s500); }

.tag {
  display: inline-block;
  background: var(--s100); color: var(--s600);
  font-size: 10px; font-weight: 500;
  padding: .125rem .5rem; border-radius: 9999px;
}

.vazio {
  text-align: center; color: var(--s400);
  font-size: 11px; padding: 1.25rem .5rem;
  border: 1px dashed var(--s300); border-radius: 8px;
}

/* ------------------------------------------------------------------- lista */

.tabela-wrap {
  background: #fff; border: 1px solid var(--s200);
  border-radius: 12px; overflow: hidden;
  box-shadow: var(--sombra-card);
}
.tabela-topo {
  padding: .875rem 1rem; border-bottom: 1px solid var(--s200);
  font-size: 13px; font-weight: 600; color: var(--s800);
  display: flex; align-items: center; justify-content: space-between;
}
.tabela-topo span.sub { font-size: 11px; font-weight: 400; color: var(--s400); }
table.tarefas {
  width: 100%; border-collapse: collapse;
  font-size: 12px; color: var(--s600); text-align: left;
}
table.tarefas thead {
  background: var(--s50); color: var(--s400);
  border-bottom: 1px solid var(--s200);
}
table.tarefas th { padding: .625rem .75rem; font-weight: 500; }
table.tarefas td {
  padding: .625rem .75rem;
  border-top: 1px solid var(--s100);
  vertical-align: middle;
}
table.tarefas tbody tr {
  transition-property: background-color;
  transition-duration: 120ms;
}
table.tarefas tbody tr:hover { background: var(--s50); }
table.tarefas td.nome { font-weight: 500; color: var(--s800); }
table.tarefas td.data { font-variant-numeric: tabular-nums; }
.check {
  display: inline-block; width: 14px; height: 14px;
  border: 1.5px solid var(--s300); border-radius: 4px;
  vertical-align: -.15em;
}
.check.feito {
  border: none; color: var(--roxo); width: auto; height: auto;
}
.pill-status {
  font-size: 10px; font-weight: 600; padding: .125rem .5rem;
  border-radius: 9999px; background: var(--s100); color: var(--s700);
  white-space: nowrap;
}

/* ------------------------------------------------------------------ equipe */

/* Painel branco sobre o fundo slate — mesma moldura da tabela da Lista e da
   topbar, para a tela de Equipe não parecer de outro app. */
[class*="st-key-painel_"] {
  background: #fff;
  border: 1px solid var(--s200);
  border-radius: 12px;
  padding: 1rem 1.125rem 1.125rem;
  box-shadow: var(--sombra-card);
  margin-bottom: .75rem;
  gap: 0;
}
.painel-topo {
  display: flex; align-items: center; gap: .5rem;
  margin-bottom: .125rem;
}
.painel-topo h3 {
  font-size: 13px; font-weight: 700; color: var(--s800);
  margin: 0; padding: 0;
}
.painel-sub {
  font-size: 11px; color: var(--s400); margin: 0 0 .5rem;
  text-wrap: pretty;
}

/* Uma linha por pessoa, lida como tabela: filete acima de cada uma — o
   primeiro fica logo abaixo do título e serve de régua de cabeçalho.
   Não dá para reservar o filete só para "linha depois de linha": o Streamlit
   embrulha cada container num <div> próprio, então as linhas nunca são
   irmãs e o seletor `+` não casaria nunca. */
[class*="st-key-linha_"], [class*="st-key-conv_linha_"] {
  padding: .4rem .5rem;
  margin: 0 -.5rem;
  border-top: 1px solid var(--s100);
  gap: 0;
  transition-property: background-color;
  transition-duration: 120ms;
}
[class*="st-key-linha_"]:hover, [class*="st-key-conv_linha_"]:hover {
  background: var(--s50);
}
/* O `margin-bottom: -1rem` do markdown encolheria a coluna do nome e tiraria
   o avatar do eixo dos botões vizinhos. */
[class*="st-key-linha_"] [data-testid="stMarkdownContainer"],
[class*="st-key-conv_linha_"] [data-testid="stMarkdownContainer"] {
  margin-bottom: 0 !important;
}

.pessoa { display: flex; align-items: center; gap: .625rem; min-width: 0; }
.pessoa-texto { display: flex; flex-direction: column; min-width: 0; }
.pessoa-nome {
  font-size: 13px; font-weight: 600; color: var(--s800); line-height: 1.35;
  display: flex; align-items: center; gap: .375rem;
}
.pessoa-email {
  font-size: 11px; color: var(--s400); line-height: 1.35;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.pessoa-quando { font-size: 11px; color: var(--s400); }

.selo-voce, .selo-gestor {
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .04em; padding: .1rem .375rem; border-radius: 4px;
}
.selo-voce   { background: var(--s100); color: var(--s500); }
.selo-gestor { background: var(--roxo-suave); color: var(--roxo); }

.convite-linha { display: flex; align-items: center; gap: .5rem; }
.convite-email {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 12px; color: var(--s600);
}

/* O toggle vem com o rótulo "Gestor" à direita; em 13px ele briga com o nome
   da pessoa, então volta ao peso de legenda. */
[class*="st-key-linha_"] label[data-testid="stWidgetLabel"] p {
  font-size: 11px !important; color: var(--s500);
}

/* --------------------------------------------------------------- controles */

/* Descendente, não filho direto: quando o botão tem `help=`, o Streamlit o
   embrulha em dois <span> de tooltip e o `>` deixa de casar. */
.stButton button, .stFormSubmitButton button {
  border-radius: 8px;
  border: 1px solid var(--s200);
  background: #fff;
  color: var(--s600);
  font-size: 12px; font-weight: 500;
  min-height: 40px;                      /* alvo de clique confortável */
  box-shadow: var(--sombra-card);
  transition-property: background-color, border-color, color, box-shadow, transform;
  transition-duration: 150ms;
  transition-timing-function: ease-out;
}
.stButton button:hover, .stFormSubmitButton button:hover {
  border-color: var(--s300);
  color: var(--s800);
  background: var(--s50);
}
.stButton button:active, .stFormSubmitButton button:active {
  transform: scale(.98);
}
/* dentro de um st.form o `kind` vira "primaryFormSubmit", daí o ^= */
.stButton button[kind^="primary"], .stFormSubmitButton button[kind^="primary"] {
  background: var(--roxo); border-color: var(--roxo); color: #fff;
  box-shadow: 0 1px 2px rgba(123, 104, 238, .3);
}
.stButton button[kind^="primary"] p, .stFormSubmitButton button[kind^="primary"] p {
  color: #fff;
}
.stButton button[kind^="primary"]:hover, .stFormSubmitButton button[kind^="primary"]:hover {
  background: var(--roxo-escuro); border-color: var(--roxo-escuro); color: #fff;
}
.stButton button:focus-visible, .stFormSubmitButton button:focus-visible {
  outline: 2px solid var(--roxo); outline-offset: 2px;
}

/* inputs, selects */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div {
  border-radius: 8px !important;
  border-color: var(--s200) !important;
  background: #fff !important;
  font-size: 13px !important;
  min-height: 40px;
}
/* A borda visível dos campos mora no <div> que embrulha o <input>, não no
   <input> (que tem border-width 0). Nesta versão do Streamlit esse invólucro
   nasce `1px solid #fff` — branco sobre o cartão branco, some. Pintar só o
   `input` acima não resolvia; é o pai direto que precisa da cor. */
[data-testid="stTextInput"] div:has(> input),
[data-testid="stTextArea"] div:has(> textarea) {
  border: 1px solid var(--s200) !important;
  border-radius: 8px !important;
  background: #fff !important;
}
[data-testid="stTextInput"] div:has(> input:focus),
[data-testid="stTextArea"] div:has(> textarea:focus) {
  border-color: var(--roxo) !important;
  box-shadow: 0 0 0 3px rgba(123, 104, 238, .15) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--roxo) !important;
  box-shadow: 0 0 0 3px rgba(123, 104, 238, .15) !important;
}
label[data-testid="stWidgetLabel"] p {
  font-size: 12px !important; font-weight: 500; color: var(--s500);
}

/* Filtros do topo: largura fixa (150px). Um <select> esticado até o fim da
   coluna promete um texto longo que nunca vem — "Urgente", "Em Progresso" e um
   nome próprio cabem folgados em 150px, e o espaço que sobra volta para a busca
   e para o quadro. */
.st-key-filtro_prioridade, .st-key-filtro_resp {
  max-width: 150px;
}
/* Dentro dos modais (criar/editar) as seleções ficam em pares de colunas: aqui
   elas PRECISAM preencher a metade inteira, senão sobra um vão à direita de
   cada campo e o formulário fica desalinhado no modal largo. Sem teto, cada
   uma acompanha a sua coluna e os pares Status/Prioridade e Responsável/Data
   ficam simétricos. */
.st-key-criar_status, .st-key-criar_prioridade,
.st-key-criar_resp, .st-key-criar_data,
.st-key-edit_status, .st-key-edit_prioridade,
.st-key-edit_resp, .st-key-edit_data {
  max-width: 100%;
}

/* Abas = a barra de views do protótipo: pílula roxa no ativo, sem
   sublinhado. O tab-highlight do BaseWeb é justamente esse sublinhado,
   então some com ele em vez de recolorir. */
[data-baseweb="tab-list"] {
  gap: .25rem;
  background: #fff;
  border: 1px solid var(--s200);
  border-radius: 10px;
  padding: .25rem;
  margin-bottom: .75rem;
}
[data-baseweb="tab"] {
  border-radius: 6px;
  padding: .375rem .875rem !important;
  font-size: 12px !important; font-weight: 500;
  color: var(--s600);
  transition-property: background-color, color;
  transition-duration: 150ms;
}
[data-baseweb="tab"]:hover { background: var(--s100); }
[data-baseweb="tab"][aria-selected="true"] {
  background: var(--roxo-suave); color: var(--roxo) !important;
}
[data-baseweb="tab"][aria-selected="true"] p { color: var(--roxo) !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }

/* item de navegação fixo da sidebar (quando não há o que escolher) */
.nav-fixo {
  padding: .5rem .625rem; border-radius: 8px;
  background: var(--s100); color: var(--roxo);
  font-size: 12px; font-weight: 500;
}

/* rádio de navegação da sidebar vira lista de links */
[data-testid="stSidebar"] [role="radiogroup"] { gap: .125rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: .5rem .625rem; border-radius: 8px; min-height: 40px;
  font-size: 12px; font-weight: 500; color: var(--s600);
  transition-property: background-color, color;
  transition-duration: 120ms;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--s100); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: var(--s100); color: var(--roxo);
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }

[data-testid="stExpander"] {
  border: none; background: transparent; box-shadow: none;
}
[data-testid="stExpander"] summary { padding: .25rem .5rem; font-size: 12px; }

hr, [data-testid="stDivider"] { border-color: var(--s200); margin: .75rem 0; }

/* A regra de "linha ativa" da árvore é injetada em tempo de execução (só ali
   se sabe qual espaço está aberto). O <style> não desenha nada, mas o
   Streamlit ainda reserva o bloco de markdown em volta dele. */
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] style) {
  display: none;
}

/* O componente que grava o cookie de sessão não tem nada para mostrar.
   Colapsa o espaço em vez de `display:none` — um iframe escondido ainda
   executa, mas não vale arriscar o carregamento por causa de um vão. */
[data-testid="stElementContainer"]:has([data-testid="stCustomComponentV1"]),
[data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {
  height: 0 !important; min-height: 0 !important;
  margin: 0 !important; padding: 0 !important;
  overflow: hidden;
}

/* ------------------------------------------------------------------- login */

/* O cartão de 400x400. `min-height` e não `height`: a aba "Criar conta" tem
   quatro campos e precisa crescer — travar a altura só cortaria o botão. */
.st-key-login_card {
  width: 400px; max-width: calc(100vw - 2rem);
  min-height: 400px;
  margin: 6vh auto 0;
  background: #fff;
  border: 1px solid var(--s200);
  border-radius: 16px;
  padding: 1.75rem;
  box-shadow: 0 10px 15px -3px rgba(15, 23, 42, .06),
              0 4px 6px -4px rgba(15, 23, 42, .05);
  gap: .25rem;
}
/* A faixa roxa no topo amarra o cartão à marca sem pintar o fundo inteiro. */
.st-key-login_card::before {
  content: ""; position: absolute; inset: 0 0 auto 0; height: 3px;
  background: linear-gradient(to right, var(--roxo), var(--rosa));
  border-radius: 16px 16px 0 0;
}
.st-key-login_card { position: relative; }
.st-key-login_card [data-baseweb="tab-list"] { margin: .875rem 0 .25rem; }
.st-key-login_card .stForm { border: none; padding: 0; }
.st-key-login_card [data-testid="stElementContainer"] { margin-bottom: 0; }

.login-marca {
  display: flex; align-items: center; gap: .75rem;
}
.login-marca .ws-logo { width: 40px; height: 40px; font-size: 16px; border-radius: 12px; }
.login-titulo { font-size: 18px; font-weight: 700; color: var(--s900); margin: 0; line-height: 1.3; }
.login-sub    { font-size: 12px; color: var(--s500); margin: 0; text-wrap: pretty; }
/* O `margin-top: auto` vai no contêiner, não no <p>: quem é filho do flex do
   cartão é o contêiner de elemento, e só nele a margem automática empurra o
   aviso para o rodapé. Na aba Entrar sobrava um palmo de branco embaixo do
   botão; agora o texto ocupa essa folga. */
.st-key-login_card > [data-testid="stElementContainer"]:last-child {
  margin-top: auto;
}
/* O `-1rem` que o Streamlit põe em todo markdown deixaria o rodapé 16px mais
   perto da borda de baixo do que o cabeçalho está da de cima. */
.st-key-login_card > [data-testid="stElementContainer"]:last-child
  [data-testid="stMarkdownContainer"] {
  margin-bottom: 0 !important;
}
.login-rodape {
  margin: 0; padding-top: 1rem;
  font-size: 11px; color: var(--s400); text-align: center;
  text-wrap: pretty;
}
</style>
"""


def aplicar() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
