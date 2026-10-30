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
      'sourceBoard':company, 'status':'active', 'description':str(job.get('descriptionPlain') or '')[:12000], 'guidance':cv_guidance(title,str(job.get('descriptionPlain') or '')),
      'note':'From employer-published Ashby feed. Confirm eligibility, location and deadline on the posting.'}

def cv_guidance(title, description=''):
    text=(title+' '+description).lower()
    show=[]; work=[]
    if re.search(r'credit|bank|lending|treasury|working capital',text):
        show.append('Quantify financing transactions and credit assessment experience.')
        work.append('Review credit ratios, cash-flow analysis and financing structures.')
    if re.search(r'consult|strategy|market entry|transformation|advisory',text):
        show.append('Show client-facing projects and structured commercial problem solving.')
        work.append('Practice profitability, market sizing and market entry cases.')
    if re.search(r'investment|valuation|transaction|m&a|deal|financial model',text):
        show.append('Highlight financial analysis, valuation projects and transaction exposure.')
        work.append('Practice three-statement models, DCF and comparable valuations.')
    return {'showcase':show or ['Quantified achievements and analytical projects.'],
            'workOn':work or ['Review employer requirements and prepare relevant examples.'],
            'method':'Keyword matching, not AI assessment'}

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
      'sourceBoard':company,'status':'active', 'description':re.sub(r'<[^>]*>',' ',str(job.get('content') or ''))[:12000], 'guidance':cv_guidance(title,str(job.get('content') or '')),
      'note':'Employer-published Greenhouse posting; API updated_at is not necessarily the original posting date. Check requirements and deadline on the employer page.'}

