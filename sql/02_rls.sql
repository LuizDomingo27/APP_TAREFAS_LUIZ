-- =====================================================================
-- 02_rls.sql — Row Level Security
--
-- Política da equipe: todo membro ativo LÊ tudo e EDITA tudo.
-- Exclusão de tarefa fica com quem criou (ou com um gestor).
-- Comentários: cada um mexe só no próprio.
--
-- Rode DEPOIS de 01_schema.sql.
-- =====================================================================

-- Funções auxiliares em SECURITY DEFINER: evitam recursão infinita
-- quando uma policy de profiles precisa consultar profiles.
create or replace function public.is_membro()
returns boolean
language sql stable security definer set search_path = public
as $$
    select exists (
        select 1 from public.profiles
        where id = auth.uid() and ativo
    );
$$;

create or replace function public.is_gestor()
returns boolean
language sql stable security definer set search_path = public
as $$
    select exists (
        select 1 from public.profiles
        where id = auth.uid() and ativo and gestor
    );
$$;


-- ---------- Ativa RLS em tudo ----------
alter table public.profiles       enable row level security;
alter table public.allowed_emails enable row level security;
alter table public.spaces    enable row level security;
alter table public.lists     enable row level security;
alter table public.tasks     enable row level security;
alter table public.task_tags enable row level security;
alter table public.subtasks  enable row level security;
alter table public.comments  enable row level security;


-- ---------- allowed_emails ----------
-- Lista de convidados: só gestor lê e altera. Ninguém mais precisa dela —
-- o trigger tk_handle_new_user é SECURITY DEFINER e passa por cima do RLS.
drop policy if exists allowed_emails_gestor on public.allowed_emails;
create policy allowed_emails_gestor on public.allowed_emails
    for all to authenticated
    using (public.is_gestor()) with check (public.is_gestor());


-- ---------- profiles ----------
-- O 'id = auth.uid()' é o que permite a quem ainda não foi liberado ler o
-- próprio perfil e ver a tela de "acesso pendente" em vez de um erro.
drop policy if exists profiles_select on public.profiles;
create policy profiles_select on public.profiles
    for select to authenticated
    using (id = auth.uid() or public.is_membro());

-- Cada um edita apenas o próprio perfil.
drop policy if exists profiles_update_self on public.profiles;
create policy profiles_update_self on public.profiles
    for update to authenticated
    using (id = auth.uid())
    with check (id = auth.uid());

-- Gestor ativa/desativa e promove pela tela de Equipe.
drop policy if exists profiles_gestor_manage on public.profiles;
create policy profiles_gestor_manage on public.profiles
    for update to authenticated
    using (public.is_gestor()) with check (public.is_gestor());


-- ---------- spaces / lists ----------
-- Estrutura do workspace: todos leem, só gestor altera.
drop policy if exists spaces_select on public.spaces;
create policy spaces_select on public.spaces
    for select to authenticated using (public.is_membro());

drop policy if exists spaces_write on public.spaces;
create policy spaces_write on public.spaces
    for all to authenticated
    using (public.is_gestor()) with check (public.is_gestor());

drop policy if exists lists_select on public.lists;
create policy lists_select on public.lists
    for select to authenticated using (public.is_membro());

drop policy if exists lists_write on public.lists;
create policy lists_write on public.lists
    for all to authenticated
    using (public.is_gestor()) with check (public.is_gestor());


-- ---------- tasks ----------
drop policy if exists tasks_select on public.tasks;
create policy tasks_select on public.tasks
    for select to authenticated using (public.is_membro());

drop policy if exists tasks_insert on public.tasks;
create policy tasks_insert on public.tasks
    for insert to authenticated
    with check (public.is_membro() and criado_por = auth.uid());

drop policy if exists tasks_update on public.tasks;
create policy tasks_update on public.tasks
    for update to authenticated
    using (public.is_membro()) with check (public.is_membro());

-- Só quem criou (ou um gestor) exclui.
drop policy if exists tasks_delete on public.tasks;
create policy tasks_delete on public.tasks
    for delete to authenticated
    using (criado_por = auth.uid() or public.is_gestor());


-- ---------- task_tags / subtasks ----------
-- Acompanham a tarefa: qualquer membro ativo gerencia.
drop policy if exists task_tags_all on public.task_tags;
create policy task_tags_all on public.task_tags
    for all to authenticated
    using (public.is_membro()) with check (public.is_membro());

drop policy if exists subtasks_all on public.subtasks;
create policy subtasks_all on public.subtasks
    for all to authenticated
    using (public.is_membro()) with check (public.is_membro());


-- ---------- comments ----------
drop policy if exists comments_select on public.comments;
create policy comments_select on public.comments
    for select to authenticated using (public.is_membro());

drop policy if exists comments_insert on public.comments;
create policy comments_insert on public.comments
    for insert to authenticated
    with check (public.is_membro() and autor_id = auth.uid());

drop policy if exists comments_update_own on public.comments;
create policy comments_update_own on public.comments
    for update to authenticated
    using (autor_id = auth.uid()) with check (autor_id = auth.uid());

drop policy if exists comments_delete_own on public.comments;
create policy comments_delete_own on public.comments
    for delete to authenticated
    using (autor_id = auth.uid() or public.is_gestor());
