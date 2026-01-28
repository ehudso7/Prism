-- 001_init.sql
create table if not exists media (
  id uuid primary key,
  created_at timestamptz not null default now(),
  type text not null,                -- youtube|article|audio|text
  source_url text,
  title text,
  duration_sec int,
  status text not null default 'ingested' -- ingested|processing|ready|error
);

create table if not exists segments (
  id uuid primary key,
  media_id uuid not null references media(id) on delete cascade,
  idx int not null,
  start_sec int,
  end_sec int,
  text text not null
);

create table if not exists lenses (
  id uuid primary key,
  created_at timestamptz not null default now(),
  name text not null,
  description text,
  system_prompt text not null,
  output_schema jsonb not null
);

create table if not exists lens_runs (
  id uuid primary key,
  created_at timestamptz not null default now(),
  media_id uuid not null references media(id) on delete cascade,
  lens_id uuid not null references lenses(id) on delete cascade,
  status text not null default 'queued', -- queued|running|done|error
  result jsonb,
  error text
);

create index if not exists idx_segments_media on segments(media_id, idx);
create index if not exists idx_lens_runs_media on lens_runs(media_id);
