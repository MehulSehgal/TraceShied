(()=>{if(window.__ts)return;window.__ts=1;
const E=TraceEngine,COLR={High:'#fb7185',Elevated:'#fbbf24',Low:'#4ade80'},RANK={Low:0,Elevated:1,High:2};
let seen=[],host,sh,obs,timer,last='Low',res=null,initial=true;
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const $=id=>sh.getElementById(id);
function ui(){if(host)return;host=document.createElement('div');host.style.cssText='position:fixed;right:16px;bottom:16px;z-index:2147483647;font:14px system-ui,sans-serif';
 sh=host.attachShadow({mode:'closed'});
 sh.innerHTML=`<style>*{box-sizing:border-box}#bd{background:#0b1220;color:#fff;border:2px solid #2dd4bf;border-radius:99px;padding:8px 14px;font:700 13px system-ui;cursor:pointer;float:right}#pn,#al{width:320px;background:#0b1220;color:#e6edf7;border:1px solid #27385a;border-radius:14px;padding:12px;margin-bottom:8px;max-height:60vh;overflow:auto}#al{border-color:#fb7185}li{margin:2px 0}button.s{background:#16233b;color:#fff;border:1px solid #27385a;border-radius:8px;padding:6px 10px;margin:6px 6px 0 0;cursor:pointer;font:600 12px system-ui}.m{color:#a9b8cf;font-size:12px}</style><div id="al" hidden></div><div id="pn" hidden></div><button id="bd">TraceShield</button>`;
 document.documentElement.appendChild(host);
 $('bd').onclick=()=>{$('pn').hidden=!$('pn').hidden;$('al').hidden=true}}
function scan(){const root=document.querySelector('div[role="main"]')||document.body,rb=root.getBoundingClientRect(),mid=rb.left+rb.width/2;
 const f=[...root.querySelectorAll('div[dir="auto"]')].filter(e=>!e.querySelector('div[dir="auto"]')&&!e.closest('a,header,h1,h2,[role="heading"]')&&e.innerText.trim()).map(e=>{const r=e.getBoundingClientRect();return{text:e.innerText.trim(),who:r.left+r.width/2>mid?'me':'them',y:r.top,w:r.width}}).filter(m=>m.w<rb.width*.75).sort((a,b)=>a.y-b.y);
 const key=m=>m.who+'|'+m.text,cnt={},c2={};seen.forEach(m=>cnt[key(m)]=(cnt[key(m)]||0)+1);
 const known=f.map(m=>{const k=key(m);c2[k]=(c2[k]||0)+1;return c2[k]<=(cnt[k]||0)});
 const fk=known.indexOf(true);
 if(seen.length&&fk<0)seen=[];
 const now=initial?null:Date.now(),pre=[],post=[];
 f.forEach((m,i)=>{if(!known[i]){const o={who:m.who,text:m.text,ts:now};(fk<0||i<fk?pre:post).push(o)}});
 seen=[...pre,...seen,...post];initial=false;
 if(seen.length)show(E.analyze(seen))}
function show(r){res=r;ui();const b=$('bd');b.textContent=`TraceShield: ${r.level} (${r.score}/9)`;b.style.borderColor=COLR[r.level];
 $('pn').innerHTML=`<b style="color:${COLR[r.level]}">${r.level} risk, score ${r.score} of 9</b><ul>${r.points.map(p=>`<li>${p[0]}: ${esc(p[1])} (+${p[2]})</li>`).join('')}</ul><div class="m">Flagged messages</div><ul>${r.flagged.slice(-8).map(m=>`<li>#${m.id} ${m.label.replace(/_/g,' ')}: ${esc(m.text.slice(0,70))}</li>`).join('')||'<li>none</li>'}</ul><button class="s" id="sv">Save evidence report</button><button class="s" id="cl">Clear data</button><button class="s" id="ps">Pause</button><div class="m" style="margin-top:8px">Local only. A risk assessment, not a legal verdict.</div>`;
 $('sv').onclick=()=>report(res);$('cl').onclick=()=>{seen=[];res=null;initial=false;$('pn').hidden=true;b.textContent='TraceShield'};$('ps').onclick=()=>chrome.storage.local.set({consent:false});
 if(RANK[r.level]>RANK[last]&&r.level!=='Low'){const a=$('al');a.hidden=false;a.innerHTML=`<b>TraceShield alert</b><br>${r.level==='High'?'A clear escalating pattern was detected.':'Some concerning signals were detected.'} Open the panel to review. Do not delete the messages.`}
 last=r.level}
async function report(r){const h=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(r.msgs.map(m=>[m.who,m.text])))))].map(b=>b.toString(16).padStart(2,'0')).join('');
 const rows=r.flagged.map(m=>`<tr><td>${m.id}</td><td>${m.ts?new Date(m.ts).toLocaleString():'earlier history'}</td><td>${m.who==='me'?'You':'Other person'}</td><td>${esc(m.text)}</td><td>${m.label.replace(/_/g,' ')}</td></tr>`).join('');
 const html=`<!doctype html><meta charset="utf-8"><title>TraceShield report</title><style>body{font:14px system-ui;max-width:800px;margin:24px auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:4px 8px;text-align:left}</style><h1>TraceShield incident report</h1><p>Risk level: <b>${r.level}</b> (score ${r.score} of 9)</p><h3>Signals</h3><ul>${r.points.map(p=>`<li>${p[0]}: ${esc(p[1])} (+${p[2]})</li>`).join('')}</ul><h3>Flagged messages</h3><table><tr><th>ID</th><th>Time</th><th>Sender</th><th>Text</th><th>Pattern</th></tr>${rows}</table><h3>Integrity</h3><p>SHA-256: ${h}<br>Generated: ${new Date().toLocaleString()}<br>Source: Instagram web, read locally in the browser with the user’s consent. Messages already on screen when monitoring began have no timestamps.</p><p><i>A risk assessment, not a legal verdict.</i></p>`;
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([html],{type:'text/html'}));a.download='traceshield-report.html';a.click()}
function start(){ui();host.hidden=false;if(!obs){obs=new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(scan,800)});obs.observe(document.body,{childList:true,subtree:true,characterData:true})}scan()}
function stop(){if(obs){obs.disconnect();obs=null}if(host)host.hidden=true}
chrome.storage.local.get('consent',r=>{if(r.consent)start()});
chrome.storage.onChanged.addListener(c=>{if(c.consent)c.consent.newValue?start():stop()});
})();
