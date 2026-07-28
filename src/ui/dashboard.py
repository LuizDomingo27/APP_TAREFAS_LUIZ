"""Dashboard e Gráficos de Monitoramento de Entregas por Projetos e Usuários com Apache ECharts."""

from __future__ import annotations

from datetime import timedelta
import json
import logging
import streamlit as st
import streamlit.components.v1 as components

from src.models import Perfil, Status, Prioridade, CORES_PRIORIDADE
from src.prazos import (
    calcular_dias_em_andamento,
    calcular_prazo,
    esta_critica,
    hoje as data_de_hoje,
    para_data,
)
from src.repo import catalog, tasks
from src.ui.componentes import avatar, data_longa, esc, icone, limpar

logger = logging.getLogger(__name__)

# Paleta de Cores do Sistema
CORES_STATUS = {
    "A Fazer": "#94a3b8",      # Slate 400
    "Em Progresso": "#3b82f6",  # Blue 500
    "Em Revisão": "#f59e0b",    # Amber 500
    "Concluído": "#10b981",     # Emerald 500
}

CORES_PRIO = {
    "Urgente": "#ef4444",
    "Alta": "#f59e0b",
    "Normal": "#3b82f6",
    "Baixa": "#64748b",
}


# Cor de cada selo da coluna "Situação do Prazo". Era uma escada de ternários
# que só cobria três classes: "alerta" (entrega fora do prazo) caía no cinza
# do `else` e ficava indistinguível de "Sem data limite". Dicionário para que
# uma classe nova apareça errada de um jeito óbvio, não invisível.
ESTILO_BADGE_PRAZO = {
    "urgente": "background:#fee2e2; color:#dc2626;",    # pendente e vencida
    "alerta": "background:#ffedd5; color:#c2410c;",     # entregue com atraso
    "alta": "background:#fef3c7; color:#d97706;",       # vence em breve
    "concluido": "background:#d1fae5; color:#059669;",  # entregue no prazo
    "normal": "background:#f1f5f9; color:#475569;",     # sem urgência
}


def _estilo_badge(badge_class: str) -> str:
    return ESTILO_BADGE_PRAZO.get(badge_class, ESTILO_BADGE_PRAZO["normal"])


