"""Record comparison with the pre-Catrina four-vehicle CPU checkpoint."""
from pathlib import Path
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
baseline=ROOT/'build/sessions/20261106-004743-039'
receipt=read(ROOT/'build/suspension-playground/latest-audit.json');candidate=Path(receipt['session'])
assert read(candidate/'physics-audit/result.json')['status']=='PASS'
exe=ROOT/'build/windows-gl/bin/Release/suspension_playground.exe'
assert hashlib.sha256(exe.read_bytes()).hexdigest()==receipt['binarySha256'].lower()
before=rows(baseline/'physics-audit/checks.csv');after=rows(candidate/'physics-audit/checks.csv')
lookup={(r['vehicle'],r['check']):r for r in after}
changed=[r for r in before if lookup.get((r['vehicle'],r['check']))!=r]
assert len(before)==137 and not changed,changed
trace=rows(candidate/'physics-audit/catrina-hydraulics.csv');metrics={}
for name in dict.fromkeys(r['scenario'] for r in trace):
    group=[r for r in trace if r['scenario']==name]
    detail={k:[min(float(r[k]) for r in group),max(float(r[k]) for r in group)] for k in ('y','speed','frontGap','up','fl','fr','rl','rr','flLoad','frLoad','rlLoad','rrLoad')}
    detail['sampled_contacts']={n:sum(r['contacts']==n for r in group) for n in sorted(set(r['contacts'] for r in group))}
    metrics[name]=detail
result={'status':'PASS','baselineSession':str(baseline),'candidateSession':str(candidate),'binarySha256':receipt['binarySha256'].lower(),'baselineChecks':len(before),'identicalChecks':len(before),'changedChecks':changed,'totalCurrentChecks':receipt['checks'],'traceSampleHz':10,'scenarioMetrics':metrics,'scope':'Exact prior check rows and current hydraulic trace; visual model acceptance is recorded separately.'}
(ROOT/'build/la-catrina/physics-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'PASS: {len(before)} prior check rows unchanged; {receipt["checks"]} current checks.')
