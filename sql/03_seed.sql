-- =====================================================================
-- 03_seed.sql — dados iniciais do workspace
--
-- Cadastro é aberto: cada pessoa cria a própria conta na tela de registro
-- do app. O que libera o acesso é estar em allowed_emails abaixo — quem
-- não estiver cria login mas não enxerga nada.
--
-- Ajuste os e-mails e os espaços/listas abaixo para os reais de vocês.
-- =====================================================================

-- ---------- Quem pode usar o app ----------
-- gestor = true dá permissão de criar/editar espaços, excluir tarefas
-- de outros e gerenciar esta própria lista.
insert into public.allowed_emails (email, nome, gestor) values
    ('sistema4713tdi@gmail.com', 'Luiz', true)
    -- ('colega2@empresa.com', 'Nome 2', false),
    -- ('colega3@empresa.com', 'Nome 3', false),
    -- ('colega4@empresa.com', 'Nome 4', false),
    -- ('colega5@empresa.com', 'Nome 5', false)
on conflict (email) do nothing;

-- ---------- Espaços ----------
-- 'prefixo' vira o código das tarefas: DEV-101, MKT-101, ...
insert into public.spaces (nome, cor, prefixo, proximo_numero, ordem) values
    ('Engenharia & Dev',   '#6366f1', 'DEV', 101, 1),
    ('Marketing & Vendas', '#ec4899', 'MKT', 101, 2),
    ('Design & UI/UX',     '#10b981', 'DES', 101, 3)
on conflict (prefixo) do nothing;

-- ---------- Listas ----------
insert into public.lists (space_id, nome, icone, ordem)
select s.id, v.nome, v.icone, v.ordem
from (values
    ('DEV', 'Sprint Atual',   'list',   1),
    ('DEV', 'Bugs & Ajustes', 'bug',    2),
    ('DEV', 'Roadmap',        'layers', 3),
    ('MKT', 'Campanhas',      'list',   1),
    ('DES', 'Design System',  'figma',  1)
) as v (prefixo, nome, icone, ordem)
join public.spaces s on s.prefixo = v.prefixo
where not exists (
    select 1 from public.lists l
    where l.space_id = s.id and l.nome = v.nome
);

-- ---------- Perfis de usuários que JÁ existiam ----------
-- O trigger on_auth_user_created_tarefas só dispara em cadastros novos.
-- Este insert cobre quem já estava em auth.users antes do app existir.
insert into public.profiles (id, email, nome, cargo, gestor, ativo)
select u.id,
       u.email,
       coalesce(u.raw_user_meta_data ->> 'nome', a.nome, split_part(u.email, '@', 1)),
       a.cargo,
       coalesce(a.gestor, false),
       a.email is not null
  from auth.users u
  left join public.allowed_emails a on lower(a.email) = lower(u.email)
 where not exists (select 1 from public.profiles p where p.id = u.id);

-- ---------- Sincroniza perfis com a allowlist ----------
-- Rode de novo sempre que adicionar ou promover alguém em allowed_emails.
update public.profiles p
   set email  = u.email,
       gestor = a.gestor,
       ativo  = true,
       nome   = coalesce(a.nome, p.nome),
       cargo  = coalesce(a.cargo, p.cargo)
  from auth.users u
  join public.allowed_emails a on lower(a.email) = lower(u.email)
 where u.id = p.id;

-- ---------- Conferência ----------
-- Rode para verificar que os 5 perfis existem e estão ativos:
--   select p.nome, p.cargo, p.gestor, p.ativo, u.email
--     from public.profiles p join auth.users u on u.id = p.id
--    order by p.nome;
