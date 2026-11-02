from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid4
from io import BytesIO
import json, os, re
import pandas as pd
import streamlit as st
from docx import Document

ROOT = Path(__file__).parent
QUESTIONS = json.loads((ROOT/'data/questions.json').read_text())
st.set_page_config(page_title='SALGA | Fire Services Research', page_icon='🔥', layout='wide')
st.title('SALGA Fire Services Research')
st.caption('RFP 2334 · Interview preparation, evidence and municipal coverage')

def setting(key, default=''):
    if key in os.environ: return os.environ[key]
    try: return st.secrets.get(key, default)
    except FileNotFoundError: return default

# No globally cached authenticated client: each browser session has its own client.
try:
    demo = str(setting('DEMO_MODE', 'true')).lower() == 'true'
except FileNotFoundError:
    demo = os.environ.get('DEMO_MODE', 'true').lower() == 'true'
if demo:
    st.warning('DEMONSTRATION — changes last only in this browser session. Use fictional information. No database connection.')
    uid, admin = 'demo-researcher', True
else:
    from supabase import create_client
    if 'client' not in st.session_state:
        url, key = setting('SUPABASE_URL'), setting('SUPABASE_PUBLISHABLE_KEY')
        if not url or not key:
            st.error('Administrator setup required: configure Supabase URL and publishable key.'); st.stop()
        st.session_state.client = create_client(url, key)
    client = st.session_state.client
    if not client.auth.get_session():
        st.caption('Use your Supabase Auth email and password. APP_PASSWORD and ADMIN_PASSWORD in Streamlit Secrets do not set this password.')
        with st.form('login'):
            email=st.text_input('Email'); password=st.text_input('Password', type='password')
            if st.form_submit_button('Sign in'):
                if not email.strip() or not password:
                    st.error('Enter your email and password.')
                else:
                    try:
                        client.auth.sign_in_with_password({'email':email.strip(),'password':password})
                        st.rerun()
                    except Exception as exc:
                        code = str(getattr(exc, 'code', ''))
                        if code == 'email_not_confirmed':
                            st.error('Your email has not been confirmed. Use Resend confirmation email below, open the confirmation link in your inbox, then return here and sign in.')
                        elif code in {'invalid_credentials', 'invalid_grant'}:
                            st.error('The email or Supabase Auth password is incorrect. This is not your Streamlit APP_PASSWORD, ADMIN_PASSWORD or Supabase dashboard password.')
                        elif code in {'over_request_rate_limit', 'over_email_send_rate_limit'}:
                            st.error('Too many attempts. Wait a few minutes before trying again.')
                        else:
                            st.error('Sign-in could not be completed. Check the Supabase connection settings or contact the project administrator.')
        with st.expander('Email confirmation help'):
            st.write('If your account email is unconfirmed, request a new confirmation message. Open the link in your email, then return to this app to sign in. No password is changed.')
            with st.form('resend_confirmation'):
                confirm_email = st.text_input('Email to confirm')
                send_confirmation = st.form_submit_button('Resend confirmation email')
            if send_confirmation:
                import time
                if not confirm_email.strip() or '@' not in confirm_email:
                    st.error('Enter a valid email address.')
                elif time.time() - st.session_state.get('last_confirmation_request', 0) < 60:
                    st.info('Please wait at least one minute before requesting another email.')
                else:
                    try:
                        client.auth.resend({'type':'signup', 'email':confirm_email.strip()})
                        st.session_state.last_confirmation_request = time.time()
                        st.success('Confirmation requested. If this account is eligible, check your inbox and spam folder, open the confirmation link, then return here to sign in.')
                    except Exception as exc:
                        code = str(getattr(exc, 'code', ''))
                        if code in {'over_request_rate_limit', 'over_email_send_rate_limit'}:
                            st.error('Email limit reached. Wait a few minutes, then try again.')
                        else:
                            st.error('The confirmation request failed. Please ask the administrator to check Supabase email delivery.')
        st.stop()
    if st.sidebar.button('Sign out'):
        client.auth.sign_out(); st.session_state.clear(); st.rerun()
    try:
        uid = str(client.auth.get_user().user.id)
        membership = client.table('study_members').select('role').eq('user_id',uid).execute().data
        if not membership:
            st.error('This account has not been granted access to this study.'); st.stop()
        admin = membership[0]['role']=='admin'
    except Exception:
        st.error('Unable to validate project access. Please sign in again.'); st.stop()


