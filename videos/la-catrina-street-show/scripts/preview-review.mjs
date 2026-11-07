// Run only through Run-VideoTool.ps1: its shared mutex, Job and deadline own
// the background preview server and this isolated software-browser client.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';

if(process.env.THREEPP_FILM_SUPERVISED!=='1') throw new Error('Use npm run preview so the shared supervisor owns the preview.');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const proof=path.join(root,'proof');
const caches=[path.join(process.env.LOCALAPPDATA ?? '', 'npm-cache', '_npx'),
  path.join(process.env.USERPROFILE ?? '', 'AppData','Local','npm-cache','_npx')];
const candidates=[path.join(root,'node_modules','hyperframes')];
for(const cache of new Set(caches)) if(fs.existsSync(cache)) for(const name of fs.readdirSync(cache).sort()) candidates.push(path.join(cache,name,'node_modules','hyperframes'));
const hf=candidates.find(dir=>{
  try{return JSON.parse(fs.readFileSync(path.join(dir,'package.json'),'utf8')).version==='0.9.19';}catch{return false;}
});
if(!hf) throw new Error('The pinned local HyperFrames 0.9.19 package is missing; no preview was started.');
if(process.env.HYPERFRAMES_DESKTOP_PROJECT) throw new Error('A desktop-app-owned project must use its existing preview; no second server was started.');
const chrome=[process.env.ProgramFiles,process.env['ProgramFiles(x86)'],process.env.LOCALAPPDATA]
  .filter(Boolean).map(dir=>path.join(dir,'Google','Chrome','Application','chrome.exe')).find(fs.existsSync);
if(!chrome) throw new Error('Local Chrome is missing; no preview was started.');
const puppeteer=createRequire(path.join(hf,'package.json'))('puppeteer-core');
const cli=path.join(hf,'bin','hyperframes.mjs');
function preview(...args){
  const result=spawnSync(process.execPath,[cli,'preview',...args,'--json'],{
    cwd:root,encoding:'utf8',windowsHide:true,timeout:45000,
    env:{...process.env,PRODUCER_BROWSER_GPU_MODE:'software',PRODUCER_LOW_MEMORY_MODE:'true'}
  });
  if(result.error || result.status!==0) throw new Error(`Preview ${args[0]} failed: ${result.error?.message ?? result.stderr}`);
  const receipt=JSON.parse(result.stdout.trim());
  if(receipt.ok!==true) throw new Error(`Preview ${args[0]} was refused: ${JSON.stringify(receipt.error)}`);
  return receipt.result;
}
const existing=preview('--status');
if(existing.state!=='not-running') throw new Error('An existing preview is running. It was left untouched; finish that review before this supervised stage.');
let session, browser, review, stopped=false;
try{
  session=preview('--background','--no-open','--no-browser-gpu');
  const status=preview('--status');
  if(status.state!=='running' || status.pid!==session.pid) throw new Error('The new preview did not remain running.');
  const url=new URL(session.studioUrl);
  if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname)) throw new Error('Preview must stay on this computer.');
  const response=await fetch(session.serverUrl,{signal:AbortSignal.timeout(10000)});
  if(response.status!==200) throw new Error(`Preview returned HTTP ${response.status}.`);
  console.log(`Editable preview: ${session.studioUrl}`);
  console.log('Opening an isolated software-only review client. The server stays available during the bounded review.');
  browser=await puppeteer.launch({
    executablePath:chrome,headless:true,defaultViewport:{width:960,height:600,deviceScaleFactor:1},
    timeout:45000,args:['--disable-gpu','--mute-audio','--window-size=960,600','--no-first-run','--no-default-browser-check']
  });
  const page=await browser.newPage();
  const pageErrors=[];
  page.on('pageerror',error=>pageErrors.push(error.message));
  await page.goto(session.studioUrl,{waitUntil:'networkidle2',timeout:45000});
  let composition=null;
  const deadline=Date.now()+30000;
  while(Date.now()<deadline && !composition){
    for(const frame of page.frames()){
      const state=await frame.evaluate(()=>{
        // The pinned player owns an open shadow root. Search both light DOM
        // and any nested open roots; page.frames() still handles its iframe.
        function queryOpenRoots(root,selector){
          const matches=[...root.querySelectorAll(selector)];
          for(const host of [root,...root.querySelectorAll('*')]){
            if(host.shadowRoot) matches.push(...queryOpenRoots(host.shadowRoot,selector));
          }
          return matches;
        }
        const main=queryOpenRoots(document,'[data-composition-id="main"][data-duration="48"]')[0];
        if(!main) return null;
        return {duration:Number(main.dataset.duration),width:Number(main.dataset.width),height:Number(main.dataset.height),
          videos:queryOpenRoots(main,'video').map(v=>({src:v.currentSrc || v.src,readyState:v.readyState,width:v.videoWidth,height:v.videoHeight,error:v.error?.code ?? null}))};
      }).catch(()=>null);
      if(state?.videos.some(v=>v.readyState>=2 && v.width===960 && v.height===600 && v.error===null)) {composition=state;break;}
    }
    if(!composition) await delay(500);
  }
  if(!composition || composition.width!==960 || composition.height!==600) throw new Error('The editable preview did not load the native 48-second composition and a decoded 960x600 video.');
  if(pageErrors.length) throw new Error(`Preview page error: ${pageErrors.join('; ')}`);
  const screenshot='proof/preview-editor.png';
  await page.screenshot({path:path.join(root,screenshot),fullPage:false});
  const bodyText=await page.evaluate(()=>document.body.innerText);
  review={status:'PASS',cliVersion:'0.9.19',studioUrl:session.studioUrl,httpStatus:response.status,
    openedHeadless:true,browserGpu:'software',viewport:{width:960,height:600},
    title:await page.title(),composition,pageErrors,screenshot,
    screenshotSha256:createHash('sha256').update(fs.readFileSync(path.join(root,screenshot))).digest('hex'),
    frameyMentioned:/Keep editing by chatting with Framey|Edit with Framey/i.test(bodyText),
    listeningReviewed:false,reviewWindowSeconds:30};
  console.log(`Preview loaded; screenshot: ${screenshot}. Closing this review session in 30 seconds.`);
  await delay(30000);
} finally {
  try {if(browser) await browser.close();} finally {
    if(session){
      const status=preview('--status');
      if(status.state==='running' && status.pid!==session.pid) throw new Error('Preview ownership changed; the other server was left untouched.');
      preview('--stop');
      stopped=preview('--status').state==='not-running';
      if(!stopped) throw new Error('Preview did not stop cleanly.');
    }
  }
}
if(!review || !stopped) throw new Error('Preview review is incomplete.');
fs.writeFileSync(path.join(proof,'preview-session.json'),JSON.stringify({...review,stopped},null,2)+'\n');
console.log('Preview verified and stopped. Inspect its screenshot before rendering.');
