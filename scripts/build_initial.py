from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[1]
s=Path('/mnt/data/Career_Watch_Dubai_2027_Roles_By_Company.html').read_text()
companies=json.loads(re.search(r'const companies=(\[.*?\]);\s*const roles=',s,re.S).group(1))
roles=json.loads(re.search(r'const roles=(\[.*?\]);\s*const K=',s,re.S).group(1))
add=[('Ziina','Fintech / finance','Dubai / UAE','https://jobs.ashbyhq.com/ziina','Medium'),('Taptap Send','Fintech / finance','Dubai / UAE','https://jobs.ashbyhq.com/TaptapSend','Medium'),('Pave Bank','Fintech / finance','Dubai / UAE','https://jobs.ashbyhq.com/PaveBank','Medium'),('Alcazar Energy','Investment / infrastructure','Dubai / UAE','https://jobs.ashbyhq.com/alcazar-energy','Medium')]
for name,cat,geo,url,priority in add:
 if not any(x['name'].lower()==name.lower() for x in companies):
  companies.append({'name':name,'category':cat,'geo':geo,'url':url,'priority':priority,'fit':'Finance / investment'})
(root/'data/companies.json').write_text(json.dumps(companies,ensure_ascii=False,indent=2)+'\n')
# Seed jobs = dated/static only; use status 'link_to_check', never assert vacancies are currently open.
items=[]
for i,r in enumerate(roles):
 items.append({'id':'seed-'+hashlib.sha256(r['url'].encode()).hexdigest()[:14], 'legacyIndex':i,'company':r['company'], 'title':r['title'], 'url':r['url'], 'location':'Dubai, UAE' if 'Dubai' in r['title'] else 'Check programme locations', 'programme':r['type'],'deadline':r.get('deadline',''), 'publishedAt':'2026-10-23' if r['company']=='Citi' else '', 'firstSeen':'2026-10-29','lastSeen':'2026-10-29','source':'curated','status':'verify_on_employer_site','note':r['note']})
seed={'meta':{'generatedAt':'2026-10-29T00:00:00Z','lastAttemptAt':None,'lastSuccessfulAt':None,'note':'Seed list only. Live feed checks require GitHub Actions to be enabled.','sources':[],'sourceCoverage':'Automatic feeds: Ziina, Taptap Send, Pave Bank, Alcazar Energy (Ashby). Other employers: official application links and ChatGPT monitoring.'},'jobs':items}
(root/'data/jobs.json').write_text(json.dumps(seed,ensure_ascii=False,indent=2)+'\n')
(root/'config/sources.json').write_text(json.dumps({'feeds':[{'company':'Ziina','provider':'ashby','board':'ziina'},{'company':'Taptap Send','provider':'ashby','board':'TaptapSend'},{'company':'Pave Bank','provider':'ashby','board':'PaveBank'},{'company':'Alcazar Energy','provider':'ashby','board':'alcazar-energy'}],'location_keywords':['dubai','abu dhabi','united arab emirates','uae'],'include_title_regex':r'(?i)\b(analyst|associate|investment|finance|financial|strategy|strategic|corporate development|credit|structured|banking|research|treasury|risk|consultant|consulting|portfolio|transaction|private equity|private debt|asset management|capital markets|fundraising|deal|economics?|fp&a|intern|graduate)\b'},indent=2)+'\n')
print(len(companies),len(items))