def records():
    if demo: return st.session_state.setdefault('records', [])
    return client.table('study_interviews').select('*').order('updated_at',desc=True).execute().data

def save_record(record):
    record['owner_id']=uid
    record['updated_at']=datetime.now(ZoneInfo('Africa/Johannesburg')).isoformat()
    if demo:
        rows=st.session_state.setdefault('records',[])
        rows[:]=[r for r in rows if r['id']!=record['id']]; rows.append(record)
    else:
        client.table('study_interviews').upsert(record).execute()

def packet(record):
    d=Document();d.add_heading('SALGA Fire Services Research — Interview Pack',0)
    p=record['payload']
    for label in ['institution','instrument','scheduled','facilitator','roles','consent_checked','recording_allowed']:
        d.add_paragraph(f'{label.replace("_"," ").title()}: {p.get(label, "")}')
    d.add_paragraph('Use participant codes. Keep signed individual consent and identity keys separately in restricted custody. Recording requires separate agreement from every participant.')
    for q in QUESTIONS:
        if q['instrument']==p['instrument']:
            d.add_heading(q['id']+' · '+q['section'],2);d.add_paragraph(q['text']);d.add_paragraph(q['anchor'])
            a=p.get('answers',{}).get(q['id'],{})
            d.add_paragraph('Response: '+a.get('text',''));d.add_paragraph('Evidence reference: '+a.get('evidence',''))
    b=BytesIO();d.save(b);return b.getvalue()

page=st.sidebar.radio('Workspace',['Overview','Interview workspace','Documents','Evidence register','Coverage map','Exports and administration'])
st.sidebar.caption('Developed by Dingaan Mahlangu')
try:
    rows=records()
except Exception:
    st.error('Unable to load interviews. Check database setup and project access.');st.stop()

if page=='Overview':
    a,b,c=st.columns(3);a.metric('Planned municipal engagements',18);b.metric('Saved records',len(rows));c.metric('Submitted records',sum(r['status']=='submitted' for r in rows))
    st.write('Prepare the engagement, check consent, capture municipal or agency responses, link documentary evidence, then submit the complete record for analysis.')
    st.info('Source control: report v1.8.3; instruments v1.0 (linked to report v1.4). Instrument approval and reconciliation are required before field use.')
    st.dataframe(pd.DataFrame([
        ['20 November 2026','Inception Report'],['23–27 November 2026','Pre-test with two Chief Fire Officers'],
        ['30 November 2026–29 January 2027','Fieldwork windows'],['12 February 2027','Diagnostic Analysis'],
        ['19 February 2027','Mechanisms Map'],['5 March 2027','Proposed Operational Models'],
        ['10 March 2027','Draft Project Report'],['31 March 2027','Final Project Report']
    ],columns=['Date','Milestone']),hide_index=True)
    st.caption('Dates and sample are drawn from the supplied project documents and remain subject to project approval. No national prevalence estimate or compliance score is calculated.')

