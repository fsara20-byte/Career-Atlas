import tempfile, unittest, json, pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import update_jobs

class UpdateJobTests(unittest.TestCase):
    def test_retrieves_only_relevant_jobs_and_keeps_seed(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            jobs=root/'jobs.json'; cfg=root/'cfg.json'
            jobs.write_text(json.dumps({'meta':{},'jobs':[{'id':'seed-a','source':'curated','url':'https://example.com','title':'Example'}]}))
            cfg.write_text(json.dumps({'feeds':[{'company':'Example','provider':'ashby','board':'example'},{'company':'Broken','provider':'ashby','board':'broken'}],
             'location_keywords':['dubai','uae','abu dhabi'], 'include_title_regex':r'(?i)\b(analyst|finance|strategy)\b'}))
            def fetch(url):
                if 'broken' in url: raise OSError('network down')
                return {'jobs':[
                  {'title':'Finance Analyst','location':'Dubai','jobUrl':'https://jobs.ashbyhq.com/example/123','isListed':True,'publishedAt':'2026-10-29T10:00:00Z'},
                  {'title':'Marketing Manager','location':'Dubai','jobUrl':'https://jobs.ashbyhq.com/example/333','isListed':True},
                  {'title':'Strategy Analyst','location':'Paris','jobUrl':'https://jobs.ashbyhq.com/example/456','isListed':True},
                  {'title':'Finance Analyst','location':'Dubai','jobUrl':'https://jobs.ashbyhq.com/example/secret','isListed':False}
                ]}
            new=update_jobs.update(jobs,cfg,fetch)
            self.assertEqual(len(new['jobs']),2)
            self.assertEqual(new['meta']['newRolesLastRun'],1)
            self.assertEqual(new['meta']['sources'][1]['status'],'failed')
            next_run=update_jobs.update(jobs,cfg,fetch)
            self.assertEqual(next_run['meta']['newRolesLastRun'],0)
            self.assertEqual(len(next_run['jobs']),2)
    def test_job_removed_from_successful_feed_is_not_declared_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);a=root/'j.json';b=root/'c.json'
            a.write_text(json.dumps({'meta':{},'jobs':[]}))
            b.write_text(json.dumps({'feeds':[{'company':'X','provider':'ashby','board':'x'}], 'location_keywords':['dubai'],'include_title_regex':r'(?i)finance'}))
            update_jobs.update(a,b,lambda _: {'jobs':[{'title':'Finance Analyst','location':'Dubai','jobUrl':'https://jobs.ashbyhq.com/x/123'}]})
            result=update_jobs.update(a,b,lambda _: {'jobs':[]})
            self.assertEqual(result['jobs'][0]['status'],'not_in_latest_feed')
if __name__=='__main__':unittest.main()

class GreenhouseTests(unittest.TestCase):
    def test_greenhouse_filters_uae_relevant_and_retains_seed(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); a=root/'j.json';b=root/'c.json'
            seed={'id':'seed-sch','company':'Schonfeld','title':'Internship','source':'curated','url':'https://job-boards.greenhouse.io/schonfeld/jobs/123','deadline':''}
            a.write_text(json.dumps({'meta':{},'jobs':[seed]}))
            b.write_text(json.dumps({'feeds':[{'company':'Schonfeld','provider':'greenhouse','board':'schonfeld'}], 'location_keywords':['dubai'],'include_title_regex':r'(?i)\b(intern|analyst)\b'}))
            result=update_jobs.update(a,b,lambda u:{'jobs':[
                {'id':123,'title':'Investment Analyst Intern','location':{'name':'Dubai, UAE'},'absolute_url':'https://job-boards.greenhouse.io/schonfeld/jobs/123','updated_at':'2026-10-29'},
                {'id':124,'title':'Software Engineer','location':{'name':'Dubai'},'absolute_url':'https://job-boards.greenhouse.io/schonfeld/jobs/124'},
                {'id':125,'title':'Investment Analyst','location':{'name':'London'},'absolute_url':'https://job-boards.greenhouse.io/schonfeld/jobs/125'},
            ]})
            self.assertEqual(len(result['jobs']),1)
            self.assertEqual(result['jobs'][0]['id'],'seed-sch')
            self.assertEqual(result['jobs'][0]['source'],'greenhouse')
            self.assertEqual(result['jobs'][0]['publishedAt'],'')
            self.assertEqual(result['meta']['newRolesLastRun'],0)

class LegacyRecordTests(unittest.TestCase):
    def test_malformed_company_field_does_not_crash_sort(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);a=root/'j.json';b=root/'c.json'
            a.write_text(json.dumps({'meta':{},'jobs':[{'id':'legacy','company':{'name':'Legacy Company'},'title':'Legacy Role','source':'curated'}]}))
            b.write_text(json.dumps({'feeds':[],'location_keywords':['dubai'],'include_title_regex':r'(?i)finance'}))
            result=update_jobs.update(a,b,lambda u: {'jobs': []})
            self.assertEqual(len(result['jobs']),1)
