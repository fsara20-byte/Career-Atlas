#!/usr/bin/env python3
"""Daily best-effort discovery across every target employer's official careers URL.
This is NOT equivalent to a verified ATS feed: inaccessible and JS-only sites are
reported as unverified, never as having zero vacancies.
"""
import concurrent.futures, html, json, re, hashlib, ssl
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
COMPANIES=json.loads((ROOT/'data/companies.json').read_text())
FEEDS=json.loads((ROOT/'config/sources.json').read_text())['feeds']
FEED_NAMES={x['company'] for x in FEEDS}
OUT=ROOT/'data/discovery.json'
NOW=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
UA={'User-Agent':'Mozilla/5.0 (compatible; CareerAtlas/1.0; public career page discovery)','Accept':'text/html,application/xhtml+xml'}
class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.jsonld=[];self.script=False;self.buf=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append((a['href'],a.get('title','')))
        if tag=='script' and a.get('type','').lower()=='application/ld+json':self.script=True;self.buf=[]
    def handle_data(self,data):
        if self.script:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.script:
            self.jsonld.append(''.join(self.buf));self.script=False
def fetch(url):
    with urlopen(Request(url,headers=UA),timeout=14) as r:
        if 'html' not in r.headers.get('Content-Type','').lower():raise ValueError('Not HTML')
        return r.read(800000).decode('utf-8','replace'),r.geturl()
def extract_jobs(doc):
    if isinstance(doc,list):
        for x in doc:yield from extract_jobs(x)
    elif isinstance(doc,dict):
        typ=doc.get('@type',[])
        if isinstance(typ,str):typ=[typ]
        if 'JobPosting' in typ:yield doc
        for k in ('@graph','itemListElement'):
            if k in doc:yield from extract_jobs(doc[k])
def check(c):
    name=c['name'];url=c.get('url','')
    result={'company':name,'careersUrl':url,'checkedAt':NOW,'status':'unverified','jobs':[],'detectedPlatforms':[]}
    if name in FEED_NAMES:
        result['status']='handled_by_verified_feed';return result
    try:
        page,final=fetch(url)
        parser=Links();parser.feed(page)
        signals={
          'workday':r'[\w.-]+\.myworkdayjobs\.com/[\w/-]+',
          'greenhouse':r'(?:job-boards|boards)\.greenhouse\.io/[\w-]+',
          'ashby':r'jobs\.ashbyhq\.com/[\w-]+',
          'lever':r'jobs\.lever\.co/[\w-]+',
          'smartrecruiters':r'(?:jobs|careers)\.smartrecruiters\.com/[\w-]+',
          'workable':r'apply\.workable\.com/[\w-]+',
          'recruitee':r'[\w-]+\.recruitee\.com',
          'icims':r'[\w.-]+\.icims\.com',
          'oracle':r'[\w.-]+\.fa\.oraclecloud\.com'}
        for platform,pattern in signals.items():
            found=re.findall(pattern,page,re.I)
            if found:result['detectedPlatforms'].append({'platform':platform,'example':'https://'+found[0]})
        seen=set()
        for raw in parser.jsonld:
            try:
                for job in extract_jobs(json.loads(raw)):
                    title=str(job.get('title') or '')
                    loc=job.get('jobLocation') or {}
                    if isinstance(loc,list):loc=loc[0] if loc else {}
                    address=loc.get('address',{}) if isinstance(loc,dict) else {}
                    location=' '.join(str(address.get(k) or '') for k in ('addressLocality','addressRegion','addressCountry')) if isinstance(address,dict) else ''
                    link=str(job.get('url') or job.get('sameAs') or final)
                    if not re.search(r'dubai|abu dhabi|united arab emirates|\buae\b',location,re.I):continue
                    if not re.search(r'analyst|intern|consult|strateg|finance|bank|investment|risk|credit|valuation|treasury|research|transaction|advisory|graduate',title,re.I):continue
                    if link in seen:continue
                    seen.add(link)
                    result['jobs'].append({'id':'discovery-'+hashlib.sha256((name+link).encode()).hexdigest()[:18],'company':name,'title':title,'url':link,'location':location,'description':re.sub('<[^>]+>',' ',html.unescape(str(job.get('description') or '')))[:12000],'deadline':str(job.get('validThrough') or '')[:10],'status':'needs_verification','source':'jsonld_discovery','discoveredAt':NOW})
            except (ValueError,TypeError):continue
        result['status']='structured_jobs_found' if result['jobs'] else 'page_reachable_no_verified_feed'
        result['finalUrl']=final
    except Exception as exc:
        result['status']='fetch_failed';result['error']=str(exc)[:160]
    return result
def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results=list(pool.map(check,COMPANIES))
    report={'generatedAt':NOW,'employers':len(results),'results':results,
            'note':'Discovery is not complete ATS monitoring. No results means unknown, not no vacancies. JSON-LD jobs require verification.'}
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Employer pages checked:',len(results))
    for status in sorted(set(r['status'] for r in results)):
        print(status,sum(r['status']==status for r in results))
    print('Structured candidate postings:',sum(len(r['jobs']) for r in results))
if __name__=='__main__':main()
