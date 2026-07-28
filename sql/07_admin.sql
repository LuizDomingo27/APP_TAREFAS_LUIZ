-- =====================================================================
-- 07_admin.sql — papel de administrador + trava contra ficar sem gestor
--
-- Rode DEPOIS de 06_concluido_em.sql. Pode rodar mais de uma vez.
--
-- Duas coisas entram aqui:
--
--   1. a coluna `admin`, um segundo papel com exatamente os mesmos poderes
--      do gestor (a diferença é só de nomenclatura);
--   2. as travas que impedem alguém de tirar o próprio acesso e o workspace
--      de ficar sem nenhuma pessoa que possa gerenciar.
--
-- A (2) é resposta a um incidente: o único gestor conseguiu se desativar
-- pela tela de Equipe e o workspace ficou sem ninguém que pudesse liberar
-- acesso — sem caminho de volta a não ser por este SQL Editor. As travas
-- estão também no app (`src/repo/catalog.py`), mas app tem bug; a policy e
-- o trigger abaixo valem para qualquer caminho, inclusive chamada direta na
-- API REST do Supabase com o token de um membro.
-- =====================================================================


-- ---------- 1. Coluna do papel ----------

alter table public.profiles
    add column if not exists admin boolean not null default false;

alter table public.allowed_emails
    add column if not exists admin boolean not null default false;

-- Quem gerencia: gestor OU admin. Espelha `Perfil.pode_gerenciar` no Python.
create or replace function public.tk_gerencia(p public.profiles)
returns boolean
language sql immutable
as $$
    select p.gestor or p.admin;
$$;

-- O cadastro passa a carregar o papel que veio da pré-autorização.
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

    insert into public.profiles (id, email, nome, cargo, gestor, admin, ativo)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'nome', v_allow.nome, split_part(new.email, '@', 1)),
        coalesce(new.raw_user_meta_data ->> 'cargo', v_allow.cargo),
        coalesce(v_allow.gestor, false),
        coalesce(v_allow.admin, false),
        v_allow.email is not null          -- fora da allowlist entra inativo
    )
    on conflict (id) do nothing;
    return new;
end $$;


-- ---------- 2. Admin manda igual gestor ----------
-- Redefinir esta função basta: todas as policies de 02_rls.sql chamam ela,
-- nenhuma olha a coluna `gestor` direto. O nome fica como está para não ter
-- de reescrever as dez policies.
create or replace function public.is_gestor()
returns boolean
language sql stable security definer set search_path = public
as $$
    select exists (
        select 1 from public.profiles
        where id = auth.uid() and ativo and (gestor or admin)
    );
$$;


-- ---------- 3. Gestor não mexe na própria linha ----------
-- Vale para a policy de gestão. A `profiles_update_self` continua como
-- estava, porque é ela que deixa cada um editar o próprio nome e cargo —
-- o que ela NÃO pode mais deixar passar são as colunas de acesso, e isso
-- quem barra é o trigger do item 4 (policy não enxerga OLD, e subconsulta
-- em `profiles` dentro de uma policy de `profiles` daria recursão).
drop policy if exists profiles_gestor_manage on public.profiles;
create policy profiles_gestor_manage on public.profiles
    for update to authenticated
    using (public.is_gestor() and id <> auth.uid())
    with check (public.is_gestor() and id <> auth.uid());


-- ---------- 4. As duas travas de acesso ----------
-- Trigger e não policy: aqui existe OLD, então dá para comparar o que mudou
-- em vez de só olhar a linha nova.
--
--   (a) ninguém altera o próprio gestor/admin/ativo/recusado — nem por PATCH
--       direto na API REST, que era o furo maior: qualquer membro conseguia
--       se promover a gestor;
--   (b) o último que gerencia não perde o acesso, venha o comando de quem
--       vier — é o caso que deixou o workspace sem ninguém.
--
-- `auth.uid()` é nulo no SQL Editor, então (a) não atrapalha a recuperação
-- manual do item 5.
create or replace function public.tk_guardar_acesso()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
    v_mudou_acesso boolean := (new.gestor, new.admin, new.ativo, new.recusado)
                     is distinct from (old.gestor, old.admin, old.ativo, old.recusado);
begin
    if v_mudou_acesso and auth.uid() is not null and auth.uid() = old.id then
        raise exception
            'Você não pode alterar o próprio nível de acesso. Peça a outro '
            'gestor ou administrador.'
            using errcode = 'check_violation';
    end if;

    -- Só interessa quando a linha DEIXA de gerenciar (ou de estar ativa).
    if (old.ativo and public.tk_gerencia(old))
       and not (new.ativo and public.tk_gerencia(new)) then
        if not exists (
            select 1 from public.profiles
             where id <> old.id and ativo and (gestor or admin)
        ) then
            raise exception
                'Não é possível remover o acesso de %: é a única pessoa que '
                'pode gerenciar o workspace. Promova outra antes.', old.nome
                using errcode = 'check_violation';
        end if;
    end if;

    return new;
end $$;

drop trigger if exists profiles_protege_ultimo_gestor on public.profiles;
drop trigger if exists profiles_guarda_acesso on public.profiles;
create trigger profiles_guarda_acesso
    before update on public.profiles
    for each row execute function public.tk_guardar_acesso();


-- ---------- 5. Recuperação ----------
-- Se o workspace já estiver sem nenhum gestor ativo, nada acima ressuscita
-- ninguém — o trigger só impede *perder* o último, não devolve. Rode isto
-- uma vez, com o seu e-mail, para se readmitir:
--
--   update public.profiles
--      set ativo = true, recusado = false, admin = true
--    where lower(email) = lower('voce@empresa.com');
--
-- Se nem a linha existir mais (o usuário foi apagado em Authentication →
-- Users, o que apaga o profile junto, por cascade), o caminho é a allowlist.
-- A ordem importa: o trigger tk_handle_new_user lê allowed_emails no momento
-- do cadastro, então pré-autorize ANTES de criar a conta na tela de registro.
--
--   insert into public.allowed_emails (email, nome, admin)
--   values (lower('voce@empresa.com'), 'Seu Nome', true)
--   on conflict (email) do update set admin = true;
--
-- (o 03_seed.sql já deixa sistema4713tdi@gmail.com na allowlist como gestor;
--  para esse e-mail basta recadastrar que ele volta ativo e com gestão)
