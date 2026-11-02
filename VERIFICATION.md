# Local verification — 2 November 2026

Passed in Python 3.12 with the pinned requirements installed:

- All six workspace pages rendered in Streamlit AppTest without application exceptions.
- Extracted 23 municipal questions and 19 agency questions from the supplied DOCX tables.
- Municipal draft saved in demonstration session state; draft reopened and Word download offered.
- Agency route rendered with rating and narrative controls.
- Incomplete submission was blocked.
- Live mode without Supabase settings stopped with a setup message.
- Python source compilation passed.

No live Supabase or hosted Streamlit connection was used for these tests. SQL, row security, uploads, multi-user isolation and production session behaviour require the live acceptance checks listed in README. The map was checked for rendering; point accuracy is deliberately approximate and unverified.
