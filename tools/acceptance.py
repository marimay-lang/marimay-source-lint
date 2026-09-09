#!/usr/bin/env python3
"""App-owned byte/status/filesystem oracles; unchanged process harness v1."""
import csv, hashlib, io, json, os, random, subprocess, time
from pathlib import Path
from mmay_acceptance import Application
ROOT = Path(__file__).resolve().parents[1]
APP = Application(ROOT, timeout=180)
WORK = ROOT / 'build' / 'acceptance'
WORK.mkdir(parents=True, exist_ok=True)
DATA, OUTPUT = WORK/'вход ü.txt', WORK/'выход.txt'
started = time.monotonic()
engines = APP.engines(WORK, 'app', ['--allow-read', str(WORK), '--allow-write', str(WORK), '--max-heap-bytes', '67108864'])
results = []
def encoded(value): return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()+b'\n'
def err(message): return (ROOT.name+': '+message+'\n').encode()
def case(arguments, data, expected, selected=None, prepare=None, extra=None):
    def verify(engine, result):
        assert (result.stdout, result.stderr) == expected[1:], (arguments, engine, result.stdout, result.stderr, expected)
        if extra is not None: extra()
    APP.compare(engines if selected is None else selected, arguments, expected[0], data=data, verify=verify, prepare=prepare)
    results.append({'arguments':arguments, 'data_sha256':hashlib.sha256(data or b'').hexdigest(), 'status':expected[0], 'stdout_sha256':hashlib.sha256(expected[1]).hexdigest(), 'stderr':expected[2].decode()})
def output_is(value): assert OUTPUT.read_bytes() == value
MESSAGES = {'L001':'Пробелы в конце строки','L002':'Табуляция в отступе','L003':'TODO/FIXME в комментарии','L004':'Незавершённая строка, комментарий или интерполяция','L005':'Нет LF в конце файла','L006':'Одиночный CR; используйте LF или CRLF'}
def finding(code,start,end,line,column,message=None):
    return dict(code=code,message=MESSAGES[code] if message is None else message,startByte=start,endByte=end,line=line,column=column)
def report(rows,name='-'): return encoded(dict(version=1,count=len(rows),files=[dict(path=name,findings=rows)]))
error_status, base, small = 2, ['--json'], b'x\n'
expected_small = report([])
for source in [b'',b'fn main(): void {}\n',b'const x = "TODO // /*  ";\n',b'const x = r"/* TODO \\ ";\n',b'const x = $"{{TODO}} {f("x")}  ";\n',b'/* nested /* TODOx */ xTODO FIXMEx */\n','/* яTODO */\n'.encode(),b'// done\r\n']:
    case([*base,'-'],source,(0,report([]),b''))
