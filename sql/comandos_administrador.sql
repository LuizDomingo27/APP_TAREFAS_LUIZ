-- =====================================================================
-- comandos_administrador.sql — caixa de ferramentas do gestor
--
-- ATENÇÃO: este arquivo NÃO é migração. Não rode ele inteiro.
--
-- Diferente dos numerados (01 a 07), que são aplicados uma vez e na ordem,
-- aqui é uma coleção de comandos avulsos para consultar e consertar acesso.
-- No SQL Editor do Supabase, selecione o bloco que você quer e dê Ctrl+Enter
-- (ou Cmd+Enter) — o editor roda só o que está selecionado.
--
-- Os blocos 1 a 4 são de leitura: não mudam nada, pode rodar à vontade.
-- Do 5 em diante escrevem no banco; cada um diz quando deve ser usado.
--
-- Onde aparecer 'sistema4713tdi@gmail.com', troque pelo e-mail que interessa.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. A migração 07 já foi aplicada?
--
-- Vários comandos abaixo citam a coluna `admin`, que só existe depois do
-- 07_admin.sql. Se este bloco devolver `tem_coluna_admin = false`, rode o
-- 07_admin.sql antes e, nas consultas seguintes, tire as referências a
-- `admin` (troque `(gestor or admin)` por `gestor`).
-- ---------------------------------------------------------------------

select exists (
           select 1 from information_schema.columns
            where table_schema = 'public' and table_name = 'profiles'
              and column_name = 'admin'
       ) as tem_coluna_admin,
       exists (
           select 1 from pg_trigger
            where tgname = 'profiles_guarda_acesso'
       ) as tem_trava_de_acesso;


-- ---------------------------------------------------------------------
-- 2. O usuário existe? Em que estado?
--
-- Mostra os dois lados — o login (auth.users) e o perfil (profiles) —
-- porque some um sem o outro:
--
--   nenhuma linha ............. apagado em Authentication -> Users
--   tem_perfil = false ........ o login existe, só o perfil sumiu
--   ativo=false, recusado=true  não foi apagado: foi DESATIVADO pela tela
--   login_apagado preenchido .. soft delete do Supabase
-- ---------------------------------------------------------------------

select u.email,
       u.id,
       u.created_at            as login_criado,
       u.deleted_at            as login_apagado,
       p.id is not null        as tem_perfil,
       p.ativo,
       p.gestor,
       p.admin,
       p.recusado
  from auth.users u
  full outer join public.profiles p on p.id = u.id
 order by u.created_at nulls last;


-- ---------------------------------------------------------------------
-- 3. Sobrou alguém que possa gerenciar?
--
-- É a consulta que diz se o workspace está travado. `podem_gerenciar = 0`
-- significa que ninguém libera acesso pelo app — a saída é o bloco 5.
-- ---------------------------------------------------------------------

select count(*)                                             as perfis,
       count(*) filter (where ativo)                        as ativos,
       count(*) filter (where ativo and (gestor or admin))  as podem_gerenciar,
       count(*) filter (where not ativo and not recusado)   as pendentes,
       count(*) filter (where recusado)                     as desativados
  from public.profiles;

-- A equipe inteira, linha a linha:
select nome, email, ativo, gestor, admin, recusado, criado_em
  from public.profiles
 order by ativo desc, nome;


-- ---------------------------------------------------------------------
-- 4. Foi apagado mesmo? Quando, e por quem?
--
-- Trilha de auditoria do Auth. Procure a ação `user_deleted`. Se não houver
-- nenhuma, o login nunca foi apagado — o que houve foi desativação, ou
-- remoção direta da linha de profiles (essa NÃO aparece aqui: a auditoria
-- cobre só o schema `auth`).
-- ---------------------------------------------------------------------

select created_at,
       payload ->> 'action'                  as acao,
       payload ->> 'actor_email'             as quem_fez,
       payload -> 'traits' ->> 'user_email'  as alvo
  from auth.audit_log_entries
 order by created_at desc
 limit 50;


-- ---------------------------------------------------------------------
-- 5. Recuperar o próprio acesso
--
-- Use quando o bloco 3 mostrar `podem_gerenciar = 0`, ou quando o bloco 2
-- mostrar seu perfil com ativo = false.
--
-- O `returning` é o que interessa: UMA linha = acesso de volta, é só
-- recarregar o app. ZERO linhas = o perfil não existe mais, siga para o 5b.
--
-- Fica com `gestor` (e não `admin`) porque este bloco precisa funcionar
-- mesmo antes do 07_admin.sql. Para virar Admin, veja o bloco 6.
-- ---------------------------------------------------------------------

