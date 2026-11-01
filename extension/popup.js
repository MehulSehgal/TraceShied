const ORIG=['https://www.instagram.com/*'],$=id=>document.getElementById(id);
async function status(){const{consent}=await chrome.storage.local.get('consent');const has=await chrome.permissions.contains({origins:ORIG});
 $('st').textContent=consent&&has?'Active on Instagram (local only)':has?'Paused':'Not enabled'}
$('ok').onchange=()=>{$('en').disabled=!$('ok').checked};
$('en').onclick=async()=>{const g=await chrome.permissions.request({origins:ORIG});if(!g){$('st').textContent='Permission was not granted';return}
 await chrome.storage.local.set({consent:true});
 try{await chrome.scripting.unregisterContentScripts({ids:['ts']})}catch(e){}
 await chrome.scripting.registerContentScripts([{id:'ts',matches:ORIG,js:['engine.js','content.js'],runAt:'document_idle',persistAcrossSessions:true}]);
 const[t]=await chrome.tabs.query({active:true,currentWindow:true});
 if(t&&t.url&&t.url.startsWith('https://www.instagram.com/'))try{await chrome.scripting.executeScript({target:{tabId:t.id},files:['engine.js','content.js']})}catch(e){}
 status()};
$('pa').onclick=async()=>{await chrome.storage.local.set({consent:false});status()};
$('rv').onclick=async()=>{await chrome.storage.local.set({consent:false});try{await chrome.scripting.unregisterContentScripts({ids:['ts']})}catch(e){}await chrome.permissions.remove({origins:ORIG});status()};
status();
