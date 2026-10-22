-- Supabase 대시보드 > SQL Editor에 붙여 넣고 Run 해요.
create table if not exists public.entries (
  seq bigserial primary key,
  id text not null unique,
  name text not null check (char_length(name) between 1 and 40),
  message text not null check (char_length(message) between 1 and 500),
  tag text,
  created_at timestamptz not null default now()
);

-- 브라우저에서 직접 접근하지 못하게 막아요. 서버(service role key)만 읽고 써요.
alter table public.entries enable row level security;

-- "새 테이블 자동 공개"를 껐어도 서버 키로 읽고 쓸 수 있게 권한을 줘요.
grant select, insert on public.entries to service_role;
grant usage, select on sequence public.entries_seq_seq to service_role;
