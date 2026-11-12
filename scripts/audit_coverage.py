#!/usr/bin/env python3
"""Truthful employer-by-employer vacancy monitoring coverage audit."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
companies=json.loads((ROOT/'data/companies.json').read_text())
config=json.loads((ROOT/'config/sources.json').read_text())
jobs=json.loads((ROOT/'data/jobs.json').read_text())
feeds={f['company']:f for f in config['feeds']}
health={s['company']:s for s in jobs.get('meta',{}).get('sources',[])}
secondary=config.get('additional_unmonitored_boards',{})
rows=[]
for company in companies:
    name=company['name'];feed=feeds.get(name);scan=health.get(name,{})
    status=('not_configured' if not feed else
            'verified_feed' if scan.get('status')=='ok' else
            'failed' if scan.get('status')=='failed' else 'awaiting_first_scan')
    if status=='verified_feed' and secondary.get(name):status='partial_feed'
    rows.append({'company':name,'careersUrl':company.get('url',''),
                 'provider':feed.get('provider') if feed else None,
                 'monitoringStatus':status,
                 'lastCheckedAt':scan.get('checkedAt'),
                 'matchingJobs':scan.get('count'),
                 'error':scan.get('error',''),
                 'otherUnmonitoredBoards':secondary.get(name,[])})
result={'generatedAt':datetime.now(timezone.utc).isoformat(),
        'employers':len(rows),
        'verifiedFeeds':sum(x['monitoringStatus']=='verified_feed' for x in rows),
        'notConfigured':sum(x['monitoringStatus']=='not_configured' for x in rows),
        'rows':rows,
        'note':'Verified feed coverage only applies to the configured platform. A partial_feed employer has additional unmonitored official boards, so zero results does not mean zero vacancies.'}
(ROOT/'data/monitoring-coverage.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(f"Coverage: {result['verifiedFeeds']}/{result['employers']} verified feeds; {result['notConfigured']} unconfigured")
