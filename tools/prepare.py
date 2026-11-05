from pathlib import Path
import concurrent.futures,hashlib,json,os,time,urllib.request,urllib.parse,shutil,zipfile
root=Path('site');stage=Path('release-source-stage');stage.mkdir(exist_ok=True)
baseline=json.loads(Path('release-source-map.json').read_text(encoding='utf-8-sig'))
local=os.environ.get('RHEMA_LOCAL_SOURCE')
def copy_file(item):
 name,digest=item
 if name.startswith('/') or '..' in Path(name).parts:raise ValueError(name)
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True)
 if local:
  body=(Path(local)/name).read_bytes()
  assert hashlib.sha256(body).hexdigest()==digest,name
  target.write_bytes(body);return
 for attempt in range(4):
  for base in ['https://tig1ran2-web.github.io/bibliya/release-v0200/','https://tig1ran2-web.github.io/bibliya/preview-v0190/']:
   try:
    url=base+urllib.parse.quote(name)
    with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache'}),timeout=90) as response:body=response.read()
    if hashlib.sha256(body).hexdigest()!=digest:raise ValueError('Hash mismatch '+name)
    target.write_bytes(body);return
   except Exception as error:last=error
  time.sleep(2*(attempt+1))
 raise RuntimeError('Cannot recover release source '+name) from last
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(copy_file,baseline.items()))
assert json.loads((stage/'version.json').read_text())['version']=='0.20.0'
shutil.copytree(stage,root,dirs_exist_ok=True)
# Immutable source snapshot makes repeat publication independent of mutable main files.
shutil.copytree(stage,root/'release-v0200',dirs_exist_ok=True)
with zipfile.ZipFile('main-update.zip') as patch:
 for name in patch.namelist():
  if name.startswith('/') or '..' in Path(name).parts:raise ValueError(name)
 patch.extractall(root)
update_map=json.loads(Path('main-update-map.json').read_text(encoding='utf-8'))
for name,digest in update_map.items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
assert json.loads((root/'version.json').read_text())['version']=='0.20.3'
p=root/'index.html';text=p.read_text(encoding='utf-8').replace('/bibliya/preview-v0190/','/bibliya/').replace('#7053bd','#9c6019');p.write_text(text,encoding='utf-8')
p=root/'manifest.json';manifest=json.loads(p.read_text(encoding='utf-8'));manifest.update(name='Рема / Rhema',short_name='Рема',id='/bibliya/',scope='/bibliya/',start_url='/bibliya/');p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
p=root/'flutter_service_worker.js';worker=p.read_text(encoding='utf-8').replace('bibliya-preview-0200','bibliya-shell-0200').replace("k.startsWith('bibliya-preview-')","k.startsWith('bibliya-shell-')");p.write_text(worker,encoding='utf-8')
preview=root/'preview-v0190';preview.mkdir(exist_ok=True)
(preview/'index.html').write_text('''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Рема</title><script>location.replace('/bibliya/'+location.search+location.hash)</script><a href="/bibliya/">Открыть Рему</a></html>''',encoding='utf-8')
(preview/'flutter_service_worker.js').write_text("self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('bibliya-preview-')).map(k=>caches.delete(k)))).then(()=>self.registration.unregister())));",encoding='utf-8')
(root/'.nojekyll').write_text('')
assert '<base href="/bibliya/">' in (root/'index.html').read_text(encoding='utf-8')
assert manifest['name']=='Рема / Rhema'
assert 'bibliya-shell-0203' in worker and '__slovo_modules_v1' in worker
size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());assert size<1_000_000_000
print('Rhema main release verified; immutable snapshot preserved; total bytes',size)
