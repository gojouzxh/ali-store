create extension if not exists pgcrypto;

create table public.staff_users (
  user_id uuid primary key references auth.users (id) on delete cascade,
  created_at timestamptz not null default now()
);

create table public.birds (
  id uuid primary key default gen_random_uuid(),
  common_name text not null,
  scientific_name text not null,
  family text not null,
  category text not null,
  hatch_info text not null default '',
  lifespan text not null default '',
  wingspan text not null default '',
  habitat text not null default '',
  diet text not null default '',
  iucn_status text not null default 'NE'
    check (iucn_status in ('LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX', 'DD', 'NE')),
  iucn_checked_at date,
  source_note text not null default '',
  call text not null default '',
  field_notes text not null default '',
  availability text not null default 'sold'
    check (availability in ('available', 'reserved', 'sold')),
  quantity_available integer
    check (quantity_available is null or quantity_available >= 0),
  photo_path text,
  photo_alt text not null default '',
  is_approved boolean not null default false,
  is_published boolean not null default false,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint birds_published_requires_approval
    check (not is_published or is_approved),
  constraint birds_category_allowed
    check (category in ('raptor', 'water', 'tropical', 'budgie', 'lovebird')),
  constraint birds_photo_path_matches_id
    check (photo_path is null or split_part(photo_path, '/', 1) = id::text)
);

create function public.is_aviary_staff()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.staff_users
    where user_id = auth.uid()
  );
$$;

revoke all on function public.is_aviary_staff() from public;
grant execute on function public.is_aviary_staff() to anon, authenticated;

create function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger birds_set_updated_at
before update on public.birds
for each row
execute function public.set_updated_at();

alter table public.staff_users enable row level security;
alter table public.birds enable row level security;

revoke all on public.staff_users from public, anon, authenticated;

grant select on public.birds to authenticated;
grant insert, update, delete on public.birds to authenticated;
revoke all on public.birds from public, anon;

create policy "Public can read approved published birds"
on public.birds
for select
to anon, authenticated
using (is_approved and is_published);

create policy "Staff can read all birds"
on public.birds
for select
to authenticated
using ((select public.is_aviary_staff()));

create policy "Staff can insert birds"
on public.birds
for insert
to authenticated
with check ((select public.is_aviary_staff()));

create policy "Staff can update birds"
on public.birds
for update
to authenticated
using ((select public.is_aviary_staff()))
with check ((select public.is_aviary_staff()));

create policy "Staff can delete birds"
on public.birds
for delete
to authenticated
using ((select public.is_aviary_staff()));

create view public.birds_public
with (security_barrier = true, security_invoker = false)
as
select
  id,
  common_name,
  scientific_name,
  family,
  category,
  hatch_info,
  lifespan,
  wingspan,
  habitat,
  diet,
  iucn_status,
  iucn_checked_at,
  source_note,
  call,
  field_notes,
  availability,
  quantity_available,
  photo_path,
  photo_alt,
  sort_order
from public.birds
where is_approved and is_published;

revoke all on public.birds_public from public, anon, authenticated;
grant select on public.birds_public to anon, authenticated;

create function public.is_published_bird_folder(object_name text)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.birds as bird
    where bird.id::text = split_part(object_name, '/', 1)
      and bird.is_approved
      and bird.is_published
  );
$$;

revoke all on function public.is_published_bird_folder(text) from public;
grant execute on function public.is_published_bird_folder(text) to anon, authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'bird-photos',
  'bird-photos',
  false,
  5242880,
  array['image/jpeg', 'image/png', 'image/webp']
)
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create policy "Public reads published bird photos; staff read all"
on storage.objects
for select
to anon, authenticated
using (
  bucket_id = 'bird-photos'
  and (
    (select public.is_aviary_staff())
    or (
      name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[A-Za-z0-9][A-Za-z0-9._-]*[.](jpg|jpeg|png|webp)$'
      and (select public.is_published_bird_folder(storage.objects.name))
    )
  )
);

create policy "Staff can upload bird photos"
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'bird-photos'
  and (select public.is_aviary_staff())
  and name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[A-Za-z0-9][A-Za-z0-9._-]*[.](jpg|jpeg|png|webp)$'
  and exists (
    select 1
    from public.birds
    where birds.id::text = split_part(storage.objects.name, '/', 1)
  )
);

create policy "Staff can update bird photos"
on storage.objects
for update
to authenticated
using (
  bucket_id = 'bird-photos'
  and (select public.is_aviary_staff())
  and name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[A-Za-z0-9][A-Za-z0-9._-]*[.](jpg|jpeg|png|webp)$'
)
with check (
  bucket_id = 'bird-photos'
  and (select public.is_aviary_staff())
  and name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[A-Za-z0-9][A-Za-z0-9._-]*[.](jpg|jpeg|png|webp)$'
  and exists (
    select 1
    from public.birds
    where birds.id::text = split_part(storage.objects.name, '/', 1)
  )
);

create policy "Staff can delete bird photos"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'bird-photos'
  and (select public.is_aviary_staff())
  and name ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[A-Za-z0-9][A-Za-z0-9._-]*[.](jpg|jpeg|png|webp)$'
);
