-- Run in Supabase: SQL Editor -> New query

create table public.users (
  id uuid primary key default gen_random_uuid(),
  guardian_name text not null,
  student_name text not null,
  email text not null,
  phone text,
  created_at timestamptz not null default now(),
  unique (email, student_name)
);

-- One row per WEEKLY slot. Booking a slot claims it every week.
create table public.availabilities (
  id uuid primary key default gen_random_uuid(),
  day_of_week smallint not null check (day_of_week between 0 and 6), -- 0 = Monday ... 6 = Sunday
  start_time time not null,
  is_booked boolean not null default false,
  user_id uuid references public.users(id) on delete set null,
  subject text,
  notes text,
  wants_recurring boolean not null default false,
  wants_multiple_per_week boolean not null default false,
  booked_at timestamptz,
  unique (day_of_week, start_time)
);

-- Lock both tables to the public API. The Flask server uses the service_role
-- key, which bypasses RLS. With no policies, the anon key can read nothing.
alter table public.users enable row level security;
alter table public.availabilities enable row level security;

-- Readable view for browsing bookings in the Supabase table editor.
-- security_invoker keeps RLS applied, so it is NOT publicly readable.
create view public.bookings_view with (security_invoker = true) as
select
  a.id as slot_id,
  (array['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])[a.day_of_week + 1] as day,
  a.start_time,
  u.guardian_name, u.student_name, u.email, u.phone,
  a.subject, a.notes, a.wants_recurring, a.wants_multiple_per_week, a.booked_at
from public.availabilities a
join public.users u on u.id = a.user_id
where a.is_booked
order by a.day_of_week, a.start_time;

-- Seed: Monday-Friday, 5:00 / 5:30 / 6:00 / 6:30 PM
insert into public.availabilities (day_of_week, start_time)
select d, t::time
from generate_series(0, 4) as d,
     unnest(array['17:00', '17:30', '18:00', '18:30']) as t;

-- To re-open a slot manually later:
-- update public.availabilities
--   set is_booked = false, user_id = null, subject = null, notes = null,
--       wants_recurring = false, wants_multiple_per_week = false, booked_at = null
--   where id = '<slot id>';