def _render_echart_html(js_code: str, height: int = 400) -> None:
    """Renderiza um gráfico Apache ECharts via CDN com estilo moderno e tooltips em dark glassmorphism."""
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            html, body {{
                margin: 0; padding: 0; width: 100%; height: 100%;
                background: transparent; overflow: hidden;
                font-family: 'Inter', -apple-system, sans-serif;
            }}
            #chart-container {{
                width: 100%; height: {height - 6}px;
            }}
        </style>
    </head>
    <body>
        <div id="chart-container"></div>
        <script>
            var container = document.getElementById('chart-container');
            var chart = echarts.init(container, null, {{renderer: 'canvas'}});
            {js_code}
            chart.setOption(option);
            window.addEventListener('resize', function() {{ chart.resize(); }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=False)


def render(eu: Perfil) -> None:
    """Renderiza a página completa do Dashboard de Gráficos."""
    st.markdown(
        '<h2 style="font-weight:700; color:#0f172a; margin-bottom:0.25rem;">📊 Painel de Indicadores e Entregas</h2>'
        '<p style="color:#64748b; font-size:13px; margin-bottom:1.25rem;">'
        "Monitoramento visual de prazos, entregas por projetos e situação por integrante da equipe."
        "</p>",
        unsafe_allow_html=True,
    )

    try:
        todas_tarefas = tasks.listar()
        perfis = catalog.listar_perfis()
        espacos = catalog.espacos()
        listas = catalog.listas()
    except Exception as exc:
        logger.exception("Erro ao carregar dados do banco no Dashboard.")
        st.error(f"Erro ao carregar os indicadores do banco de dados: {exc}")
        return

    # Data no fuso da equipe, não no do servidor: o Streamlit Cloud roda em
    # UTC, e `date.today()` lá já virou amanhã enquanto aqui ainda é hoje —
    # isso sozinho criava um dia de atraso fantasma no fim da tarde.
    hoje = data_de_hoje()

    # Mapeamento auxiliar: list_id -> space
    lista_para_espaco = {l["id"]: l["space_id"] for l in listas}
    espacos_dict = {e["id"]: e for e in espacos}
    perfis_dict = {p["id"]: p for p in perfis}

    # Enriquecer tarefas com métricas calculadas
    tarefas_enriquecidas = []
    falhas_no_calculo = 0
    for t in todas_tarefas:
        try:
            space_id = lista_para_espaco.get(t.get("list_id"))
            espaco = espacos_dict.get(space_id)
            resp = perfis_dict.get(t.get("responsavel_id"))

            dias_andamento = calcular_dias_em_andamento(t, hoje)
            info_prazo = calcular_prazo(t, hoje)

            tarefas_enriquecidas.append(
                {
                    **t,
                    "space_id": space_id,
                    "space_nome": espaco["nome"] if espaco else "Sem Espaço",
                    "space_cor": espaco.get("cor", "#7b68ee") if espaco else "#7b68ee",
                    "responsavel_nome": resp["nome"] if resp else "Não atribuído",
                    "dias_andamento": dias_andamento,
                    **info_prazo,
                }
            )
        except Exception:
            # A tarefa entra mesmo assim, sem as métricas. Descartar em
            # silêncio fazia ela sumir do painel e dos totais — um KPI a
            # menos e ninguém sabendo por quê.
            falhas_no_calculo += 1
            logger.exception("Erro ao calcular métricas da tarefa %s.", t.get("id"))
            tarefas_enriquecidas.append(
                {
                    **t,
                    "space_id": None,
                    "space_nome": "Sem Espaço",
                    "space_cor": "#7b68ee",
                    "responsavel_nome": "Não atribuído",
                    "dias_andamento": 0,
                    **calcular_prazo({}, hoje),
                    "status_prazo": "Não foi possível calcular",
                    "badge_class": "normal",
                }
            )

    if falhas_no_calculo:
        st.warning(
            f"{falhas_no_calculo} tarefa(s) tiveram as métricas de prazo "
            "ignoradas por dados inconsistentes. Elas continuam listadas, mas "
            "sem situação de prazo."
        )

    # ========================================================== BARRA DE FILTROS
    with st.container():
        f_col1, f_col2, f_col3 = st.columns([1, 1, 1])

        opts_espacos = ["Todos os Projetos"] + [e["nome"] for e in espacos]
        espaco_sel = f_col1.selectbox("Filtrar por Projeto/Espaço", opts_espacos, key="dash_filter_espaco")

        opts_usuarios = ["Todos os Integrantes"] + [p["nome"] for p in perfis if p.get("ativo")]
        usuario_sel = f_col2.selectbox("Filtrar por Integrante", opts_usuarios, key="dash_filter_usuario")

        opts_status = ["Todos os Status", "Em Aberto (Pendentes)", "Concluídos"]
        status_sel = f_col3.selectbox("Situação das Entregas", opts_status, key="dash_filter_status")

    # Filtrar tarefas
    tarefas_filtradas = tarefas_enriquecidas
    if espaco_sel != "Todos os Projetos":
        tarefas_filtradas = [t for t in tarefas_filtradas if t["space_nome"] == espaco_sel]

    if usuario_sel != "Todos os Integrantes":
        tarefas_filtradas = [t for t in tarefas_filtradas if t["responsavel_nome"] == usuario_sel]

    if status_sel == "Em Aberto (Pendentes)":
        tarefas_filtradas = [t for t in tarefas_filtradas if t["status"] != Status.CONCLUIDO.value]
    elif status_sel == "Concluídos":
        tarefas_filtradas = [t for t in tarefas_filtradas if t["status"] == Status.CONCLUIDO.value]

    # ========================================================== CARDS DE KPIS
    total = len(tarefas_filtradas)
    concluidas = sum(1 for t in tarefas_filtradas if t["status"] == Status.CONCLUIDO.value)
    em_andamento = sum(1 for t in tarefas_filtradas if t["status"] == Status.EM_PROGRESSO.value)
    # `atrasado` já significa "pendente e vencida" (ver src/prazos.py); entrega
    # antiga fora do prazo é `entregue_com_atraso` e não entra neste KPI.
    atrasadas = sum(1 for t in tarefas_filtradas if t["atrasado"])
    med_andamento = (
        round(sum(t["dias_andamento"] for t in tarefas_filtradas) / total, 1)
        if total > 0
        else 0
    )

    pct_concluido = f"{(concluidas/total*100):.0f}% do total" if total > 0 else "0%"
    delta_atrasadas = f"⚠️ {atrasadas} atenção" if atrasadas > 0 else "No prazo"
    delta_atrasadas_cls = "kpi-delta--negative" if atrasadas > 0 else "kpi-delta--positive"

    kpi_html = limpar(f"""
<div class="kpi-row">
<div class="kpi-card" style="--kpi-accent: #6452db;">
<div class="kpi-label">Projetos / Tarefas</div>
<div class="kpi-value">{total}</div>
<div class="kpi-delta kpi-delta--positive">{em_andamento} em progresso</div>
</div>
<div class="kpi-card" style="--kpi-accent: #10b981;">
<div class="kpi-label">Entregas Concluídas</div>
<div class="kpi-value">{concluidas}</div>
<div class="kpi-delta kpi-delta--positive">{pct_concluido}</div>
</div>
<div class="kpi-card" style="--kpi-accent: #ef4444;">
<div class="kpi-label">Entregas Atrasadas</div>
<div class="kpi-value">{atrasadas}</div>
<div class="kpi-delta {delta_atrasadas_cls}">{esc(delta_atrasadas)}</div>
</div>
<div class="kpi-card" style="--kpi-accent: #3b82f6;">
<div class="kpi-label">Média Dias em Andamento</div>
<div class="kpi-value">{med_andamento} dias</div>
<div class="kpi-delta">Tempo de ciclo</div>
</div>
</div>
    """)
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ========================================================== ABAS DO DASHBOARD
    tab_gantt, tab_usuarios, tab_projetos, tab_aging = st.tabs([
        "📅 Cronograma (Gantt)",
        "👤 Situação por Usuário",
        "📂 Entregas por Projeto",
        "⏱️ Aging & Alertas de Prazo"
    ])

    # ---------------------------------------------------------- ABA GANTT (ECHARTS)
    with tab_gantt:
        st.markdown("### 📅 Cronograma Geral de Prazos e Entregas (Gráfico de Gantt)")
        st.markdown(
            "<p style='color:#64748b; font-size:13px; margin-bottom:1rem;'>"
            "Visão temporal contínua das tarefas do início (criação) até o prazo final no calendário."
            "</p>",
            unsafe_allow_html=True,
        )

        if not tarefas_filtradas:
            st.info("Nenhuma tarefa encontrada com os filtros selecionados.")
        else:
            cor_por = st.radio("Colorir barras por:", ["Status", "Projeto"], horizontal=True, key="gantt_color_by")
            min_date = min((para_data(t.get("criado_em")) or hoje for t in tarefas_filtradas), default=hoje)

            y_cats = []
            offsets = []
            durations = []
            meta_data = []

            for t in reversed(tarefas_filtradas):
                cod = t.get("codigo") or ""
                tit = t.get("titulo", "")
                lbl = f"{cod} · {tit}" if cod else tit
                if len(lbl) > 38:
                    lbl = lbl[:35] + "..."
                y_cats.append(lbl)

                dt_ini = para_data(t.get("criado_em")) or hoje
                dt_fim = para_data(t.get("data_limite")) or (dt_ini + timedelta(days=1))
                if dt_fim <= dt_ini:
                    dt_fim = dt_ini + timedelta(days=1)

                off = (dt_ini - min_date).days
                dur = max(1, (dt_fim - dt_ini).days)

                offsets.append(off)

                # Cor da barra
                bar_color = CORES_STATUS.get(t["status"], "#7b68ee")
                if cor_por == "Projeto":
                    bar_color = t.get("space_cor", "#7b68ee")

                durations.append({
                    "value": dur,
                    "itemStyle": {
                        "color": bar_color,
                        "borderRadius": [0, 8, 8, 0],
                        "shadowBlur": 6,
                        "shadowColor": "rgba(0, 0, 0, 0.15)"
                    }
                })

                meta_data.append({
                    "codigo": cod,
                    "titulo": tit,
                    "inicio": dt_ini.strftime("%d/%m/%Y"),
                    "fim": dt_fim.strftime("%d/%m/%Y"),
                    "resp": t.get("responsavel_nome", "—"),
                    "projeto": t.get("space_nome", "—"),
                    "status": t.get("status", "—"),
                    "prazo": t.get("status_prazo", "—"),
                })

            js_gantt = f"""
            var yCats = {json.dumps(y_cats, ensure_ascii=False)};
            var offsets = {json.dumps(offsets)};
            var durations = {json.dumps(durations, ensure_ascii=False)};
            var metaData = {json.dumps(meta_data, ensure_ascii=False)};

            var option = {{
                tooltip: {{
                    trigger: 'axis',
                    axisPointer: {{ type: 'shadow', shadowStyle: {{ color: 'rgba(123, 104, 238, 0.08)' }} }},
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    borderColor: 'rgba(123, 104, 238, 0.4)',
                    borderWidth: 1,
                    padding: [12, 16],
                    textStyle: {{ color: '#ffffff', fontSize: 12, fontFamily: 'Inter, sans-serif' }},
                    extraCssText: 'box-shadow: 0 12px 30px rgba(0,0,0,0.35); backdrop-filter: blur(10px); border-radius: 12px;',
                    formatter: function(params) {{
                        var item = params[1] || params[0];
                        if (!item || item.dataIndex === undefined) return '';
                        var m = metaData[item.dataIndex];
                        if (!m) return '';
                        return '<div style="font-weight:700;font-size:13px;color:#f8fafc;margin-bottom:6px;">' + m.codigo + ' · ' + m.titulo + '</div>' +
                               '<div style="font-size:11px;color:#cbd5e1;line-height:1.6;">' +
                               '📅 <b>Período:</b> ' + m.inicio + ' a ' + m.fim + ' (' + item.value + 'd)<br/>' +
                               '👤 <b>Responsável:</b> ' + m.resp + '<br/>' +
                               '📂 <b>Projeto:</b> ' + m.projeto + '<br/>' +
                               '📌 <b>Status:</b> ' + m.status + '<br/>' +
                               '⏱️ <b>Situação:</b> ' + m.prazo +
                               '</div>';
                    }}
                }},
                grid: {{ left: '3%', right: '4%', bottom: '4%', top: '3%', containLabel: true }},
                xAxis: {{ type: 'value', name: 'Dias', nameTextStyle: {{ color: '#334155', fontWeight: '600', fontSize: 12 }}, axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 12, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }}, splitLine: {{ lineStyle: {{ color: '#e2e8f0' }} }} }},
                yAxis: {{ type: 'category', data: yCats, axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 11, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }} }},
                series: [
                    {{ name: 'Offset', type: 'bar', stack: 'gantt', itemStyle: {{ color: 'transparent' }}, data: offsets }},
                    {{ name: 'Duração', type: 'bar', stack: 'gantt', data: durations }}
                ]
            }};
            """
            chart_height = max(420, len(tarefas_filtradas) * 38)
            _render_echart_html(js_gantt, height=chart_height)

    # ---------------------------------------------------------- ABA 1: USUÁRIOS (ECHARTS)
    with tab_usuarios:
        st.markdown("### 👤 Monitoramento de Carga e Entregas por Integrante")

        if not tarefas_filtradas:
            st.info("Nenhuma tarefa encontrada com os filtros selecionados.")
        else:
            dados_user = {}
            for t in tarefas_filtradas:
                user = t["responsavel_nome"]
                st_nome = t["status"]
                if user not in dados_user:
                    dados_user[user] = {s.value: 0 for s in Status}
                    dados_user[user]["atrasadas"] = 0
                    dados_user[user]["dias_totais"] = 0
                    dados_user[user]["count"] = 0

                dados_user[user][st_nome] += 1
                dados_user[user]["count"] += 1
                dados_user[user]["dias_totais"] += t["dias_andamento"]
                if t["atrasado"]:
                    dados_user[user]["atrasadas"] += 1

            users_list = list(dados_user.keys())

            series_list = []
            for st_enum in Status:
                st_name = st_enum.value
                y_vals = [dados_user[u].get(st_name, 0) for u in users_list]
                series_list.append({
                    "name": st_name,
                    "type": "bar",
                    "stack": "total",
                    "itemStyle": {
                        "color": CORES_STATUS.get(st_name, "#94a3b8"),
                        "borderRadius": [4, 4, 0, 0] if st_enum == Status.CONCLUIDO else [0, 0, 0, 0]
                    },
                    "data": y_vals
                })

            js_user = f"""
            var xCats = {json.dumps(users_list, ensure_ascii=False)};
            var seriesData = {json.dumps(series_list, ensure_ascii=False)};

            var option = {{
                tooltip: {{
                    trigger: 'axis',
                    axisPointer: {{ type: 'shadow', shadowStyle: {{ color: 'rgba(123, 104, 238, 0.08)' }} }},
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    borderColor: 'rgba(123, 104, 238, 0.4)',
                    borderWidth: 1,
                    padding: [12, 16],
                    textStyle: {{ color: '#ffffff', fontSize: 12, fontFamily: 'Inter, sans-serif' }},
                    extraCssText: 'box-shadow: 0 12px 30px rgba(0,0,0,0.35); backdrop-filter: blur(10px); border-radius: 12px;',
                    formatter: function(params) {{
                        var total = 0;
                        var res = '<div style="font-weight:700;font-size:13px;color:#f8fafc;margin-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:4px;">👤 ' + params[0].name + '</div>';
                        params.forEach(function(item) {{
                            total += item.value;
                            if (item.value > 0) {{
                                res += '<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:11px;color:#cbd5e1;margin-bottom:3px;">' +
                                       '<span>' + item.marker + ' ' + item.seriesName + '</span>' +
                                       '<strong style="color:#fff;">' + item.value + '</strong></div>';
                            }}
                        }});
                        res += '<div style="margin-top:6px;padding-top:4px;border-top:1px solid rgba(255,255,255,0.15);font-size:11px;font-weight:700;color:#a78bfa;display:flex;justify-content:space-between;"><span>Total de Tarefas:</span><span>' + total + '</span></div>';
                        return res;
                    }}
                }},
                legend: {{
                    top: 0,
                    textStyle: {{ color: '#475569', fontSize: 12, fontFamily: 'Inter, sans-serif' }}
                }},
                grid: {{ left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true }},
                xAxis: {{ type: 'category', data: xCats, axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 12, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }} }},
                yAxis: {{ type: 'value', axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 12, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }}, splitLine: {{ lineStyle: {{ color: '#e2e8f0' }} }} }},
                series: seriesData
            }};
            """
            _render_echart_html(js_user, height=380)

            # Detalhamento por Usuário Selecionado
            st.markdown("---")
            st.markdown("### 🔍 Detalhamento das Entregas por Usuário Específico")

            users_disponiveis = list(dados_user.keys())
            user_escolhido = st.selectbox("Selecione o integrante para examinar seus prazos:", users_disponiveis, key="dash_user_detail_select")

            if user_escolhido:
                sub_t = [t for t in tarefas_filtradas if t["responsavel_nome"] == user_escolhido]
                info_u = dados_user[user_escolhido]
                media_u = round(info_u["dias_totais"] / info_u["count"], 1) if info_u["count"] > 0 else 0

                u_atrasadas = info_u["atrasadas"]
                u_delta_cls = "kpi-delta--negative" if u_atrasadas > 0 else "kpi-delta--positive"
                u_delta_txt = f"⚠️ {u_atrasadas} atenção" if u_atrasadas > 0 else "No prazo"

                user_kpi_html = limpar(f"""
<div class="kpi-row">
<div class="kpi-card" style="--kpi-accent: #6452db;">
<div class="kpi-label">Total no Usuário</div>
<div class="kpi-value">{info_u['count']}</div>
</div>
<div class="kpi-card" style="--kpi-accent: #3b82f6;">
<div class="kpi-label">Em Progresso</div>
<div class="kpi-value">{info_u.get(Status.EM_PROGRESSO.value, 0)}</div>
</div>
<div class="kpi-card" style="--kpi-accent: #ef4444;">
<div class="kpi-label">Atrasadas</div>
<div class="kpi-value">{u_atrasadas}</div>
<div class="kpi-delta {u_delta_cls}">{esc(u_delta_txt)}</div>
</div>
<div class="kpi-card" style="--kpi-accent: #10b981;">
<div class="kpi-label">Média em Andamento</div>
<div class="kpi-value">{media_u} dias</div>
</div>
</div>
                """)
                st.markdown(user_kpi_html, unsafe_allow_html=True)

                st.markdown(f"**Lista de Projetos / Tarefas sob responsabilidade de `{user_escolhido}`:**")

                rows_html = []
                for item in sub_t:
                    badge_style = _estilo_badge(item["badge_class"])
                    # A data da entrega ao lado do prazo torna a conta
                    # conferível na própria tela: dá para ver de onde saiu o
                    # número de dias em vez de ter que acreditar nele.
                    entregue_em = item.get("data_conclusao")
                    entrega_txt = data_longa(entregue_em.isoformat()) if entregue_em else "—"
                    rows_html.append(f"""
                    <tr>
                        <td style="font-weight:600; color:#0f172a;">{esc(item.get('codigo') or '-')}</td>
                        <td>{esc(item.get('titulo', ''))}</td>
                        <td><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:{esc(item['space_cor'])}; margin-right:4px;"></span>{esc(item['space_nome'])}</td>
                        <td><span style="font-size:11px; padding:2px 8px; border-radius:12px; background:#f1f5f9; font-weight:600;">{esc(item['status'])}</span></td>
                        <td><strong>{item['dias_andamento']} dias</strong></td>
                        <td>{data_longa(item.get('data_limite'))}</td>
                        <td>{entrega_txt}</td>
                        <td><span style="font-size:11px; padding:2px 8px; border-radius:4px; font-weight:600; {badge_style}">{esc(item['status_prazo'])}</span></td>
                    </tr>
                    """)

                tabela_user_html = limpar(f"""
                <div class="tabela-wrap" style="margin-top:10px;">
                    <table class="tarefas">
                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Projeto / Tarefa</th>
                                <th>Espaço</th>
                                <th>Status</th>
                                <th>Dias em Andamento</th>
                                <th>Prazo Limite</th>
                                <th>Entrega Real</th>
                                <th>Situação do Prazo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows_html)}
                        </tbody>
                    </table>
                </div>
                """)
                st.markdown(tabela_user_html, unsafe_allow_html=True)

    # ---------------------------------------------------------- ABA 2: PROJETOS / ESPAÇOS (ECHARTS)
    with tab_projetos:
        st.markdown("### 📂 Monitoramento da Saúde das Entregas por Projeto")

        if not tarefas_filtradas:
            st.info("Nenhuma tarefa encontrada com os filtros selecionados.")
        else:
            dados_espaco = {}
            for t in tarefas_filtradas:
                esp = t["space_nome"]
                st_nome = t["status"]
                if esp not in dados_espaco:
                    dados_espaco[esp] = {s.value: 0 for s in Status}
                    dados_espaco[esp]["total"] = 0
                    dados_espaco[esp]["cor"] = t["space_cor"]

                dados_espaco[esp][st_nome] += 1
                dados_espaco[esp]["total"] += 1

            col_g1, col_g2 = st.columns([1.4, 1])

            with col_g1:
                esp_names = list(dados_espaco.keys())
                series_esp = []
                for st_enum in Status:
                    st_name = st_enum.value
                    y_vals = [dados_espaco[e].get(st_name, 0) for e in esp_names]
                    series_esp.append({
                        "name": st_name,
                        "type": "bar",
                        "stack": "total",
                        "itemStyle": {
                            "color": CORES_STATUS.get(st_name, "#94a3b8"),
                            "borderRadius": [4, 4, 0, 0] if st_enum == Status.CONCLUIDO else [0, 0, 0, 0]
                        },
                        "data": y_vals
                    })

                js_esp = f"""
                var xCats = {json.dumps(esp_names, ensure_ascii=False)};
                var seriesData = {json.dumps(series_esp, ensure_ascii=False)};

                var option = {{
                    title: {{ text: 'Status por Projeto', textStyle: {{ fontSize: 13, fontWeight: 'bold', color: '#1e293b' }} }},
                    tooltip: {{
                        trigger: 'axis',
                        axisPointer: {{ type: 'shadow', shadowStyle: {{ color: 'rgba(123, 104, 238, 0.08)' }} }},
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        borderColor: 'rgba(123, 104, 238, 0.4)',
                        borderWidth: 1,
                        padding: [12, 16],
                        textStyle: {{ color: '#ffffff', fontSize: 12, fontFamily: 'Inter, sans-serif' }},
                        extraCssText: 'box-shadow: 0 12px 30px rgba(0,0,0,0.35); backdrop-filter: blur(10px); border-radius: 12px;',
                        formatter: function(params) {{
                            var total = 0;
                            var res = '<div style="font-weight:700;font-size:13px;color:#f8fafc;margin-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:4px;">📂 ' + params[0].name + '</div>';
                            params.forEach(function(item) {{
                                total += item.value;
                                if (item.value > 0) {{
                                    res += '<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:11px;color:#cbd5e1;margin-bottom:3px;">' +
                                           '<span>' + item.marker + ' ' + item.seriesName + '</span>' +
                                           '<strong style="color:#fff;">' + item.value + '</strong></div>';
                                }}
                            }});
                            res += '<div style="margin-top:6px;padding-top:4px;border-top:1px solid rgba(255,255,255,0.15);font-size:11px;font-weight:700;color:#a78bfa;display:flex;justify-content:space-between;"><span>Total do Projeto:</span><span>' + total + '</span></div>';
                            return res;
                        }}
                    }},
                    legend: {{
                        top: 25,
                        textStyle: {{ color: '#475569', fontSize: 11, fontFamily: 'Inter, sans-serif' }}
                    }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', top: '65px', containLabel: true }},
                    xAxis: {{ type: 'category', data: xCats, axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 12, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }} }},
                    yAxis: {{ type: 'value', axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 12, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }}, splitLine: {{ lineStyle: {{ color: '#e2e8f0' }} }} }},
                    series: seriesData
                }};
                """
                _render_echart_html(js_esp, height=360)

            with col_g2:
                # Gráfico de Rosca (Donut ECharts) por Prioridade
                prioridades_cnt = {}
                for t in tarefas_filtradas:
                    prio = t.get("prioridade", "Normal")
                    prioridades_cnt[prio] = prioridades_cnt.get(prio, 0) + 1

                pie_data = []
                for p_name, p_val in prioridades_cnt.items():
                    pie_data.append({
                        "name": p_name,
                        "value": p_val,
                        "itemStyle": {"color": CORES_PRIO.get(p_name, "#64748b")}
                    })

                js_pie = f"""
                var pieData = {json.dumps(pie_data, ensure_ascii=False)};
                var totalTasks = {sum(prioridades_cnt.values())};

                var option = {{
                    title: {{
                        text: 'Prioridades',
                        left: 'center',
                        top: 0,
                        textStyle: {{ fontSize: 13, fontWeight: 'bold', color: '#1e293b' }}
                    }},
                    tooltip: {{
                        trigger: 'item',
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        borderColor: 'rgba(123, 104, 238, 0.4)',
                        borderWidth: 1,
                        padding: [12, 16],
                        textStyle: {{ color: '#ffffff', fontSize: 12, fontFamily: 'Inter, sans-serif' }},
                        extraCssText: 'box-shadow: 0 12px 30px rgba(0,0,0,0.35); backdrop-filter: blur(10px); border-radius: 12px;',
                        formatter: function(params) {{
                            return '<div style="font-weight:700;font-size:12px;color:#f8fafc;">' + params.marker + ' ' + params.name + '</div>' +
                                   '<div style="font-size:11px;color:#cbd5e1;margin-top:4px;">Quantidade: <strong style="color:#a78bfa;">' + params.value + '</strong> (' + params.percent + '%)</div>';
                        }}
                    }},
                    legend: {{
                        bottom: '0%',
                        left: 'center',
                        textStyle: {{ color: '#475569', fontSize: 11, fontFamily: 'Inter, sans-serif' }}
                    }},
                    series: [{{
                        type: 'pie',
                        radius: ['48%', '75%'],
                        center: ['50%', '46%'],
                        avoidLabelOverlap: false,
                        itemStyle: {{
                            borderRadius: 8,
                            borderColor: '#ffffff',
                            borderWidth: 2
                        }},
                        label: {{
                            show: true,
                            position: 'center',
                            formatter: function() {{ return 'Total\\n' + totalTasks; }},
                            fontSize: 14,
                            fontWeight: 'bold',
                            color: '#334155'
                        }},
                        data: pieData
                    }}]
                }};
                """
                _render_echart_html(js_pie, height=360)

            # Tabela Resumo da Saúde dos Projetos
            st.markdown("### 📋 Resumo Consolidado por Projeto")

            p_rows = []
            for esp_nome, e_info in dados_espaco.items():
                tot = e_info["total"]
                conc = e_info.get(Status.CONCLUIDO.value, 0)
                pct = round((conc / tot * 100), 1) if tot > 0 else 0
                em_prog = e_info.get(Status.EM_PROGRESSO.value, 0)
                a_faz = e_info.get(Status.A_FAZER.value, 0)

                p_rows.append(f"""
                <tr>
                    <td style="font-weight:600;"><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:{esc(e_info['cor'])}; margin-right:6px;"></span>{esc(esp_nome)}</td>
                    <td><strong>{tot}</strong></td>
                    <td>{a_faz}</td>
                    <td>{em_prog}</td>
                    <td><strong style="color:#10b981;">{conc}</strong></td>
                    <td>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="flex:1; background:#e2e8f0; border-radius:4px; height:8px; overflow:hidden;">
                                <div style="width:{pct}%; background:#10b981; height:100%;"></div>
                            </div>
                            <span style="font-size:11px; font-weight:600; min-width:36px;">{pct}%</span>
                        </div>
                    </td>
                </tr>
                """)

            tabela_proj_html = limpar(f"""
            <div class="tabela-wrap">
                <table class="tarefas">
                    <thead>
                        <tr>
                            <th>Projeto / Espaço</th>
                            <th>Total de Tarefas</th>
                            <th>A Fazer</th>
                            <th>Em Progresso</th>
                            <th>Concluídas</th>
                            <th>Taxa de Conclusão</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(p_rows)}
                    </tbody>
                </table>
            </div>
            """)
            st.markdown(tabela_proj_html, unsafe_allow_html=True)

    # ---------------------------------------------------------- ABA 3: AGING & ALERTAS (ECHARTS)
    with tab_aging:
        st.markdown("### ⏱️ Tempo em Andamento (Aging) & Alerta de Prazos Próximos")

        if not tarefas_filtradas:
            st.info("Nenhuma tarefa encontrada com os filtros selecionados.")
        else:
            faixas = {"0-7 dias": 0, "8-15 dias": 0, "16-30 dias": 0, "+30 dias": 0}
            em_aberto = [t for t in tarefas_filtradas if t["status"] != Status.CONCLUIDO.value]

            for t in em_aberto:
                d = t["dias_andamento"]
                if d <= 7:
                    faixas["0-7 dias"] += 1
                elif d <= 15:
                    faixas["8-15 dias"] += 1
                elif d <= 30:
                    faixas["16-30 dias"] += 1
                else:
                    faixas["+30 dias"] += 1

            col_a1, col_a2 = st.columns([1, 1])

            with col_a1:
                aging_colors = ["#3b82f6", "#f59e0b", "#ff7a00", "#ef4444"]
                aging_bar_data = []
                for idx, (f_name, f_val) in enumerate(faixas.items()):
                    aging_bar_data.append({
                        "value": f_val,
                        "itemStyle": {
                            "color": aging_colors[idx],
                            "borderRadius": [8, 8, 0, 0]
                        }
                    })

                js_aging = f"""
                var xCats = {json.dumps(list(faixas.keys()), ensure_ascii=False)};
                var barData = {json.dumps(aging_bar_data, ensure_ascii=False)};

                var option = {{
                    title: {{ text: 'Aging de Tarefas Pendentes', textStyle: {{ fontSize: 13, fontWeight: 'bold', color: '#1e293b' }} }},
                    tooltip: {{
                        trigger: 'axis',
                        axisPointer: {{ type: 'shadow', shadowStyle: {{ color: 'rgba(123, 104, 238, 0.08)' }} }},
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        borderColor: 'rgba(123, 104, 238, 0.4)',
                        borderWidth: 1,
                        padding: [12, 16],
                        textStyle: {{ color: '#ffffff', fontSize: 12, fontFamily: 'Inter, sans-serif' }},
                        extraCssText: 'box-shadow: 0 12px 30px rgba(0,0,0,0.35); backdrop-filter: blur(10px); border-radius: 12px;',
                        formatter: function(params) {{
                            return '<div style="font-weight:700;color:#f8fafc;font-size:12px;">⏱️ ' + params[0].name + '</div>' +
                                   '<div style="color:#cbd5e1;font-size:11px;margin-top:4px;">Tarefas pendentes: <strong style="color:#a78bfa;">' + params[0].value + '</strong></div>';
                        }}
                    }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', top: '45px', containLabel: true }},
                    xAxis: {{ type: 'category', data: xCats, axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 12, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }} }},
                    yAxis: {{ type: 'value', axisLabel: {{ color: '#0f172a', fontWeight: '600', fontSize: 12, fontFamily: 'Inter, sans-serif' }}, axisLine: {{ show: true, lineStyle: {{ color: '#94a3b8' }} }}, splitLine: {{ lineStyle: {{ color: '#e2e8f0' }} }} }},
                    series: [{{
                        type: 'bar',
                        barWidth: '45%',
                        data: barData,
                        label: {{ show: true, position: 'top', color: '#334155', fontWeight: 'bold', fontSize: 12 }}
                    }}]
                }};
                """
                _render_echart_html(js_aging, height=350)

            with col_a2:
                # Tarefas mais antigas em andamento
                antigas = sorted(em_aberto, key=lambda x: x["dias_andamento"], reverse=True)[:5]
                st.markdown("**Top 5 Tarefas em Andamento há mais Tempo:**")
                if not antigas:
                    st.success("Não há tarefas pendentes!")
                else:
                    for a in antigas:
                        st.markdown(
                            f"- **{esc(a.get('codigo') or '')} {esc(a['titulo'])}** "
                            f"({esc(a['responsavel_nome'])}) — "
                            f"<span style='color:#ef4444; font-weight:600;'>{a['dias_andamento']} dias em andamento</span>",
                            unsafe_allow_html=True,
                        )

            st.markdown("---")
            st.markdown("### 🚨 Painel de Alerta de Vencimento e Atrasos")

            criticas = [t for t in tarefas_filtradas if esta_critica(t)]

            if not criticas:
                st.success("🎉 Nenhuma tarefa atrasada ou prestes a vencer nos próximos 3 dias!")
            else:
                crit_rows = []
                for c in criticas:
                    badge_c = _estilo_badge(c["badge_class"])
                    crit_rows.append(f"""
                    <tr>
                        <td style="font-weight:600;">{esc(c.get('codigo') or '-')}</td>
                        <td>{esc(c['titulo'])}</td>
                        <td>{esc(c['responsavel_nome'])}</td>
                        <td>{esc(c['space_nome'])}</td>
                        <td><span style="font-size:11px; padding:2px 8px; border-radius:4px; font-weight:600; {badge_c}">{esc(c['status_prazo'])}</span></td>
                    </tr>
                    """)

                tabela_crit_html = limpar(f"""
                <div class="tabela-wrap">
                    <table class="tarefas">
                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Título</th>
                                <th>Responsável</th>
                                <th>Espaço</th>
                                <th>Status do Prazo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(crit_rows)}
                        </tbody>
                    </table>
                </div>
                """)
                st.markdown(tabela_crit_html, unsafe_allow_html=True)