-- 5a. O perfil existe e está desativado:
update public.profiles
   set ativo = true, recusado = false, gestor = true
 where lower(email) = lower('sistema4713tdi@gmail.com')
returning nome, email, ativo, gestor, recusado;

-- 5b. O perfil sumiu, mas o login continua em auth.users:
insert into public.profiles (id, email, nome, gestor, ativo)
select u.id,
       u.email,
       coalesce(u.raw_user_meta_data ->> 'nome', split_part(u.email, '@', 1)),
       true,
       true
  from auth.users u
 where lower(u.email) = lower('sistema4713tdi@gmail.com')
   and not exists (select 1 from public.profiles p where p.id = u.id)
returning nome, email, ativo, gestor;

-- 5c. Nem o login existe (foi apagado em Authentication -> Users):
--     pré-autorize o e-mail e crie a conta de novo pela tela de registro.
--     A ORDEM IMPORTA: o trigger tk_handle_new_user lê allowed_emails no
--     momento do cadastro, então rode isto ANTES de se cadastrar.
insert into public.allowed_emails (email, nome, gestor)
values (lower('sistema4713tdi@gmail.com'), 'Luiz', true)
on conflict (email) do update set gestor = true;


-- ---------------------------------------------------------------------
-- 6. Mudar o papel de alguém
--
-- Gestor e Admin têm exatamente os mesmos poderes; muda só o rótulo na
-- tela. Exige o 07_admin.sql aplicado (bloco 1).
--
-- O normal é fazer isso pela tela de Equipe. Aqui é para quando a tela
-- está inalcançável — ou para o caso que a tela recusa de propósito:
-- alterar o próprio acesso. No SQL Editor `auth.uid()` é nulo, então a
-- trava não dispara.
-- ---------------------------------------------------------------------

update public.profiles
   set admin = true, gestor = false          -- Admin
 where lower(email) = lower('sistema4713tdi@gmail.com')
returning nome, email, gestor, admin;

-- Gestor:  set gestor = true,  admin = false
-- Membro:  set gestor = false, admin = false
--          (a trava do banco recusa se for a última pessoa com gestão)


-- ---------------------------------------------------------------------
-- 7. Allowlist — quem já entra liberado
--
-- Um e-mail aqui pula a fila de aprovação: ao se cadastrar, o perfil já
-- nasce ativo e com o papel indicado.
-- ---------------------------------------------------------------------

select email, nome, gestor, admin, convidado_em
  from public.allowed_emails
 order by email;

-- Adicionar (ou atualizar o papel de) um convite:
insert into public.allowed_emails (email, nome, gestor, admin)
values (lower('colega@empresa.com'), 'Nome do Colega', false, false)
on conflict (email) do update
   set nome   = excluded.nome,
       gestor = excluded.gestor,
       admin  = excluded.admin;

-- Remover um convite (não mexe em quem já se cadastrou):
delete from public.allowed_emails
 where lower(email) = lower('colega@empresa.com');


-- ---------------------------------------------------------------------
-- 8. Desativar alguém pelo banco
--
-- Comentado de propósito: é exatamente o comando que zerou o workspace uma
-- vez. O caminho certo é o botão "Desativar" na tela de Equipe, que checa
-- as travas antes. Se for rodar aqui mesmo assim, rode o bloco 3 antes e
-- confira que `podem_gerenciar` continua >= 1 depois.
--
-- O trigger `profiles_guarda_acesso` recusa se sobrar zero gestão — mas
-- não protege contra desativar a pessoa errada.
-- ---------------------------------------------------------------------

-- update public.profiles
--    set ativo = false, recusado = true
--  where lower(email) = lower('quem@empresa.com')
-- returning nome, email, ativo, recusado;


-- estecomando mostra se a trava está ativa, e o estado do perfil:
select exists (select 1 from pg_trigger where tgname='profiles_guarda_acesso') as trava_ativa,
       p.nome, p.email, p.ativo, p.gestor, p.admin, p.recusado
  from public.profiles p
 where lower(p.email) = lower('sistema4713tdi@gmail.com');

-- este comando deixa qualquer perfil Admin, mesmo que o trigger esteja ativo. Use com cuidado.
update public.profiles set admin = true, gestor = false
 where lower(email) = lower('sistema4713tdi@gmail.com')
returning nome, email, gestor, admin;