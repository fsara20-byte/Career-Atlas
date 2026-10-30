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
rows=[]
for company in companies:
    name=company['name'];feed=feeds.get(name);scan=health.get(name,{})
    status=('not_configured' if not feed else
            'verified_feed' if scan.get('status')=='ok' else
            'failed' if scan.get('status')=='failed' else 'awaiting_first_scan')
    rows.append({'company':name,'careersUrl':company.get('url',''),
                 'provider':feed.get('provider') if feed else None,
                 'monitoringStatus':status,
                 'lastCheckedAt':scan.get('checkedAt'),
                 'matchingJobs':scan.get('count'),
                 'error':scan.get('error','')})
result={'generatedAt':datetime.now(timezone.utc).isoformat(),
        'employers':len(rows),
        'verifiedFeeds':sum(x['monitoringStatus']=='verified_feed' for x in rows),
        'notConfigured':sum(x['monitoringStatus']=='not_configured' for x in rows),
        'rows':rows,
        'note':'Only verified_feed indicates successful vacancy retrieval. Listed careers URLs are not automatic job monitoring.'}
(ROOT/'data/monitoring-coverage.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(f"Coverage: {result['verifiedFeeds']}/{result['employers']} verified feeds; {result['notConfigured']} unconfigured")
