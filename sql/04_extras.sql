-- =====================================================================
-- 04_extras.sql — ajustes de apoio à tela de Equipe
-- Rode DEPOIS de 03_seed.sql.
-- =====================================================================

-- Sem esta coluna, "Recusar" não teria como se distinguir de "ainda não
-- olhei": os dois estados seriam ativo = false, e o recusado voltaria à
-- lista de pendentes toda vez que a tela recarregasse.
alter table public.profiles
    add column if not exists recusado boolean not null default false;

-- Pendentes = quem se cadastrou, não foi liberado e não foi recusado.
create index if not exists profiles_pendentes_idx
    on public.profiles (criado_em)
    where not ativo and not recusado;
