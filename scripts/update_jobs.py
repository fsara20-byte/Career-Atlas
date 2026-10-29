#!/usr/bin/env python3
"""Refresh supported employer-published Ashby and Greenhouse feeds into data/jobs.json.

No credentials. Never guesses deadlines or declares jobs closed just because a site failed.
Run: python scripts/update_jobs.py
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/jobs.json'
SOURCES = ROOT / 'config/sources.json'
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
TODAY = NOW[:10]

def fetch_json(url: str):
    req = Request(url, headers={'User-Agent':'CareerWatchJobMonitor/1.0 (+github-pages; public official posting API)', 'Accept':'application/json'})
    with urlopen(req, timeout=25) as res:
        return json.load(res)

def relevant(job, cfg):
    place = ' '.join([str(job.get('location') or '')] + [str(x.get('location') or '') for x in job.get('secondaryLocations') or []])
    postal = (job.get('address') or {}).get('postalAddress') or {}
    place += ' ' + ' '.join(str(postal.get(k) or '') for k in ('addressLocality','addressRegion','addressCountry'))
    if not any(k.lower() in place.lower() for k in cfg['location_keywords']):
        return False
    title = str(job.get('title') or '')
    if re.search(cfg.get('exclude_title_regex', r'(?!)'),title):
        return False
    if re.search(cfg.get('exclude_senior_title_regex', r'(?!)'),title):
        return False
    text = title+' '+str(job.get('department') or '')
    return bool(re.search(cfg['include_title_regex'], text))

def flags_from_title(title, location='', description=''):
    """Conservative flags: signals to verify, never definitive eligibility claims."""
    t=title.lower()
    flags=[]
    if re.search(r'\b(mba|master of business administration)\b', t):flags.append('MBA programme – check eligibility')
    if re.search(r'\b(summer|spring|off.cycle|intern|graduate|campus)\b', t):flags.append('Student or graduation rules – check eligibility')
    if re.search(r'\b(director|principal|vp|vice president|senior|lead)\b', t):flags.append('Senior role – check years required')
    if re.search(r'\b(quant|quantitative|trader|systematic)\b', t):flags.append('Quantitative skills may be required')
    if re.search(r'\b(uae national|emirati|emiratization|emiratisation)\b', t):flags.append('UAE nationality restriction – check eligibility')
    return flags

def programme_from_title(title, label=''):
    t=(title+' '+label).lower()
    if 'summer' in t and ('intern' in t or 'analyst' in t):return 'Summer internship'
    if 'spring' in t and ('intern' in t or 'analyst' in t):return 'Spring internship'
    if 'off-cycle' in t or 'off cycle' in t:return 'Off-cycle internship'
    if 'intern' in t:return 'Internship'
    if 'graduate' in t or 'campus' in t:return 'Graduate / full-time'
    return 'Full-time / other'

def normalize(job, company):
    url = job.get('jobUrl') or job.get('applyUrl') or ''
    if not url.startswith('https://jobs.ashbyhq.com/'):
        return None
    label = job.get('employmentType') or 'Role'
    title = str(job.get('title') or '').strip()
    if not title: return None
    loc = job.get('location') or ''
    secondary = [x.get('location','') for x in job.get('secondaryLocations') or []]
    location = ', '.join(x for x in [loc] + secondary if x)
    published = str(job.get('publishedAt') or '')[:10]
    return {'id':'ashby-'+hashlib.sha256(url.split('?')[0].encode('utf8')).hexdigest()[:18],
      'company':company, 'title':title, 'url':url, 'location':location,
      'programme': programme_from_title(title,label), 'eligibilityFlags':flags_from_title(title),
      'deadline':'', 'publishedAt':published, 'source':'ashby',
      'sourceBoard':company, 'status':'active', 'note':'From employer-published Ashby feed. Confirm eligibility, location and deadline on the posting.'}

def greenhouse_normalize(job, company):
    """Normalize Greenhouse's public Job Board API; never infer a closing date."""
    url = str(job.get('absolute_url') or '')
    if not url.startswith('https://'): return None
    title = str(job.get('title') or '').strip()
    if not title: return None
    loc = job.get('location') or {}
    location = loc.get('name','') if isinstance(loc,dict) else str(loc)
    updated = str(job.get('updated_at') or '')[:10]
    return {'id':'greenhouse-'+hashlib.sha256(url.split('?')[0].encode('utf8')).hexdigest()[:18],
      'company':company,'title':title,'url':url,'location':location,
      'programme':programme_from_title(title), 'eligibilityFlags':flags_from_title(title),
      'deadline':'','publishedAt':'','updatedAt':updated,'source':'greenhouse',
      'sourceBoard':company,'status':'active',
      'note':'Employer-published Greenhouse posting; API updated_at is not necessarily the original posting date. Check requirements and deadline on the employer page.'}