elif page=='Interview workspace':
    own=[r for r in rows if r['owner_id']==uid]
    selection=st.selectbox('Open record',['New interview']+[r['id'] for r in own],format_func=lambda x: x if x=='New interview' else next(r['payload']['institution']+' · '+r['status']+' · '+x[:8] for r in own if r['id']==x),key='record_selection')
    if selection=='New interview':
        if 'new_id' not in st.session_state:st.session_state.new_id=str(uuid4())
        rid=st.session_state.new_id; old={}
    else:
        rid=selection;old=next(r['payload'] for r in own if r['id']==rid)
    instrument=st.radio('Interview route',[5,6],format_func=lambda x:'Municipal focus group · Instrument 5' if x==5 else 'Specialised agency survey · Instrument 6',index=0 if old.get('instrument',5)==5 else 1,key='route_'+rid)
    st.caption('Exact supplied questions are retained. Empty answers and unavailable evidence remain explicit gaps; they are not converted into zero scores.')
    with st.form('interview_'+rid):
        institution=st.text_input('Municipality or agency',old.get('institution',''))
        scheduled=st.text_input('Proposed date and time (South Africa)',old.get('scheduled',''))
        facilitator=st.text_input('Facilitator code',old.get('facilitator',''))
        roles=st.text_area('Participant codes and official roles (no names or contact details)',old.get('roles',''))
        consent=st.checkbox('Facilitator confirms separate signed participation consent for all participants',old.get('consent_checked',False))
        recording=st.checkbox('Separate recording consent checked for every participant',old.get('recording_allowed',False))
        st.caption('These checks record facilitator verification; they do not replace the signed Instrument 4 consent forms. Participation without recording is permitted.')
        answers={}
        for q in QUESTIONS:
            if q['instrument']!=instrument:continue
            prior=old.get('answers',{}).get(q['id'],{})
            with st.expander(q['id']+' · '+q['section']):
                st.write(q['text']);st.caption(q['anchor'])
                if instrument==6 and 'Scale of one' in q['anchor']:
                    rating=st.selectbox('Rating',['Not answered',1,2,3,4,5],index=['Not answered',1,2,3,4,5].index(prior.get('rating','Not answered')),key=rid+q['id']+'rating')
                    st.caption('1 strongly disagree; 5 strongly agree')
                else:rating=None
                answer=st.text_area('Response / comment',prior.get('text',''),key=rid+q['id']+'text')
                evidence=st.text_input('Evidence reference(s)',prior.get('evidence',''),key=rid+q['id']+'evidence')
                answers[q['id']]={'text':answer,'evidence':evidence,'rating':rating}
        draft=st.form_submit_button('Save draft');submit=st.form_submit_button('Submit complete interview')
    if draft or submit:
        unanswered=[q for q,a in answers.items() if not a['text'].strip() and a['rating'] in (None,'Not answered')]
        if not institution.strip():st.error('Enter a municipality or agency.')
        elif submit and (not consent or unanswered):st.error('Check participation consent and address every question. Enter “Declined”, “Not known” or “Not applicable” with a reason where appropriate.')
        else:
            record={'id':rid,'status':'submitted' if submit else 'draft','instrument_version':'1.0','payload':dict(institution=institution,scheduled=scheduled,facilitator=facilitator,roles=roles,instrument=instrument,consent_checked=consent,recording_allowed=recording,answers=answers)}
            try:save_record(record);st.success('Interview saved. Submitted records can be revised by the owner in this draft app; immutable approval history is a later feature.')
            except Exception:st.error('Save failed. Your entries remain on screen; retry before leaving.')
    if old:
        st.download_button('Download interview pack (Word)',packet({'payload':old}),file_name='SALGA_interview_pack.docx')
    if st.button('Start another interview'):
        st.session_state.new_id=str(uuid4());st.session_state.pop('record_selection',None);st.rerun()

elif page=='Documents':
    st.subheader('Project document centre')
    st.caption('Documents are restricted to approved study members. Office and ODT files download in their original formats.')
    if demo:
        for p in sorted((ROOT/'documents').glob('*')):
            st.download_button(p.name,p.read_bytes(),file_name=p.name)
    else:
        bucket = client.storage.from_('salga-documents')
        if admin:
            with st.form('project_document_upload', clear_on_submit=True):
                uploads = st.file_uploader('Add project documents (maximum 10 MB each)', type=['pdf','docx','odt','pptx','xlsx','txt'], accept_multiple_files=True)
                upload_docs = st.form_submit_button('Upload project documents')
            if upload_docs:
                if not uploads:
                    st.error('Choose at least one document.')
                else:
                    for file in uploads:
                        if file.size > 10*1024*1024:
                            st.error(file.name + ': exceeds 10 MB.')
                            continue
                        safe = re.sub(r'[^A-Za-z0-9._-]', '_', file.name)
                        try:
                            bucket.upload(safe, file.getvalue(), {'content-type': file.type or 'application/octet-stream'})
                            st.success('Uploaded: ' + file.name)
                        except Exception:
                            st.error('Upload failed for ' + file.name + '. A file with the same name may already exist; use a versioned filename.')
        try:
            docs = bucket.list(options={'limit':100, 'sortBy':{'column':'name','order':'asc'}})
            files = [d for d in docs if d.get('id')]
            if not files:
                st.info('No project documents have been uploaded yet.')
            for d in files:
                name=d['name']
                if st.button('Prepare download: ' + name, key='prepare_doc_' + name):
                    data=bucket.download(name)
                    st.download_button('Download ' + name, data, file_name=name, key='download_doc_' + name)
        except Exception:
            st.error('Unable to load project documents. Check your study membership and storage access.')
    st.info('The instruments include letters, consent forms, case-study and appraisal protocols, the scoring rubric and close-out certificates. Instruments 5 and 6 are available as digital interview forms.')

