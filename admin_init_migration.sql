-- 在 Supabase SQL Editor 中执行一次：为首次管理员初始化增加一次性状态记录表
create table if not exists public.app_settings (
  key text primary key,
  value text not null,
  updated_at timestamptz not null default now()
);
-- 本表只由 Streamlit 服务端使用 service_role key 读写；不要在客户端暴露 service_role key。
