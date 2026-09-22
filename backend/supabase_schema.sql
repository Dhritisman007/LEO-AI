-- LEO Supabase schema
-- Paste this into the Supabase SQL editor.

create extension if not exists vector;

-- ── workspace_files ──────────────────────────────────────────────
-- Metadata for files LEO writes to Supabase Storage (bucket: leo-workspace)
create table if not exists workspace_files (
    id           uuid primary key default gen_random_uuid(),
    user_id      text not null,
    filename     text not null,
    storage_path text not null,
    size_bytes   bigint default 0,
    content_type text,
    updated_at   double precision not null default extract(epoch from now()),
    created_at   double precision not null default extract(epoch from now()),
    unique (user_id, filename)
);

create index if not exists idx_workspace_files_user_id on workspace_files (user_id);

create or replace function set_workspace_files_updated_at()
returns trigger as $$
begin
    new.updated_at = extract(epoch from now());
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_workspace_files_updated_at on workspace_files;
create trigger trg_workspace_files_updated_at
    before update on workspace_files
    for each row
    execute function set_workspace_files_updated_at();


-- ── leo_memories ─────────────────────────────────────────────────
-- Past tasks LEO recalls for context (keyword-overlap scoring for now)
create table if not exists leo_memories (
    id           uuid primary key default gen_random_uuid(),
    user_id      text not null,
    task         text not null,
    final_answer text,
    success      boolean default true,
    created_at   double precision not null default extract(epoch from now())
);

create index if not exists idx_leo_memories_user_id on leo_memories (user_id);
create index if not exists idx_leo_memories_created_at on leo_memories (created_at);


-- ── tasks ────────────────────────────────────────────────────────
create table if not exists tasks (
    id           text primary key,
    user_id      text not null,
    task         text not null,
    language     text,
    status       text not null,
    steps_taken  integer default 0,
    max_steps    integer default 10,
    duration_ms  integer default 0,
    tools_used   jsonb default '[]'::jsonb,
    model        text default 'gemini-1.5-flash',
    input_chars  integer default 0,
    output_chars integer default 0,
    created_at   double precision not null default extract(epoch from now())
);

create index if not exists idx_tasks_user_id on tasks (user_id);
create index if not exists idx_tasks_created_at on tasks (created_at);


-- ── tool_calls ───────────────────────────────────────────────────
create table if not exists tool_calls (
    id          bigint generated always as identity primary key,
    task_id     text not null references tasks (id) on delete cascade,
    user_id     text not null,
    tool_name   text not null,
    success     boolean default true,
    duration_ms integer default 0,
    created_at  double precision not null default extract(epoch from now())
);

create index if not exists idx_tool_calls_user_id on tool_calls (user_id);
create index if not exists idx_tool_calls_task_id on tool_calls (task_id);
create index if not exists idx_tool_calls_created_at on tool_calls (created_at);


-- ── checkpoints ──────────────────────────────────────────────────
create table if not exists checkpoints (
    id                text primary key,
    user_id           text not null,
    task              text not null,
    history           jsonb default '[]'::jsonb,
    steps             jsonb default '[]'::jsonb,
    plan              jsonb default '[]'::jsonb,
    current_plan_idx  integer default 0,
    created_at        double precision not null default extract(epoch from now()),
    expires_at        double precision
);

create index if not exists idx_checkpoints_user_id on checkpoints (user_id);
create index if not exists idx_checkpoints_expires_at on checkpoints (expires_at);


-- ── daily_stats ──────────────────────────────────────────────────
create table if not exists daily_stats (
    date               text not null,
    user_id            text not null,
    tasks_total        integer default 0,
    tasks_success      integer default 0,
    tasks_error        integer default 0,
    tool_calls         integer default 0,
    total_duration_ms  integer default 0,
    estimated_cost_usd double precision default 0.0,
    primary key (date, user_id)
);

create index if not exists idx_daily_stats_user_id on daily_stats (user_id);
