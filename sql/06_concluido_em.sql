-- =====================================================================
-- 06_concluido_em.sql — data real da entrega da tarefa
--
-- Rode uma vez no SQL Editor do Supabase, em bancos que já existiam antes
-- desta mudança. Instalações novas já saem prontas: o 01_schema.sql traz a
-- coluna e o trigger. Rodar de novo não faz mal (tudo é idempotente).
--
-- POR QUE ESTA COLUNA EXISTE
-- O painel usava `atualizado_em` como data de conclusão. Só que o trigger
-- `tasks_touch` carimba `atualizado_em` a cada UPDATE — trocar uma tag ou
-- corrigir o título empurra a data para frente. Resultado: tarefa entregue
-- no prazo e editada depois passava a exibir "Concluído com X dia(s) de
-- atraso" na aba "Situação por Usuário" do dashboard.
--
-- `concluido_em` só é escrito na transição para 'Concluído', então não anda
-- sozinho. Sai da coluna quando a tarefa é reaberta: se voltou para "Em
-- Progresso", não existe mais entrega para datar.
-- =====================================================================

alter table public.tasks
    add column if not exists concluido_em timestamptz;

comment on column public.tasks.concluido_em is
    'Momento em que a tarefa entrou em Concluído. Escrito só pelo trigger '
    'tasks_set_concluido_em; nulo enquanto não foi entregue. Não confundir '
    'com atualizado_em, que muda a cada edição.';


create or replace function public.tk_set_concluido_em()
returns trigger
language plpgsql
as $$
begin
    if new.status = 'Concluído' then
        -- Só carimba na entrada em "Concluído". Update seguinte numa tarefa
        -- que já estava concluída não mexe na data (é justo o bug antigo).
        if tg_op = 'INSERT' or old.status is distinct from 'Concluído' then
            new.concluido_em := coalesce(new.concluido_em, now());
        end if;
    else
        -- Reabriu: a entrega deixou de existir, a data vai junto.
        new.concluido_em := null;
    end if;
    return new;
end $$;

drop trigger if exists tasks_set_concluido_em on public.tasks;
create trigger tasks_set_concluido_em
    before insert or update on public.tasks
    for each row execute function public.tk_set_concluido_em();


-- ---------- Backfill do histórico ----------
-- Para quem já estava concluído, `atualizado_em` é a melhor estimativa que
-- existe da data de entrega (exata para quem não foi editado depois). É uma
-- aproximação assumida: sem esta coluna, o dado real nunca foi guardado.
--
-- O UPDATE dispara o `tasks_touch` e leva o `atualizado_em` dessas linhas
-- para agora. Isso é inofensivo: o valor antigo acabou de ser preservado em
-- `concluido_em`, e `atualizado_em` volta ao seu único papel, que é detectar
-- edição concorrente (`tasks.atualizar`, campo `visto_em`).
update public.tasks
   set concluido_em = atualizado_em
 where status = 'Concluído'
   and concluido_em is null;