def update(path=DATA, config_path=SOURCES, fetcher=fetch_json):
    cfg = json.loads(config_path.read_text())
    doc = json.loads(path.read_text())
    existing = {x['id']:x for x in doc.get('jobs',[]) if x.get('id')}
    outcomes=[]; num_added=0; num_changed=0; changed_ids=[]
    for source in cfg['feeds']:
        board, company = source['board'], source['company']
        provider=source['provider']
        if provider not in ('ashby','greenhouse'):
            outcomes.append({'company':company, 'status':'unsupported', 'count':0})
            continue
        url = ('https://api.ashbyhq.com/posting-api/job-board/'+quote(board,safe='')+'?includeCompensation=false'
               if provider=='ashby' else
               'https://boards-api.greenhouse.io/v1/boards/'+quote(board,safe='')+'/jobs')
        try:
            data=fetcher(url)
            if not isinstance(data.get('jobs'),list):
                raise ValueError('Employer public job API returned no jobs array')
            available=set(); count=0
            for raw in data['jobs']:
                if provider=='ashby':
                    if raw.get('isListed') is False or not relevant(raw,cfg): continue
                    item=normalize(raw,company)
                else:
                    location=raw.get('location') or {}
                    location=location.get('name','') if isinstance(location,dict) else str(location)
                    raw_normal={'location':location,'title':raw.get('title','')}
                    if not relevant(raw_normal,cfg):continue
                    item=greenhouse_normalize(raw,company)
                if not item: continue
                count+=1
                # Match previously-curated direct posting so application notes don't fork.
                canonical=item['url'].split('?')[0].rstrip('/')
                same_seed=next((j for j in existing.values() if j.get('company')==company
                                and j.get('url','').split('?')[0].rstrip('/')==canonical),None)
                if same_seed: item['id']=same_seed['id']
                available.add(item['id'])
                old=existing.get(item['id'],{})
                item['firstSeen']=old.get('firstSeen',TODAY)
                item['firstSeenAt']=old.get('firstSeenAt',NOW)
                item['lastSeen']=TODAY
                item['lastSeenAt']=NOW
                # Most public APIs do not publish deadlines. Never infer a closing date.
                # If a feed provides a structured ISO deadline, use it and audit changes.
                raw_deadline = raw.get('applicationDeadline') or raw.get('validThrough') or ''
                parsed_deadline = str(raw_deadline)[:10] if re.match(r'^\d{4}-\d{2}-\d{2}',str(raw_deadline)) else ''
                new_deadline=parsed_deadline or old.get('deadline','')
                if old and parsed_deadline and parsed_deadline != old.get('deadline',''):
                    item['previousDeadline']=old.get('deadline','')
                    item['deadlineChangedAt']=NOW
                    num_changed+=1;changed_ids.append(item['id'])
                else:
                    item['previousDeadline']=old.get('previousDeadline','')
                    item['deadlineChangedAt']=old.get('deadlineChangedAt','')
                item['deadline']=new_deadline
                item['deadlineSource']='employer feed' if parsed_deadline else old.get('deadlineSource','')
                item['deadlineVerifiedAt']=TODAY if parsed_deadline else old.get('deadlineVerifiedAt','')
                if old and old.get('status') == 'not_in_latest_feed':item['relistedAt']=NOW
                else:item['relistedAt']=old.get('relistedAt','')
                if not old:num_added+=1
                existing[item['id']]=item
            for key, old in existing.items():
                if old.get('source')==provider and old.get('sourceBoard')==company and key not in available:
                    old['status']='not_in_latest_feed'
            outcomes.append({'company':company,'status':'ok','count':count,'checkedAt':NOW,'provider':provider})
        except Exception as exc:
            outcomes.append({'company':company,'status':'failed','count':None,'checkedAt':NOW,'provider':provider,'error':str(exc)[:160]})
    good=any(x['status']=='ok' for x in outcomes)
    previous=doc.get('meta') or {}
    meta={'generatedAt':NOW,'lastAttemptAt':NOW,
          'lastSuccessfulAt':NOW if good else previous.get('lastSuccessfulAt'),
          'newRolesLastRun':num_added,'deadlineChangesLastRun':num_changed,'deadlineChangedIds':changed_ids,'sources':outcomes,
          'note':'Only configured official Ashby/Greenhouse public feeds sync automatically. Other employer portals need separate monitoring; missing deadlines remain blank.',
          'sourceCoverage':'Automated: '+', '.join(x['company'] for x in outcomes if x['status']=='ok')+'. Other employers: official career portals.'}
    doc={'meta':meta,'jobs':sorted(existing.values(),key=lambda x:(x.get('status')!='active', str(x.get('company','')),str(x.get('title',''))))}
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(f'Checked {len(outcomes)} sources; {sum(x["status"]=="ok" for x in outcomes)} succeeded; {num_added} newly discovered roles; {num_changed} deadline changes')
    for row in outcomes: print(f'  {row["company"]}: {row["status"]} ({row.get("count")})')
    # No failed scrape should break publishing, as long as the existing JSON stays usable.
    return doc

if __name__=='__main__': update()
