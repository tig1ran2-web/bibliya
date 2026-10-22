'use strict';
const CACHE='bibliya-shell-0181';
const base=new URL('./',self.location.href);
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(['./','./index.html','./main.dart.js','./flutter_bootstrap.js','./manifest.json'].map(p=>new URL(p,base).href))).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('bibliya-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.origin!==base.origin||!url.pathname.startsWith(base.pathname))return;
  if(url.pathname.includes('/__slovo_modules_v1/'))return;
  event.respondWith((async()=>{
    const cache=await caches.open(CACHE);
    const old=await cache.match(event.request);
    const fresh=()=>fetch(event.request).then(response=>{if(response.ok)cache.put(event.request,response.clone()).catch(()=>{});return response;});
    if(event.request.mode==='navigate'||url.pathname.endsWith('.html')||url.pathname.endsWith('flutter_bootstrap.js')){try{return await fresh();}catch(e){if(old)return old;throw e;}}
    return old||fresh();
  })());
});