elif page=='Evidence register':
    st.subheader('Restricted documentary evidence')
    st.caption('Upload redacted project evidence only. Keep consent signatures, recordings and identity keys in separately approved custody. Upload limit: 10 MB. Access: owner and project administrator.')
    with st.form('evidence'):
        reference=st.text_input('Evidence reference (e.g. EV-001)')
        description=st.text_input('Description and related question IDs')
        interview=st.selectbox('Related interview',['Unlinked']+[r['id'] for r in rows])
        file=st.file_uploader('Evidence file',type=['pdf','docx','xlsx','csv','txt','png','jpg'])
        upload=st.form_submit_button('Save evidence')
    if upload:
        if not file or not reference:st.error('Provide a reference and file.')
        elif file.size>10*1024*1024:st.error('File exceeds 10 MB.')
        else:
            eid=str(uuid4());safe=re.sub(r'[^A-Za-z0-9._-]','_',file.name)
            entry=dict(id=eid,owner_id=uid,reference=reference,description=description,interview_id=None if interview=='Unlinked' else interview,path=f'{uid}/{eid}/{safe}',filename=safe)
            if demo:
                st.session_state.setdefault('evidence',[]).append({**entry,'bytes':file.getvalue()});st.success('Evidence saved for this demonstration session.')
            else:
                bucket=client.storage.from_('salga-evidence')
                try:
                    bucket.upload(entry['path'],file.getvalue(),{'content-type':file.type or 'application/octet-stream'})
                    try:client.table('study_evidence').insert(entry).execute()
                    except Exception:
                        bucket.remove([entry['path']]);raise
                    st.success('Evidence saved.')
                except Exception:st.error('Upload failed. Retry or contact the administrator.')
    try:
        evidence=st.session_state.get('evidence',[]) if demo else client.table('study_evidence').select('*').execute().data
        for e in evidence:
            st.write(e['reference']+' · '+e['description'])
            if demo:st.download_button('Download '+e['filename'],e['bytes'],e['filename'],key=e['id'])
            elif st.button('Prepare download: '+e['filename'],key=e['id']):
                data=client.storage.from_('salga-evidence').download(e['path']);st.download_button('Download file',data,e['filename'],key='dl'+e['id'])
    except Exception:st.error('Evidence could not be loaded.')

elif page=='Coverage map':
    st.subheader('Proposed municipal sample')
    st.caption('18 proposed engagements: 5 metropolitan and 13 district municipalities. Approximate reference points illustrate sample distribution; these are not municipal boundaries, risk maps or verified office locations.')
    df=pd.read_csv(ROOT/'data/municipalities.csv')
    provinces=st.multiselect('Province',sorted(df.province.unique()))
    typologies=st.multiselect('Landscape typology',sorted(df.typology.unique()))
    if provinces:df=df[df.province.isin(provinces)]
    if typologies:df=df[df.typology.isin(typologies)]
    st.map(df,latitude='latitude',longitude='longitude')
    st.dataframe(df[['municipality','province','category','typology']],hide_index=True)
    st.download_button('Download sample register',df.to_csv(index=False),'proposed_sample.csv')
    st.info('Planned extension: verified municipal and fire protection association boundaries, fire stations, allocation of the fire function and engagement status. No diagnostic or risk layer is inferred from these points.')

else:
    st.subheader('Research exports and administration')
    st.caption('Exports below contain research responses. They require a manual anonymisation and disclosure review before any client handover.')
    if rows:
        st.download_button('Export accessible interviews (JSON)',json.dumps(rows,indent=2),'restricted_interviews.json')
        flat=[]
        for r in rows:
            for q,a in r['payload'].get('answers',{}).items():
                flat.append(dict(interview_id=r['id'],institution=r['payload']['institution'],status=r['status'],question=q,response=a['text'],rating=a.get('rating'),evidence=a['evidence']))
        st.download_button('Export accessible responses (CSV)',pd.DataFrame(flat).to_csv(index=False),'restricted_responses.csv')
    else:st.info('No saved interviews yet.')
    if admin:
        st.write('Administrator view: accessible interview counts and exports include all study records. Researchers see only their own records. Add users and assign membership through the Supabase dashboard as described in README.')
    st.write('Before fieldwork: reconcile instrument versions, secure ethics approval, confirm the municipal sample and agree data retention, withdrawal and handover procedures.')
    st.caption('Future modules: approved seven-domain rubric, concordance matrix, mechanisms analysis, case studies, options appraisal, audit history and disclosure-reviewed handover. No scoring is enabled in this draft.')