def fetch_workday(source):
    """Public Workday CXS endpoint. Return full postings only on complete pagination."""
    from urllib.request import Request, urlopen
    host=source['host']
    tenant=source['tenant']
    site=source['site']
    base='https://'+host+'/wday/cxs/'+quote(tenant,safe='')+'/'+quote(site,safe='')
    records=[]
    offset=0
    total=None
    while total is None or offset<total:
        payload=json.dumps({'appliedFacets':{},'limit':20,'offset':offset,'searchText':''}).encode('utf-8')
        req=Request(base+'/jobs',data=payload,headers={'User-Agent':'Mozilla/5.0 CareerAtlas/1.0','Accept':'application/json','Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=30) as res:
            doc=json.load(res)
        batch=doc.get('jobPostings')
        if not isinstance(batch,list): raise ValueError('Workday returned no jobPostings array')
        if total is None: total=int(doc.get('total',len(batch)))
        if total>1200: raise ValueError('Workday board exceeds 1200-posting full-scan limit; not claiming complete coverage')
        if not batch and offset<total: raise ValueError('Workday pagination incomplete')
        records.extend(batch)
        offset+=len(batch)
        if not batch: break
    return records,base

def workday_details(base,external):
    """Fetch description for a shortlisted job, without blocking listing discovery."""
    if not external.startswith('/'):return {}
    try:
        req=Request(base+external,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
        with urlopen(req,timeout=12) as res:doc=json.load(res)
        return doc.get('jobPostingInfo') or {}
    except Exception:return {}

def fetch_smartrecruiters(board):
    """Read all public company postings; refuse incomplete boards."""
    results=[];offset=0;total=None
    while total is None or offset<total:
        doc=fetch_json('https://api.smartrecruiters.com/v1/companies/'+quote(board,safe='')+'/postings?limit=100&offset='+str(offset))
        batch=doc.get('content')
        if not isinstance(batch,list):raise ValueError('SmartRecruiters response missing content array')
        if total is None:total=int(doc.get('totalFound',len(batch)))
        if total>1200:raise ValueError('SmartRecruiters board exceeds full-scan limit')
        if not batch and offset<total:raise ValueError('SmartRecruiters pagination incomplete')
        results.extend(batch);offset+=len(batch)
        if not batch:break
    return results

def smartrecruiters_normalize(raw,company,board):
    title=str(raw.get('name') or '').strip()
    ident=str(raw.get('id') or '')
    if not title or not ident:return None
    loc=raw.get('location') or {}
    location=', '.join(str(loc.get(k) or '') for k in ('city','region','country') if loc.get(k))
    url='https://jobs.smartrecruiters.com/'+quote(board,safe='')+'/'+quote(ident,safe='')
    return {'id':'smartrecruiters-'+hashlib.sha256((company+ident).encode()).hexdigest()[:18],
            'company':company,'title':title,'url':url,'location':location,
            'programme':programme_from_title(title),'eligibilityFlags':flags_from_title(title),
            'deadline':'','publishedAt':str(raw.get('releasedDate') or '')[:10],
            'source':'smartrecruiters','sourceBoard':company,'status':'active',
            'guidance':cv_guidance(title),
            'note':'Public SmartRecruiters employer posting; confirm eligibility and deadline.'}

def smartrecruiters_details(board,ident):
    try:
        doc=fetch_json('https://api.smartrecruiters.com/v1/companies/'+quote(board,safe='')+'/postings/'+quote(str(ident),safe=''))
        sections=(doc.get('jobAd') or {}).get('sections') or {}
        description=' '.join(str(v.get('text') if isinstance(v,dict) else v or '') for v in sections.values())
        return {'description':re.sub(r'<[^>]*>',' ',description)[:12000],
                'url':doc.get('postingUrl') or doc.get('applyUrl') or ''}
    except Exception:return {}

def workday_normalize(raw,company,base):
    title=str(raw.get('title') or '').strip()
    location=str(raw.get('locationsText') or '')
    external=str(raw.get('externalPath') or '')
    if not title or not external.startswith('/'): return None
    url=base.rsplit('/wday/cxs/',1)[0]+'/en-US/'+quote(base.rsplit('/',1)[-1],safe='')+external
    return {'id':'workday-'+hashlib.sha256((company+external).encode()).hexdigest()[:18],
            'company':company,'title':title,'url':url,'location':location,
            'programme':programme_from_title(title),'eligibilityFlags':flags_from_title(title),
            'deadline':'','publishedAt':'','source':'workday','sourceBoard':company,
            'status':'active','guidance':cv_guidance(title),
            'note':'Employer Workday listing; confirm location, eligibility and deadline on the official posting.'}

def update(path=DATA, config_path=SOURCES, fetcher=fetch_json):
    cfg = json.loads(config_path.read_text())
    doc = json.loads(path.read_text())
    existing = {x['id']:x for x in doc.get('jobs',[]) if x.get('id')}
    outcomes=[]; num_added=0; num_changed=0; changed_ids=[]
    for source in cfg['feeds']:
        board, company = source['board'], source['company']
        provider=source['provider']
        if provider=='smartrecruiters':
            try:
                records=fetch_smartrecruiters(board)
                available=set();count=0
                for raw in records:
                    loc=raw.get('location') or {}
                    location=', '.join(str(loc.get(k) or '') for k in ('city','region','country') if loc.get(k))
                    if not relevant({'title':raw.get('name',''),'location':location},cfg):continue
                    item=smartrecruiters_normalize(raw,company,board)
                    if not item:continue
                    count+=1;old=existing.get(item['id'],{})
                    detail=smartrecruiters_details(board,raw.get('id'))
                    if detail.get('url','').startswith('https://'):item['url']=detail['url']
                    item['description']=detail.get('description') or old.get('description','')
                    item['guidance']=cv_guidance(item['title'],item['description'])
                    item['firstSeen']=old.get('firstSeen',TODAY)
                    item['firstSeenAt']=old.get('firstSeenAt',NOW)
                    item['lastSeen']=TODAY;item['lastSeenAt']=NOW
                    item['deadline']=old.get('deadline','')
                    item['deadlineSource']=old.get('deadlineSource','')
                    if not old:num_added+=1
                    existing[item['id']]=item;available.add(item['id'])
                for key,old in existing.items():
                    if old.get('source')=='smartrecruiters' and old.get('sourceBoard')==company and key not in available:
                        old['status']='not_in_latest_feed'
                outcomes.append({'company':company,'status':'ok','count':count,'checkedAt':NOW,'provider':provider,'totalBoardPostings':len(records)})
            except Exception as exc:
                outcomes.append({'company':company,'status':'failed','count':None,'checkedAt':NOW,'provider':provider,'error':str(exc)[:160]})
            continue
        if provider=='workday':
            try:
                records,base=fetch_workday(source)
                available=set();count=0
                for raw in records:
                    normalized={'title':raw.get('title',''),'location':raw.get('locationsText','')}
                    if not relevant(normalized,cfg):continue
                    item=workday_normalize(raw,company,base)
                    if not item:continue
                    count+=1
                    old=existing.get(item['id'],{})
                    item['firstSeen']=old.get('firstSeen',TODAY)
                    item['firstSeenAt']=old.get('firstSeenAt',NOW)
                    item['lastSeen']=TODAY
                    item['lastSeenAt']=NOW
                    detail=workday_details(base,str(raw.get('externalPath') or ''))
                    item['description']=re.sub(r'<[^>]*>',' ',str(detail.get('jobDescription') or ''))[:12000] or old.get('description','')
                    item['guidance']=cv_guidance(item['title'],item['description'])
                    item['deadline']=old.get('deadline','')
                    item['deadlineSource']=old.get('deadlineSource','')
                    if old.get('guidance'):item['guidance']=old['guidance']
                    if not old:num_added+=1
                    existing[item['id']]=item
                    available.add(item['id'])
                for key,old in existing.items():
                    if old.get('source')=='workday' and old.get('sourceBoard')==company and key not in available:
                        old['status']='not_in_latest_feed'
                outcomes.append({'company':company,'status':'ok','count':count,'checkedAt':NOW,'provider':'workday','totalBoardPostings':len(records)})
            except Exception as exc:
                outcomes.append({'company':company,'status':'failed','count':None,'checkedAt':NOW,'provider':'workday','error':str(exc)[:160]})
            continue
        if provider not in ('ashby','greenhouse'):
            outcomes.append({'company':company, 'status':'unsupported', 'count':0})
            continue
        url = ('https://api.ashbyhq.com/posting-api/job-board/'+quote(board,safe='')+'?includeCompensation=false'
               if provider=='ashby' else
               'https://boards-api.greenhouse.io/v1/boards/'+quote(board,safe='')+'/jobs?content=true')
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
                if not item.get('description') and old.get('description'):
                    item['description']=old['description']; item['guidance']=old.get('guidance',cv_guidance(item['title'],old['description']))
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
          'note':'Configured official Ashby, Greenhouse and Workday public feeds sync automatically. Other employer portals need separate monitoring; missing deadlines remain blank.',
          'sourceCoverage':'Automated: '+', '.join(x['company'] for x in outcomes if x['status']=='ok')+'. Other employers: official career portals.'}
    doc={'meta':meta,'jobs':sorted(existing.values(),key=lambda x:(x.get('status')!='active', str(x.get('company','')),str(x.get('title',''))))}
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(f'Checked {len(outcomes)} sources; {sum(x["status"]=="ok" for x in outcomes)} succeeded; {num_added} newly discovered roles; {num_changed} deadline changes')
    for row in outcomes: print(f'  {row["company"]}: {row["status"]} ({row.get("count")})')
    # No failed scrape should break publishing, as long as the existing JSON stays usable.
    return doc

if __name__=='__main__': update()
