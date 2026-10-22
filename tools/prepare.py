from pathlib import Path
import concurrent.futures,hashlib,json,time,urllib.request,urllib.parse,zipfile
root=Path("site");root.mkdir(exist_ok=True)
manifest=json.loads(Path("asset-manifest.json").read_text())
with zipfile.ZipFile("build-patch.zip") as z:patched=set(z.namelist())
def copy_file(item):
 name,digest=item
 if name in patched or name==".last_build_id":return
 if name.startswith("/") or ".." in Path(name).parts:raise ValueError(name)
 target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
 for attempt in range(4):
  try:
   request=urllib.request.Request("https://sweet-naiad-e6822e.netlify.app/"+urllib.parse.quote(name),headers={"Cache-Control":"no-cache"})
   with urllib.request.urlopen(request,timeout=90) as r:body=r.read()
   if hashlib.sha256(body).hexdigest()!=digest:raise ValueError("Content mismatch: "+name)
   target.write_bytes(body);return
  except Exception:
   if attempt==3:raise RuntimeError("Cannot copy "+name)
   time.sleep(2*(attempt+1))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(copy_file,manifest.items()))
with zipfile.ZipFile("build-patch.zip") as z:z.extractall(root)
(root/".nojekyll").write_text("")
assert json.loads((root/"version.json").read_text())["version"]=="0.18.1"
assert 'canvasKitBaseUrl: "canvaskit/"' in (root/"flutter_bootstrap.js").read_text()
assert '<base href="/bibliya/">' in (root/"index.html").read_text()
print("Verified static site files:",len(list(root.rglob("*"))))

(root/"flutter_service_worker.js").write_text(Path("tools/service-worker.js").read_text())

# Flutter otherwise fetches its default Roboto before the first frame from Google.
font_url="https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf"
with urllib.request.urlopen(font_url,timeout=90) as response:font=response.read()
assert hashlib.sha256(font).hexdigest()=="d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134"
(root/"assets/fonts/Roboto-Regular.ttf").write_bytes(font)
font_manifest=root/"assets/FontManifest.json"
fonts=json.loads(font_manifest.read_text())
for family in ["Roboto","Arial"]:
 fonts=[f for f in fonts if f["family"]!=family]
 fonts.append({"family":family,"fonts":[{"asset":"fonts/Roboto-Regular.ttf"}]})
font_manifest.write_text(json.dumps(fonts,ensure_ascii=False))
with urllib.request.urlopen("https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/OFL.txt",timeout=90) as response:license_text=response.read()
assert hashlib.sha256(license_text).hexdigest()=="061402327a96aadb0bfb694a960ed289ecd38d383e396243831ab81feb109c41"
(root/"assets/fonts/Roboto-OFL.txt").write_bytes(license_text)
