begin;

alter table public.birds
  drop constraint if exists birds_category_check,
  drop constraint if exists birds_category_allowed;

alter table public.birds
  add constraint birds_category_allowed
    check (category in ('raptor', 'water', 'tropical', 'budgie', 'lovebird'));

commit;
