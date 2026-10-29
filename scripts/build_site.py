"""Embed initial company and job snapshots into a self-contained HTML fallback.
The live hosted website fetches data/jobs.json separately, so this is not needed daily.
"""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
txt=(root/'index.template.html').read_text()
company=json.loads((root/'data/companies.json').read_text())
doc=json.loads((root/'data/jobs.json').read_text())
for k,v in {'__APP_JS__':(root/'scripts/app.js').read_text(),'__COMPANIES__':json.dumps(company,ensure_ascii=False),'__JOBS__':json.dumps(doc['jobs'],ensure_ascii=False),'__META__':json.dumps(doc['meta'],ensure_ascii=False)}.items():txt=txt.replace(k,v)
(root/'index.html').write_text(txt)
print('Built index.html with inline offline fallback')
