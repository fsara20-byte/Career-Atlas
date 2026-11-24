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


class InvestmentSalesCoverageTests(unittest.TestCase):
    def test_excludes_explicit_nationality_only_and_past_intakes(self):
        cfg={'location_keywords':['dubai'], 'include_title_regex':r'(?i)(analyst|internship|graduate)'}
        self.assertFalse(update_jobs.relevant({'title':'Credit Analyst (UAE Nationals Only)','location':'Dubai'},cfg))
        self.assertFalse(update_jobs.relevant({'title':'2025 Wealth Internship','location':'Dubai'},cfg))
        self.assertTrue(update_jobs.relevant({'title':'Corporate Banking Summer Intern Analyst (UAE Nationals Preferred)','location':'Dubai'},cfg))
        self.assertIn('preferred',update_jobs.flags_from_title('Investment Analyst (UAE Nationals Preferred)')[0].lower())

    def test_market_sales_and_asset_management_internships_are_not_filtered_out(self):
        cfg = {
            'location_keywords':['dubai','abu dhabi','united arab emirates','uae'],
            'exclude_title_regex':r'(?i)(sales|business development|account executive|marketing|client service|customer success)',
            'exclude_senior_title_regex':r'(?i)\b(managing director|executive director|head of)\b',
            'include_title_regex':r'(?i)\b(internship|intern|analyst|graduate|investment|capital markets)\b',
            'include_finance_sales_title_regex':r'(?i)(?:sales\s*[,/&-]?\s*trading|(?:institutional|investment|asset management|fund|MEA)\s+sales|sales.{0,40}(?:intern|analyst))',
        }
        self.assertTrue(update_jobs.relevant({'title':'Sales, Trading and Structuring Off Cycle Internship Programme 2027 Dubai','location':'Dubai'},cfg))
        self.assertTrue(update_jobs.relevant({'title':'MEA Sales Internship Programme 2027 - Dubai','location':'Dubai'},cfg))
        self.assertTrue(update_jobs.relevant({'title':'Institutional Sales Analyst','location':'Abu Dhabi'},cfg))
        self.assertFalse(update_jobs.relevant({'title':'Business Development Manager','location':'Dubai'},cfg))
        self.assertFalse(update_jobs.relevant({'title':'Sales Executive','location':'Dubai'},cfg))
        self.assertFalse(update_jobs.relevant({'title':'Sales, Trading and Structuring Internship','location':'London'},cfg))


class WorkdayFallbackTests(unittest.TestCase):
    SOURCE={'company':'Citi','provider':'workday','host':'example.myworkdayjobs.com',
            'tenant':'example','site':'External','board':'External'}

    def test_scoped_query_deduplicates_and_explicitly_marks_partial(self):
        calls=[]
        def fetch(term,offset):
            calls.append((term,offset))
            if not term:return {'total':2500,'jobPostings':[{'externalPath':'/global'}]}
            if term=='Dubai':return {'total':1,'jobPostings':[{'title':'Credit Analyst','externalPath':'/job/dubai','locationsText':'Dubai'}]}
            if term=='United Arab Emirates':return {'total':1,'jobPostings':[{'title':'Credit Analyst','externalPath':'/job/dubai','locationsText':'Dubai'}]}
            return {'total':0,'jobPostings':[]}
        jobs,base,mode=update_jobs.fetch_workday(self.SOURCE,page_fetcher=fetch)
        self.assertEqual(mode,'partial')
        self.assertEqual([x['externalPath'] for x in jobs],['/job/dubai'])
        self.assertIn(('UAE',0),calls)

    def test_full_board_keeps_complete_coverage(self):
        def fetch(term,offset):
            self.assertEqual(term,'')
            return {'total':1,'jobPostings':[{'externalPath':'/single'}]}
        jobs,_,mode=update_jobs.fetch_workday(self.SOURCE,page_fetcher=fetch)
        self.assertEqual(mode,'complete')
        self.assertEqual(len(jobs),1)

    def test_failure_in_one_fallback_query_is_not_misreported_as_success(self):
        def fetch(term,offset):
            if not term:return {'total':2500,'jobPostings':[]}
            if term=='Abu Dhabi':raise OSError('network unavailable')
            return {'total':0,'jobPostings':[]}
        with self.assertRaisesRegex(ValueError,'fallback incomplete'):
            update_jobs.fetch_workday(self.SOURCE,page_fetcher=fetch)

