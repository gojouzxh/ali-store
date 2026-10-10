alter table public.birds
  alter column scientific_name drop not null,
  alter column family drop not null,
  alter column category drop not null,
  alter column iucn_status drop not null,
  alter column source_note drop not null,
  alter column field_notes drop not null,
  alter column availability drop not null,
  alter column photo_alt drop not null;

alter table public.birds
  add constraint birds_published_requires_complete_data
    check (
      not is_published
      or (
        nullif(btrim(scientific_name), '') is not null
        and nullif(btrim(family), '') is not null
        and category is not null
        and iucn_status is not null
        and source_note is not null
        and field_notes is not null
        and availability is not null
        and photo_alt is not null
      )
    ),
  add constraint birds_photo_requires_alt
    check (photo_path is null or photo_alt is not null);
