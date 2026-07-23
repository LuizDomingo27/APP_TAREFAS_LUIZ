-- =====================================================================
-- 05_seed_tasks.sql — tarefas de exemplo (as mesmas do protótipo)
--
-- Serve só para o Quadro e a Lista terem o que mostrar enquanto a
-- Fase 3 (criação/edição pelo app) não existe. Depois que a equipe
-- começar a cadastrar de verdade, dá para apagar tudo com:
--     delete from public.tasks where codigo like 'DEV-1%';
--
-- Rode DEPOIS de 04_extras.sql.
-- =====================================================================

-- Responsável: quem já estiver ativo. Com um usuário só, todas ficam com ele.
with alvo as (
    select l.id as list_id
      from public.lists l
      join public.spaces s on s.id = l.space_id
     where s.prefixo = 'DEV' and l.nome = 'Sprint Atual'
     limit 1
),
dono as (
    select id from public.profiles where ativo order by criado_em limit 1
)
insert into public.tasks
    (list_id, titulo, descricao, status, prioridade, responsavel_id, criado_por,
     data_limite, estimativa_horas, ordem)
select alvo.list_id, v.titulo, v.descricao, v.status::task_status,
       v.prioridade::task_priority, dono.id, dono.id,
       v.data_limite::date, v.horas, v.ordem
  from alvo, dono,
       (values
         ('Refatorar tela de Login com Dark Mode',
          'Aplicar a nova paleta e garantir contraste AA em ambos os temas.',
          'A Fazer', 'Urgente', current_date + 5, 4.0, 1, 'Frontend'),
         ('Documentar endpoints da API v2',
          'Subir a especificação OpenAPI e publicar no portal interno.',
          'A Fazer', 'Baixa', current_date + 12, 6.0, 2, 'Docs'),
         ('Integração com Gateway de Pagamentos',
          'Implementar checkout e tratar os webhooks de confirmação.',
          'Em Progresso', 'Alta', current_date + 3, 16.0, 1, 'Backend'),
         ('Ajustar responsividade do Dashboard',
          'Quebras de layout abaixo de 768px na visão de métricas.',
          'Em Progresso', 'Normal', current_date + 7, 5.0, 2, 'Frontend'),
         ('Homologação do Gateway de Pagamentos',
          'Verificar webhooks e retorno de erro no checkout sandbox.',
          'Em Revisão', 'Urgente', current_date + 1, 3.0, 1, 'Financeiro'),
         ('Criar Landing Page de Lançamento',
          'Landing publicada e integrada com a ferramenta de e-mail.',
          'Concluído', 'Baixa', current_date - 2, 8.0, 1, 'Marketing'),
         ('Atualizar dependências do Node.js v20',
          'Atualização concluída sem downtime no servidor.',
          'Concluído', 'Normal', current_date - 4, 2.0, 2, 'DevOps')
       ) as v (titulo, descricao, status, prioridade, data_limite, horas, ordem, tag)
 where not exists (
     select 1 from public.tasks t where t.titulo = v.titulo
 );

-- ---------- Tags ----------
insert into public.task_tags (task_id, tag)
select t.id, v.tag
  from public.tasks t
  join (values
         ('Refatorar tela de Login com Dark Mode',   'Frontend'),
         ('Documentar endpoints da API v2',          'Docs'),
         ('Integração com Gateway de Pagamentos',    'Backend'),
         ('Ajustar responsividade do Dashboard',     'Frontend'),
         ('Homologação do Gateway de Pagamentos',    'Financeiro'),
         ('Criar Landing Page de Lançamento',        'Marketing'),
         ('Atualizar dependências do Node.js v20',   'DevOps')
       ) as v (titulo, tag) on v.titulo = t.titulo
on conflict (task_id, tag) do nothing;

-- ---------- Subtarefas (só para o contador do card aparecer) ----------
insert into public.subtasks (task_id, titulo, concluida, ordem)
select t.id, v.titulo, v.concluida, v.ordem
  from public.tasks t
  join (values
         ('Integração com Gateway de Pagamentos', 'Criar conta sandbox',        true,  1),
         ('Integração com Gateway de Pagamentos', 'Implementar webhook',        false, 2),
         ('Integração com Gateway de Pagamentos', 'Testes de ponta a ponta',    false, 3),
         ('Refatorar tela de Login com Dark Mode', 'Definir tokens de cor',     true,  1),
         ('Refatorar tela de Login com Dark Mode', 'Revisar contraste AA',      false, 2)
       ) as v (tarefa, titulo, concluida, ordem) on v.tarefa = t.titulo
 where not exists (
     select 1 from public.subtasks s where s.task_id = t.id and s.titulo = v.titulo
 );
