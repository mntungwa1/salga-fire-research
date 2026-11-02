# SALGA Fire Services Research — working app draft

Prepared for Dingaan Mahlangu, 2 November 2026.

This Streamlit starter supports SALGA RFP 2334: concurrent implementation of the two fire services frameworks. It is a separate research workspace inspired by the requested Armoede approach. It does not claim to reproduce Armoede's screens. No GitHub repository, Streamlit deployment or live Supabase database has been created or changed.

## Included

- Overview with programme dates and interview counts.
- Municipal focus-group form: all 23 questions from Instrument 5, with original objective/research/legal anchors.
- Specialised-agency form: all 19 questions from Instrument 6; rating controls where specified, plus narrative responses. Other response formats are captured as text in this draft.
- Draft saving and whole-interview submission. Every question must have a response or an explicit reason for absence before submission.
- Preparation metadata, facilitator consent verification, separate recording verification and downloadable Word interview packs after saving and reopening.
- Document centre with the three supplied source files in their original formats.
- Restricted evidence uploads, evidence references and owner/admin access.
- Filterable sample map and sample register for 18 proposed municipalities.
- Restricted CSV/JSON exports for researchers and administrators.
- Session-only demonstration mode; Supabase sign-in and persistent storage when configured.

## Source governance

The report's internal reference is v1.8.3. The supplied instrument is v1.0 and cites inception report v1.4. The newer report references companion instruments v1.2. Reconcile and approve the definitive instrument before collecting data. The app preserves the supplied v1.0 questions and stamps saved records accordingly; it does not silently invent the missing v1.2 instrument.

The report calls for six core diagnostic domains plus separately scored prevention capability. This draft does not calculate scores because the rubric and source versions require reconciliation. No maturity score, legal compliance conclusion or national prevalence is inferred.

The map's 18 names/categories/typologies follow the supplied map and presentation. Coordinates are approximate illustrative points, not verified municipal centroids, offices, boundaries or risk observations. Confirm names, sample, classifications and authoritative spatial layers before analytical use.

## Run the demonstration

Use Python 3.11 or 3.12 in a virtual environment:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

DEMO_MODE defaults to true. Demonstration saves exist only for the current browser session. Do not enter real interview data in demonstration mode. It is intended for layout/workflow review.

## Configure Supabase

1. Select a dedicated project. In its SQL Editor run `schema.sql` once. The file is a draft installation script, not a migration for an existing database. If integrating into an existing project, inspect its tables and storage policies before adapting it.
2. Create the administrator and researcher accounts under Authentication → Users. Set up passwords/invitation delivery through Supabase's own supported account flow. Disable public sign-ups for this invited research workspace.
3. Add each account to `study_members` using its Auth user UUID:

```sql
insert into public.study_members(user_id, role)
values ('REPLACE_WITH_AUTH_USER_UUID', 'admin');
-- Repeat with role 'researcher' for research staff.
```

4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` locally, or paste its contents into Streamlit Cloud's Secrets settings. Enter the project URL and publishable key. Set DEMO_MODE=false. Never put an actual secrets file in GitHub.
5. Start the app and sign in. Researchers can read and edit their own interviews and evidence. Administrators can read all records and export them; they cannot impersonate owners or edit other researchers' interviews. Membership has no client write policy. There is no client-reviewer role in this draft.
6. Verify the Data API exposes these tables and confirm all SQL grants and row policies are present. Run Supabase's security advisors.

Authentication uses the caller's user session and a publishable key, not a service-role key. Each Streamlit browser session gets its own Supabase client. Storage is a private `salga-evidence` bucket with owner/admin download policies. No cross-user data is globally cached. Live configuration failures stop the app; they do not switch to demonstration mode.

## GitHub and Streamlit deployment

Create a dedicated **private** repository such as `salga-fire-research`. Upload this folder's contents, including `app.py`, `requirements.txt`, `data`, `documents`, `.streamlit/config.toml` and `schema.sql`. Do not upload credentials or collected evidence. The bundled source documents contain project details and business contact information; retain restricted repository access.

In Streamlit Community Cloud select that repository and `app.py` as entry point. Use Python 3.11/3.12 and configure the Secrets settings above with DEMO_MODE=false. App users sign in through Supabase; they should not need a ChatGPT account. Hosting/repository access configuration must be checked during deployment.

The document files are packaged with code so authenticated study members can download them. New versions can be committed through GitHub. Uploaded research evidence and interview responses belong in Supabase, not the repository or Streamlit's ephemeral disk. Office/ODT files are downloadable; inline PDF previews, document upload/version control and document comments remain future work.

## Required live acceptance checks

Use fictional test records before real data collection:

- Researcher A saves and reopens a draft; submits after all questions and participation consent are addressed. Recording remains optional.
- Researcher B cannot read A's interview, evidence metadata or storage object, including direct API calls.
- An authenticated non-member cannot read project data; an unauthenticated request cannot access data/storage.
- The administrator can read/export both researchers' records but cannot edit someone else's interview or change membership through the application.
- Oversized evidence is rejected; a metadata failure attempts cleanup of the uploaded object.
- Exported responses and Word packs preserve question IDs and the v1.0 source wording.
- Test expired sessions, wrong passwords, sign-out, database interruption, simultaneous users and the no-secrets live configuration.

Database policies are drafted but have not been executed against a live project in this delivery. The included verification report describes local checks only.

## Next design phase

Agree researcher assignments and client access separately. Add approved municipal/FPA polygon layers and engagement status tracking; a versioned question bank; consent ledger and withdrawal workflow; seven-domain scored evidence with reviewed rubric/weights; statutory concordance, mechanisms and fiscal analysis; options appraisal; immutable audit and approval history; and disclosure-reviewed anonymised handover exports.

Submission is a completeness flag in this draft, not an immutable approval lock. Blank answers remain missing evidence. All exports are restricted research exports and can contain identifiable institutional information and free text. Anonymisation requires manual disclosure review before SALGA handover. Do not give client viewers researcher/admin roles. Individual participant identity keys, signatures and recordings require separately approved storage and retention handling. The app does not enforce the protocol's retention/destruction timetable yet.

## Documentation consulted

- https://docs.streamlit.io/develop/api-reference/execution-flow/st.form
- https://supabase.com/docs/reference/python/auth-signinwithpassword
- https://supabase.com/docs/reference/python/storage-from-download
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/changelog.md (reviewed 2 November 2026)