rows = [finding('L002',0,1,1,1),finding('L003',7,11,1,7),finding('L001',11,13,1,11)]
sample = '\t// я TODO  \r\n'.encode()
case([*base,'-'],sample,(1,report(rows),b''))
plain = ''.join(f'-:{r["line"]}:{r["column"]}: {r["code"]}: {r["message"]}\n' for r in rows).encode()
case(['-'],sample,(1,plain,b''))
case([*base,'-'],'🌍'.encode(),(1,report([finding('L005',4,4,1,2)]),b''))
case([*base,'-'],b'/* TODO',(1,report([finding('L004',0,1,1,1),finding('L003',3,7,1,4),finding('L005',7,7,1,8)]),b''))
case([*base,'-'],b'x\ry\n',(1,report([finding('L006',1,2,1,2)]),b''))
case([*base,'-'],b'$"}"\n',(1,report([finding('L004',2,3,1,3,'Одиночная } в интерполированной строке')]),b''))
case([*base,'-','--max-findings','0'],small,(0,report([]),b''))
case([*base,'-','--max-findings','1'],b'// TODO FIXME\n',(2,b'',err('-: Превышен лимит замечаний')))
case([*base,'-'],b'/*'*257,(2,b'',err('-: Превышен лимит вложенности 256')))
case([*base,'-'],b'a\xff',(2,b'',err('-: Недопустимый UTF-8 в байте 1')))
large = (b'//'+b'x'*61+b'\n')*8192
case([*base,'-'],large,(0,report([]),b''))
case([],b'',(2,b'',err('Нужен хотя бы один ФАЙЛ; см. --help')))
DATA.write_bytes(sample)
case([*base,str(DATA),str(DATA)],None,(1,report(rows,str(DATA)),b''))
DATA.write_bytes(b'// TODO\n')
case([*base,str(DATA),'-','--max-findings','1'],b'// FIXME\n',(2,b'',err('-: Превышен лимит замечаний')))
bad_data, bad_error = b'\xff', err('-: Недопустимый UTF-8 в байте 0')
file_output = report([],str(DATA))
case([*base,'-','--max-input','1'],b'ab',(error_status,b'',err('-: standard input exceeds 1-byte limit')))
case([*base,'-','--max-input',str(len(small))],small,(0,expected_small,b''))
case([*base,'-','--wat'],b'',(2,b'',err('unknown option --wat at argument 2')))
DATA.write_bytes(small)
case([*base,str(DATA)],None,(0,file_output,b''))
case([*base,str(DATA),'--max-input','1'],None,(error_status,b'',err(str(DATA)+': file exceeds 1-byte limit')))
case([*base,'-','--output',str(OUTPUT)],small,(0,b'',b''),prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(expected_small))
case([*base,'-','--output',str(OUTPUT)],bad_data,(error_status,b'',bad_error),prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(b'original'))
case([*base,'-','--max-output','0','--output',str(OUTPUT)],small,(error_status,b'',err('Превышен лимит вывода 0 байт')),prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(b'original'))
missing = WORK/'missing'
case([*base,str(missing)],None,(error_status,b'',err(str(missing)+': filesystem path was not found')))
for value,message in [('-1','--max-input: допустимо 0..1048576'),('1048577','--max-input: допустимо 0..1048576'),('no','--max-input: ожидается целое число')]:
    case([*base,'-','--max-input='+value],b'',(2,b'',err(message)))
def verify_help(engine,result):
    assert not result.stderr and ROOT.name.encode() in result.stdout and b'--max-input' in result.stdout
APP.compare(engines,['--help'],0,verify=verify_help)
denied_bin = WORK/'denied'
APP.successful([APP.compiler,'build','.','--release','--output',str(denied_bin)])
denied = {'vm':[APP.compiler,'run','.','--'],'release':[str(denied_bin)]}
case([*base,str(DATA)],None,(error_status,b'',err(str(DATA)+': fs.read capability denied for '+str(DATA))),selected=denied)
case([*base,'-','--output',str(OUTPUT)],small,(error_status,b'',err('fs.write capability denied for '+str(OUTPUT))),selected=denied,prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(b'original'))
pipes = []
if os.name != 'nt':
    link=WORK/'link'
    if link.is_symlink(): link.unlink()
    link.symlink_to(DATA)
    case([*base,str(link)],None,(error_status,b'',err(str(link)+': symbolic links are not followed')))
    case([*base,'-','--output',str(link)],small,(error_status,b'',err('symbolic links are not followed')))
    assert DATA.read_bytes()==small
    for engine,prefix in engines.items():
        read_fd,write_fd=os.pipe(); os.close(read_fd)
        try: child=subprocess.Popen([*prefix,*base,'-'],cwd=ROOT,stdin=subprocess.PIPE,stdout=write_fd,stderr=subprocess.PIPE)
        finally: os.close(write_fd)
        _,error=child.communicate(small,timeout=180)
        assert child.returncode==error_status and (b'standard stream write failed' in error or b'standard stream flush failed' in error),(engine,child.returncode,error)
        pipes.append({'engine':engine,'status':child.returncode,'stderr':error.decode()})
assert DATA.read_bytes()==small
sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*.my'))}
report_data={'schema':ROOT.name+'.acceptance/1','harness':APP.metadata(engines),'sources':sources,'cases':results,'closed_pipes':pipes,'large_bytes':len(large),'managed_heap_limit':67108864,'elapsed_seconds':time.monotonic()-started}
(WORK/'report.json').write_text(json.dumps(report_data,ensure_ascii=False,indent=2)+'\n')
print(f'{ROOT.name}: {len(results)} cases + help; VM/native Debug/Release; {len(pipes)} closed pipes; {len(large)}-byte input')
