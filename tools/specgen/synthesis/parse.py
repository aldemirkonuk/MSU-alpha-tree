import re, yaml, json, collections
R='/Users/aldemirkonuk/Projects/MSU-Alpha-3/'
S='/private/tmp/claude-501/-Users-aldemirkonuk-Projects-MSU-Alpha-3/db1dcec6-4be3-4cc7-9218-9378ebfe1b46/scratchpad/'
def rd(p): return open(p,encoding='utf-8').read()
# live ids
live={}
order=[]
for l in rd(S+'live_doc2/requirement_ids.md').splitlines():
    m=re.match(r'^(R-[A-Z]{2}-\d+) \[(.*?)\]: (.*)$',l)
    if m: live[m[1]]={'tier':m[2],'text':m[3]}; order.append(m[1])
at={t['id']:t for t in yaml.safe_load(open(R+'docs/requirements_review/acceptance_tests.yaml'))['tests']}
def cells(row):
    row=row.strip()
    assert row.startswith('|')
    parts=[c.strip() for c in row[1:-1].split('|')]
    return parts
# QR
qr={}; qr_nochange=set()
txt=rd(R+'docs/requirements_review/quality_review.md')
sec4=txt[txt.index('## 4. Per-family'):]
for l in sec4.splitlines():
    if l.startswith('No change needed:'):
        for i in re.findall(r'R-[A-Z]{2}-\d+',l): qr_nochange.add(i)
    if l.startswith('| R-'):
        c=cells(l)
        if len(c)!=6: print('QRBAD',len(c),l[:80]); continue
        qr[c[0]]=dict(zip(['id','tier','issues','text','acc','why'],c))
# engineer
eng={}; engnew=[]
t=rd(R+'docs/requirements_review/perspective_data_engineer.md')
a=t.index('### 4.3'); b=t.index('### 4.4'); c_=t.index('### 4.5')
for l in t[a:b].splitlines():
    if l.startswith('| R-'):
        c=cells(l); 
        if len(c)!=5: print('EBAD',len(c),l[:60])
        eng[c[0]]=dict(zip(['id','verdict','text','acc','why'],c))
for l in t[b:c_].splitlines():
    if l.startswith('| new-'):
        c=cells(l)
        if len(c)!=6: print('ENBAD',len(c),l[:60])
        engnew.append(dict(zip(['id','tier','text','acc','lands','why'],c)))
# analyst
ana={}; ananew=[]
t=rd(R+'docs/requirements_review/perspective_espn_analyst.md')
a=t.index('### 4.2'); b=t.index('### 4.3'); c_=t.index('## 5. New'); d=t.index('## 6.')
for l in t[a:b].splitlines():
    if l.startswith('| R-'):
        c=cells(l)
        if len(c)!=6: print('ABAD',len(c),l[:60])
        ana[c[0]]=dict(zip(['id','verdict','text','acc','lands','why'],c))
for l in t[c_:d].splitlines():
    if l.startswith('| new-'):
        c=cells(l)
        if len(c)!=6: print('ANBAD',len(c),l[:60])
        ananew.append(dict(zip(['id','tier','text','acc','lands','why'],c)))
# scientist
sci={}; scinew=[]
t=rd(R+'docs/requirements_review/perspective_team_data_scientist.md')
a=t.index('### 4.2'); b=t.index('### 4.3'); d=t.index('## 5.')
for m in re.finditer(r'\*\*(R-[A-Z]{2}-\d+) · (\w+)\.\*\* (.*)',t[a:b]):
    body=m[3]
    acc=''; lands=''; why=''
    mm=re.search(r'Acceptance: (.*?)(?= Lands:| Why:|$)',body); 
    if mm: acc=mm[1]
    mm=re.search(r'Lands: (.*?)(?= Why:|$)',body)
    if mm: lands=mm[1]
    mm=re.search(r'Why: (.*)$',body)
    if mm: why=mm[1]
    text=re.split(r' Acceptance: | Lands: | Why: ',body)[0]
    sci[m[1]]=dict(id=m[1],verdict=m[2],text=text,acc=acc,lands=lands,why=why)
for l in t[b:d].splitlines():
    if l.startswith('| new-'):
        c=cells(l)
        if len(c)!=6: print('SNBAD',len(c),l[:60])
        scinew.append(dict(zip(['id','tier','text','acc','lands','why'],c)))
# ontology / 007
onto=yaml.safe_load(open(R+'config/game_ontology.yaml'))
leafname={n['id']:n['name'] for n in onto['nodes']}
leaves_by_req=collections.defaultdict(list)
inbox007=[]
for n in onto['nodes']:
    for rid in n.get('requirement_ids') or []: leaves_by_req[rid].append(n['id'])
    for g in n.get('gaps') or []:
        if g.get('proposed_id'):
            inbox007.append(dict(id=g['proposed_id'],tier=g['tier'],text=g['text'],acc=g['acceptance'],lands=g.get('implies',''),leaf=n['id'],prio=g.get('priority')))
# round2
r2=[]
t=rd(R+'docs/data/gap_closures_round2.md')
cur_leaves=[]
for l in t.splitlines():
    if l.startswith('### '):
        cur_leaves=re.findall(r'\b([A-M]\.\d\d\.\d\d)\b',l)
    m=re.match(r'^- \*\*(new-[A-Z]{2}-\d+) \((Shall|Should)\)\.\*\* (.*)$',l)
    if m:
        body=m[3]
        text,_,rest=body.partition(' *Acceptance:* ')
        refines=re.findall(r'Refines (new-[A-Z]{2}-\d+)',rest)
        acc=re.sub(r' ?Refines .*$','',rest)
        r2.append(dict(id=m[1],tier=m[2],text=text,acc=acc,leaf=cur_leaves,refines=refines))
# tables proposed changes: req -> columns
tpc=yaml.safe_load(open(R+'schema/tables_proposed_changes.yaml'))
cols_by_req=collections.defaultdict(list)
for ca in tpc['column_additions']:
    for rid in ca.get('requirement_ids') or []: cols_by_req[rid].append(ca['table']+'.'+ca['column'])
# invariants
inv=yaml.safe_load(open(R+'config/invariants.yaml'))
ivnew=[dict(id=x['id'],tier=x.get('tier'),text=x['statement'],tables=x.get('tables'),rule=x.get('rule_refs'),scope=x.get('scope'),on_break=x.get('on_break')) for x in inv['invariants'] if x['id'].startswith('new-')]
print(len(live),len(at),len(qr),len(qr_nochange),len(eng),len(engnew),len(ana),len(ananew),len(sci),len(scinew),len(inbox007),len(r2),len(ivnew))
json.dump(dict(live=live,order=order,qr=qr,qr_nochange=sorted(qr_nochange),eng=eng,engnew=engnew,ana=ana,ananew=ananew,sci=sci,scinew=scinew,inbox007=inbox007,r2=r2,ivnew=ivnew,cols_by_req=cols_by_req,leaves_by_req=leaves_by_req,leafname=leafname),open('parsed.json','w'),indent=1,default=str)
