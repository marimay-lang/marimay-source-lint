#!/usr/bin/env python3
"""Sequential whole-process measurements; BUDGETS.md is fixed before samples."""
import hashlib, json, platform, re, time
from pathlib import Path
from mmay_acceptance import Application
ROOT=Path(__file__).resolve().parents[1]
APP=Application(ROOT,timeout=240)
WORK=ROOT/'build'/('measure-'+str(time.time_ns())); WORK.mkdir(parents=True)
def encoded(value): return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()+b'\n'
if ROOT.name=='marimay-delimited':
    args=['csv-to-json','-']
    small=b'a,b\n'; small_output=encoded({'version':1,'rows':[['a','b']]})
    row=(b'a'*31+b',')*7+b'a'*31+b'\n'
    datasets=[('small',small,small_output),('stateful-256k-v1',row*1024,encoded({'version':1,'rows':[['a'*31]*8]*1024})),('stateful-512k-v1',row*2048,encoded({'version':1,'rows':[['a'*31]*8]*2048}))]
else:
    args=['--json','-']; row=b'//'+b'x'*61+b'\n'
    output=encoded({'version':1,'count':0,'files':[{'path':'-','findings':[]}]})
    datasets=[('small',b'x\n',output),('stateful-256k-v1',row*4096,output),('stateful-512k-v1',row*8192,output)]
grants=['--max-heap-bytes','67108864']
binary=WORK/'app-release'
started=time.monotonic()
APP.successful([APP.compiler,'build','.',*grants,'--release','--output',str(binary)])
build_seconds=time.monotonic()-started
engines={'native':[str(binary)],'vm':[APP.compiler,'run','.',*grants,'--']}
records=[]
for name,data,expected in datasets:
    for engine,prefix in engines.items():
        for repetition in range(4 if name=='small' else 2):
            command=[*prefix,*args]
            timer=['/usr/bin/time','-l' if platform.system()=='Darwin' else '-v']
            start=time.monotonic(); result=APP.run([*timer,*command],input=data); seconds=time.monotonic()-start
            assert (result.returncode,result.stdout)==(0,expected),(name,engine,result.returncode,result.stdout[:500],result.stderr[:500])
            pattern=rb'^\s*(\d+)\s+maximum resident set size\s*$' if platform.system()=='Darwin' else rb'Maximum resident set size \(kbytes\):\s*(\d+)'
            found=re.search(pattern,result.stderr,re.M); rss=int(found[1])*(1 if platform.system()=='Darwin' else 1024) if found else None
            budget=(0.1 if engine=='native' else 0.5) if name=='small' else (2 if engine=='native' else 20)
            rss_budget=(128 if engine=='native' else 256)*1024*1024
            records.append(dict(dataset=name,engine=engine,repetition=repetition,seconds=seconds,seconds_budget=budget,within_time_budget=seconds<=budget,rss_bytes=rss,rss_budget=rss_budget,within_rss_budget=None if rss is None else rss<=rss_budget,stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),command=command,timing_stderr=result.stderr.decode()))
            print(ROOT.name,name,engine,repetition,round(seconds,4),rss,flush=True)
APP.successful([APP.compiler,'test','.','--engine','both'])
start=time.monotonic(); tests=APP.successful([APP.compiler,'test','.','--engine','both']); test_seconds=time.monotonic()-start
report={'schema':ROOT.name+'.measurements/1','harness':APP.metadata(engines),'conditions':'Sequential ordinary desktop. First native execution immediately after this build; no application warmup, no OS-cache eviction or fresh-host claim.','sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*.my'))},'budgets_sha256':hashlib.sha256((ROOT/'BUDGETS.md').read_bytes()).hexdigest(),'build_seconds':build_seconds,'datasets':[dict(name=n,input_bytes=len(d),input_sha256=hashlib.sha256(d).hexdigest(),stdout_sha256=hashlib.sha256(e).hexdigest()) for n,d,e in datasets],'records':records,'test_both':dict(seconds=test_seconds,seconds_budget=2,within_budget=test_seconds<=2,stdout=tests.decode())}
(WORK/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(ROOT/'build/latest-measurement.txt').write_text(str(WORK/'report.json')+'\n')
print(WORK/'report.json',flush=True)
