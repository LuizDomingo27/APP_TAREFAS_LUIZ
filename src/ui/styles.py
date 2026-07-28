"""CSS injetado — o sistema de design do app.

Direção: console de operações. Denso, silencioso, feito para ser lido todo
dia. Três decisões carregam o visual inteiro:

  1. A base é cinza-frio quase neutro, não roxa. O fundo não compete com nada.
  2. O roxo é reservado ao que é *clicável ou selecionado*. Se está roxo, você
     pode mexer.
  3. Cor saturada só aparece onde significa alguma coisa — status, prioridade,
     situação de prazo. Fora disso, a tela é acromática de propósito: um
     atraso em vermelho salta porque é a única coisa vermelha em volta.

Os seletores atacam os `data-testid` e as classes `st-key-*` do Streamlit, que
é o único gancho estável que ele expõe.

Regras de acabamento seguidas ao longo do arquivo:
  - raio concêntrico: raio externo = raio interno + padding
  - `transition-property` explícito (nunca `transition: all`)
  - `tabular-nums` em tudo que é contador
  - alvo de clique mínimo de 40px nos controles
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  /* Superfícies. A escada é curta de propósito — quatro degraus bastam para
     hierarquia, e mais do que isso vira sujeira em tela escura. */
  --bg-0: #0b0d12;   /* fundo da aplicação */
  --bg-1: #12151c;   /* painéis, sidebar, cartões, tabelas */
  --bg-2: #171b23;   /* elevado: campos, linha em hover */
  --bg-3: #1e232d;   /* topo: chip, hover sobre elevado */

  --linha:       #232833;   /* filete padrão */
  --linha-forte: #2f3542;   /* divisor que precisa ser visto */

  --txt-1: #e7e9ee;  /* título e dado principal */
  --txt-2: #99a0ad;  /* rótulo, apoio */
  --txt-3: #697080;  /* legenda, placeholder */

  /* Interativo. Um tom só, três intensidades. */
  --acento:       #7c6cf5;
  --acento-alto:  #9b8dff;
  --acento-fraco: rgba(124, 108, 245, .13);
  --acento-linha: rgba(124, 108, 245, .35);

  /* Semânticas — o único lugar da interface onde cor quer dizer algo. */
  --neutro: #8d95a3;
  --info:   #5b93f5;
  --alerta: #e0a34e;
  --ok:     #3fb98a;
  --erro:   #ef6461;

  --chip-neutro-bg: rgba(141, 149, 163, .14); --chip-neutro-tx: #b2b9c5;
  --chip-info-bg:   rgba(91, 147, 245, .15);  --chip-info-tx:   #8ab4fb;
  --chip-alerta-bg: rgba(224, 163, 78, .15);  --chip-alerta-tx: #e9bb72;
  --chip-ok-bg:     rgba(63, 185, 138, .15);  --chip-ok-tx:     #63d2a6;
  --chip-erro-bg:   rgba(239, 100, 97, .15);  --chip-erro-tx:   #f58a83;

  /* Em tela escura a sombra sozinha não separa nada — quem separa é o filete
     de luz na borda de cima. As duas andam juntas o arquivo inteiro. */
  --realce-topo: inset 0 1px 0 rgba(255, 255, 255, .04);
  --sombra-1: 0 1px 2px rgba(0, 0, 0, .4);
  --sombra-2: 0 10px 30px -12px rgba(0, 0, 0, .75);

  /* Compatibilidade: a sidebar injeta a regra de "linha ativa" em tempo de
     execução (só ali se sabe qual espaço está aberto) e cita estes nomes. */
  --roxo: var(--acento);
  --roxo-suave: var(--acento-fraco);
}

/* O tema escuro é fixado em .streamlit/config.toml; o `color-scheme` aqui é o
   par disso para o que o navegador desenha sozinho — barra de rolagem nativa,
   calendário do date_input, fundo de autopreenchimento. Sem ele, esses pedaços
   vinham claros dentro de uma tela escura. */
html {
  color-scheme: dark;
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
  background: var(--bg-2);
  border: 1px solid var(--linha);
  border-radius: 9999px;
  padding: .125rem .625rem .125rem .25rem;
  box-shadow: var(--sombra-1);
  font-size: 11px; font-weight: 500; color: var(--txt-2);
}

[data-testid="stAppViewContainer"] { background: var(--bg-0); }
[data-testid="stMain"] { background: var(--bg-0); }

.block-container {
  padding: 1.25rem 1.5rem 3rem;
  max-width: 100%;
}

/* barra de rolagem fina, no tom da tela */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2b313d; border-radius: 9999px; }
::-webkit-scrollbar-thumb:hover { background: #3a4150; }

/* Texto solto (st.markdown, st.caption, títulos de seção) — sem isto o
   Streamlit escurece o corpo em cima do fundo escuro. */
[data-testid="stMarkdownContainer"] { color: var(--txt-2); }
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] strong { color: var(--txt-1); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: var(--txt-3) !important;
}

/* O Streamlit declara `font-size: inherit` para todo <p> dentro de um bloco
   de markdown, com a especificidade de uma classe + um elemento (0,1,1). Um
   seletor de classe puro (`.painel-sub`) perde essa disputa e o parágrafo
   volta aos 16px herdados do contêiner — o que apagava metade da escala
   tipográfica do sistema. Repetir os nomes aqui, sob o `data-testid`, sobe
   para (0,2,2) e resolve sem `!important`.
   Todo <p> com classe própria do app precisa estar nesta lista. */
[data-testid="stMarkdownContainer"] p.painel-sub  { font-size: 12px; }
[data-testid="stMarkdownContainer"] p.secao-nota  { font-size: 12px; }
[data-testid="stMarkdownContainer"] p.login-titulo { font-size: 17px; }
[data-testid="stMarkdownContainer"] p.login-sub   { font-size: 12px; }
[data-testid="stMarkdownContainer"] p.login-rodape { font-size: 11px; }
[data-testid="stMarkdownContainer"] .pagina-topo p { font-size: 13px; }

/* ------------------------------------------------------------------- sidebar */

[data-testid="stSidebar"] {
  background: var(--bg-1);
  border-right: 1px solid var(--linha);
  width: 260px !important;
}
[data-testid="stSidebar"] > div { padding-top: 0; }
[data-testid="stSidebarContent"] { padding: 0 .75rem 1rem; }
[data-testid="stSidebarCollapseButton"] button { color: var(--txt-3); }

.ws-header {
  display: flex; align-items: center; gap: .625rem;
  padding: .875rem .25rem;
  border-bottom: 1px solid var(--linha);
  margin: 0 -.25rem .75rem;
}
/* A marca é o único lugar com preenchimento roxo cheio: um quadrado de 32px
   é pequeno o bastante para não puxar a tela para o roxo, e é o que ancora a
   identidade num layout que de resto é cinza. */
.ws-logo {
  width: 32px; height: 32px; border-radius: 9px;
  background: var(--acento);
  color: #fff; font-weight: 700; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ws-nome  { font-size: 13px; font-weight: 600; color: var(--txt-1); line-height: 1.2;
            letter-spacing: -.01em; }
.ws-plano { font-size: 11px; color: var(--txt-3); }

/* Espaçamento em `padding`, não em `margin`: o contêiner de elemento do
   Streamlit mede só a caixa de texto, então a margem vazava para fora dele
   e o botão seguinte subia por cima do título. */
.side-titulo {
  font-size: 10px; font-weight: 600; letter-spacing: .09em;
  text-transform: uppercase; color: var(--txt-3);
  margin: 0; padding: .875rem .25rem .375rem;
}

/* árvore de espaços */
.espaco-linha {
  display: flex; align-items: center; justify-content: space-between;
  padding: .375rem .5rem; border-radius: 6px;
  font-size: 12px; font-weight: 500; color: var(--txt-2);
}
.espaco-linha .ponto {
  width: 10px; height: 10px; border-radius: 50%;
  display: inline-block; flex-shrink: 0; margin-right: .5rem;
}
.espaco-linha .contador {
  font-size: 10px; color: var(--txt-3); font-weight: 400;
  font-variant-numeric: tabular-nums;
}
.lista-linha {
  display: flex; align-items: center; gap: .5rem;
  padding: .25rem .5rem .25rem 1.5rem; border-radius: 6px;
  font-size: 12px; font-weight: 500; color: var(--txt-3);
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
  border-radius: 6px; color: var(--txt-2);
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
.st-key-nav_arvore .stButton button:hover { background: var(--bg-2); color: var(--txt-1); }

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
  padding-left: 2.5rem; color: var(--txt-3);
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
  left: .5rem; width: 8px; height: 8px; border-radius: 50%;
}
.icone-lista {
  left: 1.25rem; color: var(--txt-3);
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
  border-top: 1px solid var(--linha);
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
  color: var(--txt-3); border-radius: 8px;
}
.st-key-rodape_perfil .stButton button:hover {
  background: var(--bg-2); color: var(--txt-1);
}
.st-key-rodape_perfil [data-testid="stIconMaterial"] { font-size: 18px; }
/* O bloco de texto vira flex-column para que o avatar centre contra as
   DUAS linhas juntas. Com os <div> soltos, o align-items do pai alinhava
   pela caixa de linha do primeiro filho e o avatar subia alguns pixels. */
.perfil-texto {
  display: flex; flex-direction: column; justify-content: center;
  min-width: 0;
}
.perfil-nome  { font-size: 12px; font-weight: 600; color: var(--txt-1); line-height: 1.35; }
.perfil-cargo { font-size: 10px; color: var(--txt-3); line-height: 1.35; }

/* O avatar é o contraponto quente da tela: fundo roxo translúcido com o
   filete cheio em volta, em vez do disco chapado. Numa lista de dez pessoas
   dez discos roxos sólidos viravam um enfeite; assim ele identifica sem
   gritar. */
.avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--acento-fraco);
  border: 1px solid var(--acento-linha);
  color: var(--acento-alto);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600; letter-spacing: .02em;
  flex-shrink: 0;
}
.avatar.mini {
  width: 20px; height: 20px; font-size: 9px;
}

/* ------------------------------------------------------------------- topo */

.topbar {
  background: var(--bg-1);
  border: 1px solid var(--linha);
  border-radius: 12px;
  padding: .75rem 1rem;
  margin-bottom: .75rem;
  box-shadow: var(--realce-topo);
}
.migalhas {
  display: flex; align-items: center; gap: .5rem;
  font-size: 12px; color: var(--txt-3);
}
.migalhas .sep   { color: var(--linha-forte); }
.migalhas .atual {
  font-weight: 600; color: var(--txt-1);
  display: inline-flex; align-items: center; gap: .375rem;
}
.migalhas .atual .ponto { width: 8px; height: 8px; border-radius: 50%; }

/* Cabeçalho de página — título e uma linha de contexto. Vale para o
   dashboard e para qualquer tela que precise se apresentar. */
.pagina-topo { margin-bottom: 1.125rem; }
.pagina-topo h1 {
  font-size: 20px; font-weight: 600; color: var(--txt-1);
  letter-spacing: -.02em; margin: 0 0 .25rem; padding: 0;
  line-height: 1.25;
}
.pagina-topo p {
  font-size: 13px; color: var(--txt-3); margin: 0;
  text-wrap: pretty; max-width: 68ch;
}

/* Título de seção dentro de uma página. O filete curto à esquerda é a única
   marca decorativa do sistema, e é o que amarra as seções entre si. */
.secao {
  display: flex; align-items: center; gap: .5rem;
  font-size: 13px; font-weight: 600; color: var(--txt-1);
  letter-spacing: -.01em;
  margin: 0 0 .625rem; padding: 0;
}
.secao::before {
  content: ""; flex-shrink: 0;
  width: 2px; height: 13px; border-radius: 9999px;
  background: var(--acento);
}
.secao-nota {
  font-size: 12px; color: var(--txt-3); margin: -.25rem 0 .875rem;
  text-wrap: pretty; max-width: 72ch;
}

/* ------------------------------------------------------------------- kanban */

.col-topo {
  display: flex; align-items: center; gap: .5rem;
  padding: 0 .25rem .625rem;
}
.col-topo .ponto { width: 8px; height: 8px; border-radius: 50%; }
.col-topo h3 {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .07em; color: var(--txt-2); margin: 0;
}
.col-topo .contador {
  border-radius: 9999px; padding: .1rem .5rem;
  font-size: 10px; font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* coluna: raio 12px = raio do card (8px) + padding (4px)… arredondado
   para 12/8, que é o par do protótipo (rounded-xl sobre rounded-lg).
   `.coluna` é a versão em HTML puro; `.st-key-coluna_N` é o container
   Streamlit que a substituiu quando os cards ganharam botão. */
.coluna,
[class*="st-key-coluna_"] {
  background: rgba(255, 255, 255, .018);
  border: 1px solid var(--linha);
  border-radius: 12px;
  padding: .75rem;
  min-height: 180px;
}
[class*="st-key-coluna_"] { gap: .625rem; }

/* Card clicável: o container É o card — moldura, sombra e âncora de
   posicionamento — e o botão que veio depois é esticado por cima. Com a
   caixa aqui e não num <div> do markdown, o seletor de status também cai
   dentro dela. O rótulo do botão continua no DOM (é o título da tarefa,
   para leitor de tela), só que sem tamanho. */
[class*="st-key-card_"] {
  position: relative;
  background: var(--bg-2);
  border: 1px solid var(--linha);
  border-radius: 8px;
  padding: .75rem;
  box-shadow: var(--realce-topo);
  gap: 0;
  transition-property: background-color, border-color, transform;
  transition-duration: 140ms;
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
  background: transparent;
}
[class*="st-key-card_"]:hover {
  background: var(--bg-3);
  border-color: var(--acento-linha);
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
  background: var(--bg-1) !important;
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

/* A lista suspensa nasce clara se o BaseWeb não for corrigido à mão. */
[data-testid="stSelectboxVirtualDropdown"],
[data-baseweb="popover"] [role="listbox"] {
  background: var(--bg-2) !important;
  border: 1px solid var(--linha-forte);
  border-radius: 10px;
  box-shadow: var(--sombra-2);
}
[data-baseweb="popover"] [role="option"] { color: var(--txt-2) !important; }
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"] {
  background: var(--bg-3) !important; color: var(--txt-1) !important;
}

/* -------------------------------------------------------- modal de detalhe */

/* O `width` do `st.dialog` sozinho não serve: mesmo no "small" o Streamlit
   dimensiona por porcentagem da viewport, então numa tela larga o formulário
   esticava até quase a borda. */
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
  background: var(--bg-1) !important;
  border: 1px solid var(--linha-forte);
  border-radius: 14px;
  box-shadow: var(--sombra-2);
}

/* Modal compacto: o espaçamento padrão do Streamlit é pensado para uma
   página inteira, e dentro do modal ele dobra a altura do formulário. */
[data-testid="stDialog"] [data-testid="stVerticalBlock"] { gap: .5rem; }
[data-testid="stDialog"] [data-testid="stElementContainer"] { margin-bottom: 0; }
[data-testid="stDialog"] hr,
[data-testid="stDialog"] [data-testid="stDivider"] { margin: .375rem 0; }
[data-testid="stDialog"] [data-testid="stTextArea"] textarea { min-height: 72px; }
[data-testid="stDialog"] label[data-testid="stWidgetLabel"] { margin-bottom: .125rem; }

/* Excluir é destrutivo e o botão diz isso: vermelho contido, sem
   preenchimento. A confirmação já é em dois passos, então o gatilho não
   precisa gritar — precisa ser inconfundível.
   O "Sim, excluir" nasce `primary` (roxo cheio); aqui ele também vira o
   vermelho, para os dois botões falarem a mesma língua. */
.st-key-btn_excluir button,
.st-key-btn_confirmar_exclusao button {
  background: var(--chip-erro-bg) !important;
  color: var(--chip-erro-tx) !important;
  border: 1px solid rgba(239, 100, 97, .35) !important;
  box-shadow: none !important;
  transition-property: background-color, border-color;
  transition-duration: 150ms;
}
.st-key-btn_excluir button:hover,
.st-key-btn_confirmar_exclusao button:hover {
  background: rgba(239, 100, 97, .22) !important;
  border-color: var(--erro) !important;
}
.st-key-btn_excluir button p,
.st-key-btn_confirmar_exclusao button p { color: var(--chip-erro-tx) !important; }

.detalhe-codigo {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 11px; color: var(--txt-3); letter-spacing: .06em;
  margin-bottom: .25rem;
}
.secao-titulo {
  display: flex; align-items: center; gap: .5rem;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .07em; color: var(--txt-2);
  margin-bottom: .5rem;
}
.contador-simples {
  font-size: 10px; font-weight: 600; color: var(--txt-2);
  background: var(--bg-3); border-radius: 9999px; padding: .1rem .45rem;
  font-variant-numeric: tabular-nums;
}
.comentario { display: flex; gap: .5rem; padding: .25rem 0; }
.comentario-topo {
  font-size: 11px; font-weight: 600; color: var(--txt-1);
  display: flex; align-items: baseline; gap: .5rem;
}
.comentario-data { font-size: 10px; font-weight: 400; color: var(--txt-3); }
.comentario-texto {
  font-size: 12px; color: var(--txt-2); line-height: 1.55;
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
  font-size: 10px; font-weight: 500; color: var(--txt-3);
  font-variant-numeric: tabular-nums; letter-spacing: .04em;
}
[class*="st-key-card_"] h4 {
  font-size: 12.5px; font-weight: 600; color: var(--txt-1);
  line-height: 1.45; margin: 0 0 .5rem; padding: 0;
  text-wrap: pretty;
}
.card-rodape {
  display: flex; align-items: center; justify-content: space-between;
  padding-top: .5rem; margin-top: .75rem;
  border-top: 1px solid var(--linha);
  font-size: 11px; color: var(--txt-3);
  font-variant-numeric: tabular-nums;
}
.card-rodape .meta { display: flex; align-items: center; gap: .625rem; }
.meta-item { display: inline-flex; align-items: center; gap: .25rem; }

/* Prioridade: texto colorido sobre fundo translúcido da mesma família. Em
   tela escura, pastel chapado (o que o tema claro usava) some — o que lê é o
   texto saturado. */
.badge {
  display: inline-flex; align-items: center; gap: .25rem;
  font-size: 10px; font-weight: 600;
  padding: .15rem .5rem; border-radius: 5px;
  white-space: nowrap; letter-spacing: .01em;
}
.badge.urgente { background: var(--chip-erro-bg);   color: var(--chip-erro-tx); }
.badge.alta    { background: var(--chip-alerta-bg); color: var(--chip-alerta-tx); }
.badge.normal  { background: var(--chip-info-bg);   color: var(--chip-info-tx); }
.badge.baixa   { background: var(--chip-neutro-bg); color: var(--chip-neutro-tx); }

.vazio {
  text-align: center; color: var(--txt-3);
  font-size: 11px; padding: 1.25rem .5rem;
  border: 1px dashed var(--linha-forte); border-radius: 8px;
}

/* ---------------------------------------------------------------- indicadores */

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}
@media (max-width: 1100px) {
  .kpi-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

/* Sem borda-esquerda grossa e sem faixa em gradiente: o acento é um ponto de
   6px ao lado do rótulo. Quatro cartões lado a lado com uma barra colorida
   cada viravam um semáforo — o ponto dá a mesma leitura por um centésimo da
   tinta. */
.kpi-card {
  position: relative;
  background: var(--bg-1);
  border: 1px solid var(--linha);
  border-radius: 12px;
  padding: 14px 16px 15px;
  box-shadow: var(--realce-topo);
  transition-property: border-color, background-color;
  transition-duration: 160ms;
  min-width: 0;
}
.kpi-card:hover { border-color: var(--linha-forte); background: var(--bg-2); }

.kpi-label {
  display: flex; align-items: center; gap: .4rem;
  font-size: 10.5px; font-weight: 600;
  color: var(--txt-3);
  text-transform: uppercase; letter-spacing: .08em;
  margin-bottom: 10px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kpi-label::before {
  content: ""; flex-shrink: 0;
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--kpi-accent, var(--acento));
}

.kpi-value {
  font-size: 26px; font-weight: 600;
  color: var(--txt-1);
  line-height: 1.05; margin-bottom: 6px;
  letter-spacing: -.03em;
  font-variant-numeric: tabular-nums;
}
.kpi-value .unidade {
  font-size: 13px; font-weight: 500; color: var(--txt-3);
  letter-spacing: 0; margin-left: .18em;
}

.kpi-delta {
  font-size: 11px; font-weight: 500; color: var(--txt-3);
  font-variant-numeric: tabular-nums;
}
.kpi-delta--positive { color: var(--chip-ok-tx); }
.kpi-delta--negative { color: var(--chip-erro-tx); }
.kpi-delta--warning  { color: var(--chip-alerta-tx); }

/* ------------------------------------------------------------------- tabela */

/* Uma tabela de operação é lida de cima para baixo, procurando uma linha.
   Todo o desenho serve a isso: filete quase invisível entre linhas, zebra
   fraquíssima para dar o trilho horizontal, e a linha sob o cursor subindo
   um degrau de superfície. Sem borda vertical nenhuma — coluna se separa
   por alinhamento e espaço, não por traço. */
.tabela-wrap {
  background: var(--bg-1);
  border: 1px solid var(--linha);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: var(--realce-topo), var(--sombra-2);
}

.tabela-topo {
  padding: .875rem 1.25rem;
  border-bottom: 1px solid var(--linha);
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
}
.tabela-topo > span:first-child {
  font-size: 13px; font-weight: 600; color: var(--txt-1);
  letter-spacing: -.01em;
  display: inline-flex; align-items: center; gap: .5rem;
}
.tabela-topo > span:first-child::before {
  content: ""; display: inline-block; flex-shrink: 0;
  width: 2px; height: 13px; border-radius: 9999px;
  background: var(--acento);
}
.tabela-topo span.sub {
  font-size: 11px; font-weight: 500; color: var(--txt-3);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* Resumo de status acima da tabela: quatro contadores discretos, sem pílula
   colorida — o ponto já diz de qual status é. */
.tabela-resumo {
  display: flex; align-items: center; flex-wrap: wrap; gap: 1.25rem;
  padding: .625rem 1.25rem; border-bottom: 1px solid var(--linha);
  background: rgba(255, 255, 255, .012);
}
.tabela-resumo-item {
  display: inline-flex; align-items: center; gap: .4rem;
  font-size: 11.5px; font-weight: 500; color: var(--txt-3);
  font-variant-numeric: tabular-nums;
}
.tabela-resumo-item .ponto-mini {
  width: 6px; height: 6px; border-radius: 50%;
  display: inline-block; flex-shrink: 0;
}
.tabela-resumo-item strong {
  font-weight: 600; color: var(--txt-1); margin-left: .1rem;
}

table.tarefas {
  width: 100%; border-collapse: separate; border-spacing: 0;
  font-size: 13px; color: var(--txt-2); text-align: left;
}

/* O Streamlit estiliza toda tabela nascida de markdown com uma borda de 1px
   nos QUATRO lados de cada célula — e é dali que a nossa também nasce. Sem
   este reset a tabela vinha em grade, com um filete vertical entre cada par
   de colunas; a regra de `border-bottom` sozinha não desfazia os outros três.
   Coluna aqui se separa por alinhamento e espaço, não por traço. */
table.tarefas th, table.tarefas td { border: none; }

table.tarefas thead { position: sticky; top: 0; z-index: 1; }
table.tarefas thead tr { background: var(--bg-2); }
table.tarefas th {
  padding: .7rem 1rem;
  font-size: 10.5px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .08em;
  color: var(--txt-3);
  border-bottom: 1px solid var(--linha);
  white-space: nowrap;
}
table.tarefas th:first-child { padding-left: 1.25rem; }
table.tarefas th:last-child  { padding-right: 1.25rem; }

/* Linhas altas: 14px em cima e embaixo dão os ~46px de altura que deixam a
   varredura confortável sem virar lista de cartões. */
table.tarefas td {
  padding: .875rem 1rem;
  border-bottom: 1px solid var(--linha);
  vertical-align: middle;
}
table.tarefas td:first-child { padding-left: 1.25rem; }
table.tarefas td:last-child  { padding-right: 1.25rem; }

table.tarefas tbody tr {
  transition-property: background-color;
  transition-duration: 120ms;
}
table.tarefas tbody tr:nth-child(even) { background: rgba(255, 255, 255, .014); }
table.tarefas tbody tr:hover { background: var(--bg-2); }
table.tarefas tbody tr:last-child td { border-bottom: none; }

/* Célula do nome — o dado que a pessoa está procurando. */
table.tarefas td.nome {
  font-weight: 500; color: var(--txt-1);
  line-height: 1.45;
  max-width: 380px;
}
table.tarefas td.nome .card-codigo {
  display: inline-block;
  padding: .1rem .35rem; margin-right: .45rem;
  background: var(--bg-3); border-radius: 4px;
  color: var(--txt-3);
  vertical-align: middle;
}

table.tarefas td.data {
  font-variant-numeric: tabular-nums;
  font-size: 12.5px; font-weight: 500;
  color: var(--txt-2);
  white-space: nowrap;
}

/* Número em destaque dentro de texto corrido (rodapés, resumos). */
.numero-destaque {
  font-weight: 600; color: var(--txt-1);
  font-variant-numeric: tabular-nums;
}

/* Checkbox de conclusão */
.check {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px;
  border: 1.5px solid var(--linha-forte); border-radius: 5px;
  vertical-align: middle;
  transition-property: border-color;
  transition-duration: 140ms;
}
table.tarefas tbody tr:hover .check { border-color: var(--acento-linha); }
.check.feito {
  border: none; width: auto; height: auto;
  color: var(--ok); background: none;
}

/* Pílula de status: fundo translúcido + ponto. É a mesma linguagem do resumo
   e do Kanban, então status se reconhece pela cor em qualquer tela. */
.pill-status {
  display: inline-flex; align-items: center; gap: .4rem;
  font-size: 11px; font-weight: 600;
  padding: .22rem .6rem;
  border-radius: 9999px;
  white-space: nowrap;
  letter-spacing: .01em;
}
.pill-status::before {
  content: ""; display: inline-block;
  width: 5px; height: 5px; border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.pill-status[data-status="afazer"]      { background: var(--chip-neutro-bg); color: var(--chip-neutro-tx); }
.pill-status[data-status="emprogresso"] { background: var(--chip-info-bg);   color: var(--chip-info-tx); }
.pill-status[data-status="emrevisao"]   { background: var(--chip-alerta-bg); color: var(--chip-alerta-tx); }
.pill-status[data-status="concluido"]   { background: var(--chip-ok-bg);     color: var(--chip-ok-tx); }

/* Atraso: o único elemento animado da tela, e por isso o que o olho acha
   primeiro numa lista longa. Respeita quem pediu menos movimento. */
.data-atrasada {
  color: var(--chip-erro-tx) !important; font-weight: 600;
  display: inline-flex; align-items: center; gap: .4rem;
}
.data-atrasada::before {
  content: ""; display: inline-block;
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--erro);
  animation: pulso-atraso 1.8s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes pulso-atraso {
  0%, 100% { opacity: 1; }
  50%      { opacity: .3; }
}
@media (prefers-reduced-motion: reduce) {
  .data-atrasada::before { animation: none; }
}

.responsavel-cell {
  display: inline-flex; align-items: center; gap: .5rem;
  font-size: 12.5px; font-weight: 500; color: var(--txt-2);
  white-space: nowrap;
}
.responsavel-cell.sem { color: var(--txt-3); font-weight: 400; }

.tag {
  display: inline-flex; align-items: center;
  background: var(--bg-3);
  color: var(--txt-2);
  font-size: 10.5px; font-weight: 500;
  padding: .15rem .5rem; border-radius: 5px;
  border: 1px solid var(--linha);
  white-space: nowrap;
  transition-property: border-color, color;
  transition-duration: 140ms;
}
.tag:hover { border-color: var(--acento-linha); color: var(--acento-alto); }
.tags-cell { display: flex; flex-wrap: wrap; gap: .25rem; }

.tabela-rodape {
  padding: .75rem 1.25rem;
  border-top: 1px solid var(--linha);
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  font-size: 12px; color: var(--txt-3);
  font-variant-numeric: tabular-nums;
}
.tabela-rodape .concluidas {
  display: inline-flex; align-items: center; gap: .625rem;
}
.tabela-rodape .barra-progresso {
  width: 96px; height: 4px; border-radius: 9999px;
  background: var(--bg-3); overflow: hidden;
}
.tabela-rodape .barra-progresso-fill {
  display: block; height: 100%; border-radius: 9999px;
  background: var(--ok);
  transition-property: width;
  transition-duration: 320ms;
}

/* Barra de progresso inline, usada nas tabelas do dashboard. */
.progresso {
  display: flex; align-items: center; gap: .625rem;
  min-width: 130px;
}
.progresso-trilho {
  flex: 1; height: 4px; border-radius: 9999px;
  background: var(--bg-3); overflow: hidden;
}
.progresso-fill { display: block; height: 100%; background: var(--ok); }
.progresso-num {
  font-size: 11.5px; font-weight: 600; color: var(--txt-2);
  min-width: 38px; text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ------------------------------------------------------------------ equipe */

/* A tela de Equipe é um formulário de administração, não um painel de dados:
   linha de leitura curta lê melhor que a largura toda. 1080px é o teto e 80%
   é a proporção pedida — o que for menor vence, então em telas médias ela
   respira e em telas largas não vira uma faixa perdida no meio. */
.st-key-pagina_usuarios {
  width: min(80%, 1080px);
  margin-inline: auto;
}
@media (max-width: 900px) {
  .st-key-pagina_usuarios { width: 100%; }
}

/* Painel sobre o fundo — mesma moldura da tabela e da topbar, para a tela de
   Equipe não parecer de outro app. */
[class*="st-key-painel_"] {
  background: var(--bg-1);
  border: 1px solid var(--linha);
  border-radius: 14px;
  padding: 1.125rem 1.25rem 1.25rem;
  box-shadow: var(--realce-topo);
  margin-bottom: .875rem;
  gap: 0;
}
.painel-topo {
  display: flex; align-items: center; gap: .5rem;
  margin-bottom: .125rem;
}
.painel-topo h3 {
  font-size: 13px; font-weight: 600; color: var(--txt-1);
  letter-spacing: -.01em;
  margin: 0; padding: 0;
}
.painel-sub {
  font-size: 12px; color: var(--txt-3); margin: 0 0 .625rem;
  text-wrap: pretty; max-width: 70ch;
}

/* Uma linha por pessoa, lida como tabela: filete acima de cada uma — o
   primeiro fica logo abaixo do título e serve de régua de cabeçalho.
   Não dá para reservar o filete só para "linha depois de linha": o Streamlit
   embrulha cada container num <div> próprio, então as linhas nunca são
   irmãs e o seletor `+` não casaria nunca. */
[class*="st-key-linha_"], [class*="st-key-conv_linha_"] {
  padding: .5rem .75rem;
  margin: 0 -.75rem;
  border-top: 1px solid var(--linha);
  gap: 0;
  transition-property: background-color;
  transition-duration: 120ms;
}
[class*="st-key-linha_"]:hover, [class*="st-key-conv_linha_"]:hover {
  background: var(--bg-2);
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
  font-size: 13px; font-weight: 600; color: var(--txt-1); line-height: 1.35;
  display: flex; align-items: center; gap: .375rem;
}
.pessoa-email {
  font-size: 11.5px; color: var(--txt-3); line-height: 1.35;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.pessoa-quando {
  font-size: 11.5px; color: var(--txt-3);
  font-variant-numeric: tabular-nums;
}

.selo-voce, .selo-gestor {
  font-size: 9px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .07em; padding: .1rem .375rem; border-radius: 4px;
}
.selo-voce   { background: var(--bg-3); color: var(--txt-3); }
.selo-gestor { background: var(--acento-fraco); color: var(--acento-alto); }

.convite-linha { display: flex; align-items: center; gap: .5rem; }
.convite-email {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 12px; color: var(--txt-2);
}

/* O toggle vem com o rótulo "Gestor" à direita; em 13px ele briga com o nome
   da pessoa, então volta ao peso de legenda. */
[class*="st-key-linha_"] label[data-testid="stWidgetLabel"] p {
  font-size: 11px !important; color: var(--txt-3);
}

/* --------------------------------------------------------------- controles */

/* Descendente, não filho direto: quando o botão tem `help=`, o Streamlit o
   embrulha em dois <span> de tooltip e o `>` deixa de casar. */
.stButton button, .stFormSubmitButton button {
  border-radius: 8px;
  border: 1px solid var(--linha-forte);
  background: var(--bg-2);
  color: var(--txt-2);
  font-size: 12px; font-weight: 500;
  min-height: 40px;                      /* alvo de clique confortável */
  box-shadow: none;
  transition-property: background-color, border-color, color;
  transition-duration: 150ms;
  transition-timing-function: ease-out;
}
.stButton button p, .stFormSubmitButton button p { color: inherit; }
.stButton button:hover, .stFormSubmitButton button:hover {
  border-color: var(--acento-linha);
  color: var(--txt-1);
  background: var(--bg-3);
}
.stButton button:active, .stFormSubmitButton button:active {
  transform: scale(.985);
}
.stButton button:disabled, .stFormSubmitButton button:disabled {
  opacity: .45;
}
/* dentro de um st.form o `kind` vira "primaryFormSubmit", daí o ^= */
.stButton button[kind^="primary"], .stFormSubmitButton button[kind^="primary"] {
  background: var(--acento); border-color: var(--acento); color: #fff;
  font-weight: 600;
}
.stButton button[kind^="primary"] p, .stFormSubmitButton button[kind^="primary"] p {
  color: #fff;
}
.stButton button[kind^="primary"]:hover, .stFormSubmitButton button[kind^="primary"]:hover {
  background: var(--acento-alto); border-color: var(--acento-alto); color: #fff;
}
.stButton button:focus-visible, .stFormSubmitButton button:focus-visible {
  outline: 2px solid var(--acento-alto); outline-offset: 2px;
}

/* campos */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div {
  border-radius: 8px !important;
  background: var(--bg-2) !important;
  color: var(--txt-1) !important;
  font-size: 13px !important;
  min-height: 40px;
}
/* A borda visível dos campos mora no <div> que embrulha o <input>, não no
   <input> (que tem border-width 0). Nesta versão do Streamlit esse invólucro
   nasce com a cor do tema, que some contra a superfície. Pintar só o `input`
   não resolvia; é o pai direto que precisa da cor. */
[data-testid="stTextInput"] div:has(> input),
[data-testid="stTextArea"] div:has(> textarea) {
  border: 1px solid var(--linha-forte) !important;
  border-radius: 8px !important;
  background: var(--bg-2) !important;
}
[data-testid="stTextInput"] div:has(> input:focus),
[data-testid="stTextArea"] div:has(> textarea:focus) {
  border-color: var(--acento) !important;
  box-shadow: 0 0 0 3px var(--acento-fraco) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  box-shadow: none !important;
}
[data-baseweb="select"] > div {
  border-color: var(--linha-forte) !important;
}
[data-baseweb="select"] > div:hover { border-color: var(--acento-linha) !important; }
input::placeholder, textarea::placeholder { color: var(--txt-3) !important; }

label[data-testid="stWidgetLabel"] p {
  font-size: 11.5px !important; font-weight: 500; color: var(--txt-3);
}

/* Multiselect e date_input seguem o mesmo tom das outras superfícies. */
[data-baseweb="tag"] {
  background: var(--acento-fraco) !important;
  color: var(--acento-alto) !important;
  border-radius: 5px !important;
}
[data-testid="stDateInput"] input { color: var(--txt-1) !important; }

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

/* Abas = a barra de views: pílula no ativo, sem sublinhado. O tab-highlight
   do BaseWeb é justamente esse sublinhado, então some com ele em vez de
   recolorir. */
[data-baseweb="tab-list"] {
  gap: .125rem;
  background: var(--bg-1);
  border: 1px solid var(--linha);
  border-radius: 10px;
  padding: .25rem;
  margin-bottom: .875rem;
  flex-wrap: wrap;
}
[data-baseweb="tab"] {
  border-radius: 7px;
  padding: .4rem .875rem !important;
  font-size: 12px !important; font-weight: 500;
  color: var(--txt-3);
  transition-property: background-color, color;
  transition-duration: 150ms;
}
[data-baseweb="tab"] p { color: inherit !important; font-size: 12px !important; }
[data-baseweb="tab"]:hover { background: var(--bg-2); color: var(--txt-1); }
[data-baseweb="tab"][aria-selected="true"] {
  background: var(--acento-fraco); color: var(--acento-alto) !important;
}
[data-baseweb="tab"][aria-selected="true"] p { color: var(--acento-alto) !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }

/* item de navegação fixo da sidebar (quando não há o que escolher) */
.nav-fixo {
  padding: .5rem .625rem; border-radius: 8px;
  background: var(--acento-fraco); color: var(--acento-alto);
  font-size: 12px; font-weight: 500;
}

/* rádio de navegação da sidebar vira lista de links */
[data-testid="stSidebar"] [role="radiogroup"] { gap: .125rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: .5rem .625rem; border-radius: 8px; min-height: 40px;
  font-size: 12px; font-weight: 500; color: var(--txt-2);
  transition-property: background-color, color;
  transition-duration: 120ms;
}
[data-testid="stSidebar"] [role="radiogroup"] label p { color: inherit !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--bg-2); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: var(--acento-fraco); color: var(--acento-alto);
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }

[data-testid="stExpander"] {
  border: 1px solid var(--linha); background: var(--bg-1);
  border-radius: 12px; box-shadow: none;
}
[data-testid="stExpander"] summary {
  padding: .625rem .875rem; font-size: 12px; color: var(--txt-2);
}
[data-testid="stExpander"] summary:hover { color: var(--txt-1); }

hr, [data-testid="stDivider"] { border-color: var(--linha); margin: 1rem 0; }

/* Avisos do Streamlit no tom da interface — o padrão vem com pastel claro. */
[data-testid="stAlert"] {
  background: var(--bg-2) !important;
  border: 1px solid var(--linha-forte);
  border-radius: 10px;
  color: var(--txt-2);
}
[data-testid="stAlert"] p { color: var(--txt-2) !important; font-size: 13px; }
[data-testid="stAlertContentInfo"]    { border-left: 2px solid var(--info); }
[data-testid="stAlertContentSuccess"] { border-left: 2px solid var(--ok); }
[data-testid="stAlertContentWarning"] { border-left: 2px solid var(--alerta); }
[data-testid="stAlertContentError"]   { border-left: 2px solid var(--erro); }

[data-testid="stToast"] {
  background: var(--bg-3) !important;
  border: 1px solid var(--linha-forte);
  color: var(--txt-1);
}

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

/* O login é a única tela sem sidebar, sem dados e sem pressa: é onde o app
   pode se apresentar. O cartão ganha um brilho de acento no canto superior
   esquerdo — um foco de luz, não um gradiente de ponta a ponta — e é o único
   lugar do sistema com esse tratamento, justamente para não virar maneirismo.
   `min-height` e não `height`: a aba "Criar conta" tem quatro campos e
   precisa crescer — travar a altura só cortaria o botão. */
.st-key-login_card {
  position: relative;
  width: 400px; max-width: calc(100vw - 2rem);
  min-height: 408px;
  margin: 8vh auto 0;
  background:
    radial-gradient(120% 90% at 0% 0%, rgba(124, 108, 245, .16) 0%, rgba(124, 108, 245, 0) 58%),
    var(--bg-1);
  border: 1px solid var(--linha-forte);
  border-radius: 16px;
  padding: 1.75rem;
  box-shadow: var(--realce-topo), 0 24px 60px -24px rgba(0, 0, 0, .9);
  gap: .25rem;
}
.st-key-login_card [data-baseweb="tab-list"] {
  margin: 1.125rem 0 .25rem;
  background: transparent; border: none; padding: 0; gap: .25rem;
}
.st-key-login_card .stForm { border: none; padding: 0; }
.st-key-login_card [data-testid="stElementContainer"] { margin-bottom: 0; }

/* Campos do login em traço, não em caixa: com duas entradas e nada em volta,
   a moldura completa pesa mais do que ajuda. O rótulo fica acima, minúsculo,
   e o foco acende a linha de baixo.

   O traço mora no `[data-baseweb="input"]`, e não no `div:has(> input)` que o
   resto do arquivo usa: no campo de senha o botão do olho é irmão do input
   dentro de um `base-input` mais estreito, então a linha da senha ficava 14px
   mais curta que a do e-mail. O `input` é o invólucro externo dos dois casos e
   tem sempre a largura da coluna. */
.st-key-login_card [data-testid="stTextInput"] [data-baseweb="input"] {
  border: none !important;
  border-bottom: 1px solid var(--linha-forte) !important;
  border-radius: 0 !important;
  background: transparent !important;
  transition-property: border-color;
  transition-duration: 160ms;
}
.st-key-login_card [data-testid="stTextInput"] [data-baseweb="base-input"] {
  border: none !important;
  background: transparent !important;
}
.st-key-login_card [data-testid="stTextInput"] [data-baseweb="input"]:has(input:focus) {
  border-bottom-color: var(--acento) !important;
  box-shadow: none !important;
}
.st-key-login_card [data-testid="stTextInput"] input {
  background: transparent !important;
  padding-left: 0 !important;
}
.st-key-login_card label[data-testid="stWidgetLabel"] p {
  font-size: 10.5px !important; font-weight: 600;
  letter-spacing: .07em; text-transform: uppercase;
  color: var(--txt-3);
}
/* O submit vira a pílula larga do topo da hierarquia da tela. */
.st-key-login_card .stFormSubmitButton button {
  border-radius: 9999px;
  min-height: 44px;
  margin-top: .875rem;
  font-size: 12px; font-weight: 600;
  letter-spacing: .04em; text-transform: uppercase;
}

.login-marca { display: flex; align-items: center; gap: .75rem; }
.login-marca .ws-logo { width: 38px; height: 38px; font-size: 15px; border-radius: 11px; }
.login-titulo {
  font-size: 17px; font-weight: 600; color: var(--txt-1);
  margin: 0; line-height: 1.3; letter-spacing: -.02em;
}
.login-sub { font-size: 12px; color: var(--txt-3); margin: 0; text-wrap: pretty; }
/* O `margin-top: auto` vai no contêiner, não no <p>: quem é filho do flex do
   cartão é o contêiner de elemento, e só nele a margem automática empurra o
   aviso para o rodapé. Na aba Entrar sobrava um palmo de vazio embaixo do
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
  margin: 0; padding-top: 1.125rem;
  font-size: 11px; color: var(--txt-3); text-align: center;
  text-wrap: pretty;
}
</style>
"""


def aplicar() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
