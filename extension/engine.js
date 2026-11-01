const COL={neutral:'#94a3b8',refusal:'#14b8a6',contact_after_refusal:'#60a5fa',guilt_trip:'#f59e0b',ownership:'#a78bfa',surveillance:'#fb7185',veiled_threat:'#f43f5e',reputation_threat:'#e11d48',explicit_threat:'#be123c'};
const K=(l,s,r,m)=>({l,s,r:new RegExp(r,'i'),m});
const KB=[
K('explicit_threat',3,"i will (kill you|hurt you|find you)|dekh lunga|maar dunga|jaan se|chhodunga nahi","Direct threat of harm"),
K('reputation_threat',3,"(sabko|sab ko) bata dun|viral kar|leak|everyone will know|badnaam|screenshots?.{0,25}(share|viral|bhej)","Threatens exposure or shame"),
K('veiled_threat',2,"warna jo hoga|dekh lena|tum pachta|you.?ll regret|see what happens|don.?t make me|anjaam|majboor mat kar","Implies consequences while avoiding an explicit threat"),
K('surveillance',2,"i saw you|saw you at|you were wearing|maine dekha|dekha tumhe|kahan thi|kahan the tum|i.?m outside|outside your|tumhare ghar|i know where you|pata hai tum","Shows the sender is tracking the recipient’s movements"),
K('ownership',1,"tum (sirf )?meri ho|sirf meri|you.?re mine|only mine|kisi aur se baat|mere alawa","Treats the recipient as a possession"),
K('guilt_trip',1,"why are you ignor|why ignor|maine kya galat|after all i|you owe me|reply karo|answer me|tumne mujhe dhoka|mar jaunga|i will die|hurt myself","Pressures through guilt or emotional blackmail")];
const REF=K('refusal',0,"leave me alone|stop (messaging|texting|calling|contacting)|i need (some )?(time|space)|not interested|don.?t (message|text|call|contact)|please stop|mujhe (time|space) chahiye|baat mat karo|pareshan mat karo|mujhe baat nahi karni","Clear request to stop or pause contact");
const TH=['veiled_threat','reputation_threat','explicit_threat'];
const TOX=/idiot|stupid|bitch|bastard|slut|ugly|shut up|hate you|fuck|kutta|kamina|harami|bewakoof|saala|chutiya|gandu/gi;
const PH=/(\+?\d[\d\s\-]{8,}\d)/g,EM=/[\w.\-]+@[\w\-]+\.\w+/g;

function scrub(t){let c=0;const r=t.replace(EM,()=>(c++,'[EMAIL]')).replace(PH,()=>(c++,'[PHONE]'));return[r,c]}
function analyze(raw){
 const M=raw.map((m,i)=>({id:i+1,who:m.who,ts:m.ts,text:m.text,hits:[],label:'neutral',sev:0}));let fr=-1;
 M.forEach((m,i)=>{if(m.who==='me'){if(REF.r.test(m.text)){m.label='refusal';m.hits=[REF];if(fr<0)fr=i}}
  else{KB.forEach(k=>{if(k.r.test(m.text))m.hits.push(k)});if(m.hits.length){const t=m.hits.reduce((a,b)=>b.s>a.s?b:a);m.label=t.l;m.sev=t.s}}});
 M.forEach((m,i)=>{if(fr>=0&&i>fr&&m.who==='them'&&m.label==='neutral'){m.label='contact_after_refusal';m.sev=1}});
 const o=M.filter(m=>m.who==='them'),after=fr>=0?o.filter(m=>m.id>M[fr].id):[];
 const tm=o.filter(m=>m.ts!=null),ns=tm.length?tm.filter(m=>new Date(m.ts).getHours()<5).length/tm.length:0;
 const n=o.length,mx=(n+1)/2,my=o.reduce((a,m)=>a+m.sev,0)/(n||1);let nu=0,de=0;o.forEach((m,i)=>{nu+=(i+1-mx)*(m.sev-my);de+=(i+1-mx)**2});const sl=de?nu/de:0;
 const surv=o.filter(m=>m.hits.some(h=>h.l==='surveillance')).map(m=>m.id),thr=o.filter(m=>m.hits.some(h=>TH.includes(h.l))).map(m=>m.id);
 const P=[['Contact after refusal',after.length+' messages',after.length>=3?2:0],['Night-time share',tm.length?Math.round(ns*100)+'%':'no timestamps',ns>.3?1:0],['Escalation trend',(sl>=0?'+':'')+sl.toFixed(2),sl>.1?1:0],['Surveillance remarks',surv.length?surv.map(i=>'#'+i).join(', '):'none',surv.length?2:0],['Threats',thr.length?thr.map(i=>'#'+i).join(', '):'none',thr.length?3:0]];
 const score=P.reduce((a,p)=>a+p[2],0);
 return{level:score>=5?'High':score>=3?'Elevated':'Low',score,points:P,msgs:M,flagged:M.filter(m=>m.sev>=1||m.label==='refusal')}}
self.TraceEngine={analyze,scrub};
