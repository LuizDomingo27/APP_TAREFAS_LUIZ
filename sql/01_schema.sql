-- =====================================================================
-- 01_schema.sql — estrutura do banco
-- Rode no SQL Editor do Supabase, uma vez, na ordem 01 -> 02 -> 03.
-- =====================================================================

-- ---------- Enums ----------
do $$ begin
    create type task_status as enum ('A Fazer', 'Em Progresso', 'Em Revisão', 'Concluído');
exception when duplicate_object then null; end $$;

do $$ begin
    create type task_priority as enum ('Urgente', 'Alta', 'Normal', 'Baixa');
exception when duplicate_object then null; end $$;


-- ---------- Perfis ----------
-- Espelha auth.users. O id é o mesmo do usuário autenticado.
create table if not exists public.profiles (
    id          uuid primary key references auth.users (id) on delete cascade,
    email       text,                              -- cópia de auth.users.email:
                                                   -- o cliente anon não lê o schema auth,
                                                   -- e a tela de Equipe precisa exibir
    nome        text not null,
    cargo       text,
    avatar_url  text,
    gestor      boolean not null default false,
    ativo       boolean not null default false,   -- só a allowlist abaixo ativa
    criado_em   timestamptz not null default now()
);


-- ---------- E-mails autorizados ----------
-- O app tem cadastro aberto (a pessoa escolhe a própria senha na tela de
-- registro), então esta tabela é o que separa a equipe de qualquer um que
-- descubra a URL. Quem não está aqui até consegue criar login, mas o perfil
-- nasce com ativo = false e as policies do 02_rls.sql não devolvem uma linha
-- sequer para ele.
create table if not exists public.allowed_emails (
    email        text primary key,
    nome         text,
    cargo        text,
    gestor       boolean not null default false,
    convidado_em timestamptz not null default now()
);

-- Cria o perfil automaticamente quando alguém se cadastra.
-- Nome prefixado de propósito: 'handle_new_user' é o nome usado nos tutoriais
-- do Supabase, e este banco é compartilhado com outras aplicações.
create or replace function public.tk_handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
    v_allow public.allowed_emails%rowtype;
begin
    select * into v_allow
      from public.allowed_emails
     where lower(email) = lower(new.email);

    insert into public.profiles (id, email, nome, cargo, gestor, ativo)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'nome', v_allow.nome, split_part(new.email, '@', 1)),
        coalesce(new.raw_user_meta_data ->> 'cargo', v_allow.cargo),
        coalesce(v_allow.gestor, false),
        v_allow.email is not null          -- fora da allowlist entra inativo
    )
    on conflict (id) do nothing;
    return new;
end $$;

drop trigger if exists on_auth_user_created_tarefas on auth.users;
create trigger on_auth_user_created_tarefas
    after insert on auth.users
    for each row execute function public.tk_handle_new_user();


-- ---------- Espaços e listas ----------
create table if not exists public.spaces (
    id              uuid primary key default gen_random_uuid(),
    nome            text not null,
    cor             text not null default '#7b68ee',
    prefixo         text not null unique,          -- ex.: 'DEV' -> tarefas DEV-101
    proximo_numero  integer not null default 101,
    ordem           integer not null default 0,
    criado_em       timestamptz not null default now()
);

create table if not exists public.lists (
    id        uuid primary key default gen_random_uuid(),
    space_id  uuid not null references public.spaces (id) on delete cascade,
    nome      text not null,
    icone     text not null default 'list',
    ordem     integer not null default 0,
    criado_em timestamptz not null default now()
);

create index if not exists lists_space_idx on public.lists (space_id, ordem);


-- ---------- Tarefas ----------
create table if not exists public.tasks (
    id                uuid primary key default gen_random_uuid(),
    list_id           uuid not null references public.lists (id) on delete cascade,
    codigo            text unique,                  -- preenchido pelo trigger abaixo
    titulo            text not null,
    descricao         text not null default '',
    status            task_status not null default 'A Fazer',
    prioridade        task_priority not null default 'Normal',
    responsavel_id    uuid references public.profiles (id) on delete set null,
    criado_por        uuid not null references public.profiles (id) default auth.uid(),
    data_limite       date,
    estimativa_horas  numeric(5, 2),
    ordem             integer not null default 0,
    criado_em         timestamptz not null default now(),
    atualizado_em     timestamptz not null default now()
);

create index if not exists tasks_list_idx        on public.tasks (list_id, status, ordem);
create index if not exists tasks_responsavel_idx on public.tasks (responsavel_id);

-- Gera o código sequencial por espaço (DEV-101, DEV-102, ...).
create or replace function public.set_task_codigo()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
    v_space_id uuid;
    v_prefixo  text;
    v_numero   integer;
begin
    if new.codigo is not null then
        return new;
    end if;

    select s.id into v_space_id
    from public.lists l
    join public.spaces s on s.id = l.space_id
    where l.id = new.list_id;

    update public.spaces
       set proximo_numero = proximo_numero + 1
     where id = v_space_id
    returning prefixo, proximo_numero - 1 into v_prefixo, v_numero;

    new.codigo := v_prefixo || '-' || v_numero;
    return new;
end $$;

drop trigger if exists tasks_set_codigo on public.tasks;
create trigger tasks_set_codigo
    before insert on public.tasks
    for each row execute function public.set_task_codigo();

-- Mantém atualizado_em em dia (usado para detectar edição concorrente).
create or replace function public.touch_atualizado_em()
returns trigger language plpgsql as $$
begin
    new.atualizado_em := now();
    return new;
end $$;

drop trigger if exists tasks_touch on public.tasks;
create trigger tasks_touch
    before update on public.tasks
    for each row execute function public.touch_atualizado_em();


-- ---------- Tags, subtarefas e comentários ----------
create table if not exists public.task_tags (
    task_id uuid not null references public.tasks (id) on delete cascade,
    tag     text not null,
    primary key (task_id, tag)
);

create table if not exists public.subtasks (
    id        uuid primary key default gen_random_uuid(),
    task_id   uuid not null references public.tasks (id) on delete cascade,
    titulo    text not null,
    concluida boolean not null default false,
    ordem     integer not null default 0,
    criado_em timestamptz not null default now()
);

create index if not exists subtasks_task_idx on public.subtasks (task_id, ordem);

create table if not exists public.comments (
    id        uuid primary key default gen_random_uuid(),
    task_id   uuid not null references public.tasks (id) on delete cascade,
    autor_id  uuid not null references public.profiles (id) on delete cascade default auth.uid(),
    texto     text not null,
    criado_em timestamptz not null default now()
);

create index if not exists comments_task_idx on public.comments (task_id, criado_em);
