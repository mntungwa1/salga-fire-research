-- Draft installation script for a NEW dedicated study database.
-- Run once in Supabase SQL Editor; not a migration applied to an existing project.
create table public.study_members (
 user_id uuid primary key references auth.users(id) on delete cascade,
 role text not null check (role in ('admin','researcher'))
);
alter table public.study_members enable row level security;
grant select on public.study_members to authenticated;
create policy member_self on public.study_members for select to authenticated
 using (user_id=(select auth.uid()));
-- Membership can only be written through a trusted database administrator.
create table public.study_interviews (
 id uuid primary key,
 owner_id uuid not null references auth.users(id),
 status text not null check(status in ('draft','submitted')),
 instrument_version text not null,
 payload jsonb not null,
 updated_at timestamptz not null default now()
);
alter table public.study_interviews enable row level security;
grant select,insert,update on public.study_interviews to authenticated;
create policy interviews_read on public.study_interviews for select to authenticated
 using (exists(select 1 from public.study_members m where m.user_id=(select auth.uid()) and (m.role='admin' or owner_id=m.user_id)));
create policy interviews_create on public.study_interviews for insert to authenticated
 with check (owner_id=(select auth.uid()) and exists(select 1 from public.study_members m where m.user_id=(select auth.uid())));
create policy interviews_edit on public.study_interviews for update to authenticated
 using (owner_id=(select auth.uid()) and exists(select 1 from public.study_members m where m.user_id=(select auth.uid())))
 with check (owner_id=(select auth.uid()) and exists(select 1 from public.study_members m where m.user_id=(select auth.uid())));
create index interviews_owner_idx on public.study_interviews(owner_id);
create table public.study_evidence (
 id uuid primary key,
 owner_id uuid not null references auth.users(id),
 interview_id uuid references public.study_interviews(id),
 reference text not null,
 description text not null default '',
 path text not null unique,
 filename text not null,
 created_at timestamptz not null default now()
);
alter table public.study_evidence enable row level security;
grant select,insert on public.study_evidence to authenticated;
create policy evidence_read on public.study_evidence for select to authenticated
 using (exists(select 1 from public.study_members m where m.user_id=(select auth.uid()) and (m.role='admin' or owner_id=m.user_id)));
create policy evidence_create on public.study_evidence for insert to authenticated
 with check (owner_id=(select auth.uid()) and split_part(path,'/',1)=(select auth.uid())::text
 and exists(select 1 from public.study_members m where m.user_id=(select auth.uid()))
 and (interview_id is null or exists(select 1 from public.study_interviews i where i.id=interview_id)));
create index evidence_owner_idx on public.study_evidence(owner_id);
create index evidence_interview_idx on public.study_evidence(interview_id);
insert into storage.buckets(id,name,public,file_size_limit)
 values('salga-evidence','salga-evidence',false,10485760);
create policy evidence_file_read on storage.objects for select to authenticated
 using (bucket_id='salga-evidence' and exists(select 1 from public.study_members m where m.user_id=(select auth.uid()) and (m.role='admin' or (storage.foldername(name))[1]=m.user_id::text)));
create policy evidence_file_insert on storage.objects for insert to authenticated
 with check (bucket_id='salga-evidence' and (storage.foldername(name))[1]=(select auth.uid())::text
 and exists(select 1 from public.study_members m where m.user_id=(select auth.uid())));
-- Allows cleanup if metadata insertion fails; no overwrite permissions granted.
create policy evidence_file_cleanup on storage.objects for delete to authenticated
 using (bucket_id='salga-evidence' and (storage.foldername(name))[1]=(select auth.uid())::text
 and exists(select 1 from public.study_members m where m.user_id=(select auth.uid())));
