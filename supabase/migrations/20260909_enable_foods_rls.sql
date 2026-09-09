begin;

-- Restrict access to foods to authenticated users.
-- Group-level access policies will be added in a later migration.

alter table public.foods
enable row level security;

create policy "Authenticated users can read foods"
on public.foods
for select
to authenticated
using (true);

create policy "Authenticated users can add foods"
on public.foods
for insert
to authenticated
with check (true);

create policy "Authenticated users can delete foods"
on public.foods
for delete
to authenticated
using (true);

commit;