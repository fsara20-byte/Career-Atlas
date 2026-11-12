/* Private, browser-only CV/JD matching. No identifying profile or CV is shipped with the public site. */
(()=>{
'use strict';
const KEY='career_atlas_private_cv_v1';
let cv='';
try{cv=localStorage.getItem(KEY)||''}catch(_){}
let notify=()=>{};
let cache=new WeakMap();
const $=id=>document.getElementById(id);
const clean=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const plain=s=>String(s||'').replace(/&lt;/gi,'<').replace(/&gt;/gi,'>').replace(/<[^>]*>/g,' ').replace(/&(?:nbsp|amp|quot|#39);/gi,' ').replace(/&#(?:x[0-9a-f]+|\d+);/gi,' ').replace(/\s+/g,' ').trim();
const RULES=[
 {name:'Financial statements and accounting',w:3,cv:/financial statements?|financial analys|financial ratios?|balance sheet|income statement|common.size|liquidity analysis/i,jd:/financial statements?|financial analys|financial reports?|accounting|balance sheet|income statement|financial performance/i},
 {name:'Corporate finance and capital structure',w:3,cv:/corporate finance|capital structure|cost of (?:equity|debt|capital)|\bWACC\b|corporate lending|financing transactions/i,jd:/corporate finance|capital structure|corporate financing|funding structure|capital markets|cost of capital|debt financing/i},
 {name:'Transaction execution and origination',w:3,cv:/origina(?:ted|tion)|transaction execution|end.to.end execution|execut(?:ed|ion) of.{0,40}financing|term sheets?/i,jd:/deal execution|transaction execution|(?:mergers|acquisitions)|\bM&A\b|investment banking|transaction support|origination|transactions? (?:through|from)/i},
 {name:'Hands-on financial modelling',w:4,cv:/three.statement (?:financial )?model|(?:built|developed|created).{0,55}(?:financial model|forecast model|DCF model|integrated model)|(?:DCF|financial) model(?:l?ing)?(?: experience| proficiency| skills)/i,jd:/financial model(?:l?ing)?|build.{0,45}model|forecast(?:ing)? models?|three.statement model|integrated forecast|(?:DCF|LBO).{0,25}model|model.{0,25}(?:DCF|LBO)/i},
 {name:'M&A advisory experience',w:3,cv:/\bM&A\b|mergers and acquisitions|merger advisory|acquisition advisory|buy.side.{0,18}deal|sell.side.{0,18}deal/i,jd:/\bM&A\b|mergers.{0,8}acquisitions|M A transactions|merger advisory|buy.side mandate|sell.side mandate/i},
 {name:'Valuation methods and analysis',w:3,cv:/valuation|enterprise value|equity value|discounted cash flow|\bDCF\b|trading comparable|cost of capital|CAPM/i,jd:/valuation|enterprise value|equity valuation|\bDCF\b|comparab(?:le|ility) compan|valuation multiple/i},
 {name:'Credit and financial risk',w:3,cv:/credit(?: risk| assessment| analysis|worthiness)?|counterparty risk|interest coverage|debt.servicing|lending|solvency/i,jd:/credit|risk assessment|risk analys|counterparty|debt capacity|financial risk|liquidity risk|restructur/i},
 {name:'Investment and equity research',w:3,cv:/equity research|investment research|investment analysis|investment attractiveness|systematic risk|shareholder|capital iq/i,jd:/investment research|equity research|investment analys|securit(?:y|ies) analys|investment opportunit|capital markets/i},
 {name:'Market and sector research',w:2,cv:/market research|industry research|sector research|competitor|market.intelligence|market dynamics|competitive research/i,jd:/market research|industry research|sector research|market trends|market intelligence|competitor|competitive landscape|due diligence/i},
 {name:'Strategy and recommendations',w:2,cv:/strategic recommendations|strategy|market.entry|growth|recommendations|business analysis/i,jd:/strateg(?:y|ic)|business transformation|recommendations|market.entry|commercial due diligence|problem.solving/i},
 {name:'Client coverage and stakeholder management',w:3,cv:/client (?:coverage|relationship|contact)|stakeholder|relationship management|corporate clients|client.facing|c.suite/i,jd:/client relations|stakeholder|client facing|client service|client interaction|relationship management|client exposure|corporate clients/i},
 {name:'Presentations and communication',w:2,cv:/powerpoint|presentations?|pitch decks?|client.facing materials|structured reports|communication/i,jd:/presentation|pitch|deck|written communication|communicat|prepare materials|client deliverable/i},
 {name:'Excel and financial data tools',w:2,cv:/\bexcel\b|pivot.?tables|s&p capital iq|financial data|regression analysis/i,jd:/\bexcel\b|microsoft office|powerpoint|financial data|spreadsheet|data analysis|analytical tools/i},
 {name:'Statistics and quantitative analysis',w:2,cv:/regression|quantitative analysis|statistics|beta|CAPM|operating leverage/i,jd:/quantitative|statistic|regression|data analysis|analytical rigor|analytical skills|numerical/i},
 {name:'Arabic language',w:1,cv:/\barabic\b/i,jd:/\barabic\b/i},
 {name:'French language',w:1,cv:/\bfrench\b/i,jd:/\bfrench\b/i},
 {name:'English language',w:1,cv:/\benglish\b/i,jd:/\benglish\b/i},
 {name:'Asset management and portfolios',w:3,cv:/asset management|portfolio (?:management|analysis)|investment portfolio|investment management/i,jd:/asset management|investment management|portfolio (?:management|reporting|analysis)|institutional invest/i},
 {name:'Investment software implementation',w:3,cv:/software implement|systems implement|data migration|solutions? implementation|saas onboarding/i,jd:/solutions? implement|systems? deploy|data onboarding|data migration|platform configuration|software implement/i}
];
function restrictions(job,details){
 const t=(String(job.title||'')+' '+details).toLowerCase();
 let out=[];
 if(/emirati nationals only|emirati nationals\s+only|uae nationals only|emiratization|emiratisation/.test(t))out.push('Nationality restriction: verify directly on employer posting.');
 if(/\bmba intern\b|\bcurrently pursuing an mba\b|\bmba required\b|\bmust have an mba\b/.test(t)&&!/\bmaster of business administration\b|\bmba\b/i.test(cv))out.push('MBA-specific requirement is not evidenced in the CV.');
 const m=t.match(/\b(?:at least|minimum of|minimum)?\s*(\d{1,2})\+?\s+years?\s+(?:of\s+)?(?:relevant\s+)?(?:professional\s+)?experience\b/);
 if(m&&Number(m[1])>=5&&Number(m[1])<=15)out.push('Requires around '+m[1]+'+ years of experience; check seniority.');
 if(/visa sponsorship is not available|no visa sponsorship|must have (?:legal )?authorization to work/.test(t))out.push('Verify work authorisation / sponsorship.');
 if(/graduation date|graduating between|expected graduation|graduate between|graduation year/.test(t))out.push('Verify exact eligible graduation month/year.');
 if(/graduation date before (?:december|dec)\s+2026/.test(t)&&/expected\s+202[78]/i.test(cv))out.push('Graduation year in CV appears outside the published requirement.');
 if(/\b(?:vice president|engagement manager|senior consultant|managing director|portfolio manager|consulting director|director|consulting manager)\b|\bmanagement consulting,? manager\b/i.test(String(job.title||'')))out.push('Check seniority: role may require substantially more experience.');
 return [...new Set(out)];
}
function score(job){
 if(!cv.trim())return {state:'no_cv',score:null,matched:[],missing:[],warnings:[]};
 if(cache.has(job))return cache.get(job);
 const jd=plain(job.description);
 if(jd.length<350){const v={state:'no_jd',score:null,matched:[],missing:[],warnings:['Full job description not stored; open the employer posting.']};cache.set(job,v);return v}
 const used=RULES.filter(r=>r.jd.test(jd));
 const matched=used.filter(r=>r.cv.test(cv));
 const missing=used.filter(r=>!r.cv.test(cv));
 const warnings=restrictions(job,jd);
 let result;
 if(used.length<3)result={state:'limited_jd',score:null,matched:matched.map(r=>r.name),missing:missing.map(r=>r.name),warnings};
 else{
  const weight=used.reduce((n,r)=>n+r.w,0);
  const covered=matched.reduce((n,r)=>n+r.w,0);
  const raw=Math.round(100*covered/weight);
  const evidenceCap=used.length>=9?100:used.length>=7?94:used.length>=5?88:80;
  let final=Math.min(raw,evidenceCap);
  let state='scored';
  // Mandatory or unknown eligibility must not produce an apparently perfect match.
  if(warnings.some(w=>/Nationality restriction|MBA-specific requirement|Graduation year in CV appears outside/.test(w))){state='eligibility_check';final=null}
  // Avoid rating senior jobs as perfect matches when no equivalent role is evidenced.
  else if(warnings.some(w=>/Check seniority/.test(w))&&!/\b(?:vice president|engagement manager|senior consultant|managing director|portfolio manager|consulting director|director|consulting manager)\b|\bmanagement consulting,? manager\b/i.test(cv))final=Math.min(final,35);
  result={state,score:final,matched:matched.map(r=>r.name),missing:missing.map(r=>r.name),warnings,signalCount:used.length};
 }
 cache.set(job,result);return result;
}
function panel(job,escape=clean){
 const r=score(job);
 const label=r.state==='no_cv'?'Add CV privately':r.state==='no_jd'?'Full JD unavailable':r.state==='limited_jd'?'Limited JD evidence':r.state==='eligibility_check'?'Eligibility review required':r.score+'/100';
 const pill=r.score!==null?(r.score>=75?'good':r.score<45?'warn':''):'line';
 const text=r.state==='no_cv'
  ? '<p class="small">Paste your CV once in <a href="#cvPrivate">Private CV matching</a> to compare your evidence with this job description.</p>'
  : r.state==='no_jd'
  ? '<p class="small">No full JD is saved for this link. A reliable CV match cannot be calculated; open the employer posting.</p>'
  : '<p class="small"><b>Relevant evidence:</b> '+escape(r.matched.slice(0,5).join(' · ')||'No matching skills detected in the pasted CV.')+'</p>'
    +(r.missing.length?'<p class="small"><b>Not evidenced in CV:</b> '+escape(r.missing.slice(0,5).join(' · '))+'</p>':'')
    +(r.warnings.length?'<p class="small"><b>Eligibility checks:</b> '+escape(r.warnings.join(' · '))+'</p>':'');
 return '<div class="priorityHead"><strong>Private CV–JD match</strong><span class="pill '+pill+'">'+escape(label)+'</span></div>'+text+'<p class="tiny">Indicative keyword-based alignment, not hiring probability, guaranteed eligibility, or model proficiency. Verify the live JD.</p>';
}
function ready(){return cv.trim().length>0}
function status(){
 const status=$('privateCvStatus');if(status)status.textContent=ready()?'CV saved only in this browser. Scoring updates as jobs refresh.':'No CV saved. No personal profile is included in the public website.';
}
function save(){
 const v=$('privateCvText').value.trim();
 if(v.length<100){$('privateCvStatus').textContent='Please paste enough CV text to assess your skills (at least 100 characters).';return}
 cv=v;let persisted=true;try{localStorage.setItem(KEY,v)}catch(_){persisted=false}
 cache=new WeakMap();status();if(!persisted)$('privateCvStatus').textContent='Browser storage unavailable: matching runs for this visit only.';notify();
}
function clear(){
 cv='';cache=new WeakMap();try{localStorage.removeItem(KEY)}catch(_){}
 $('privateCvText').value='';status();notify();
}
function onChange(fn){notify=fn}
window.CareerCV={score,panel,ready,onChange};
const ta=$('privateCvText');if(ta)ta.value=cv;
$('privateCvSave')?.addEventListener('click',save);
$('privateCvClear')?.addEventListener('click',clear);
status();
})();