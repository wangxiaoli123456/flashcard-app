import json, sys, asyncio
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

JS = r"""
() => new Promise(async (resolve, reject) => {
  let osc = [];
  const OrigAC = window.AudioContext || window.webkitAudioContext;
  const proto = OrigAC.prototype;
  const origCreate = proto.createOscillator;
  let analyser = null, sink = null, failed=null;
  proto.createOscillator = function(){
    const o = origCreate.call(this);
    const realStart = o.start.bind(o);
    o.start = (t)=>{ try{ osc.push({f:Math.round(o.frequency.value), type:o.type}); }catch(e){} return realStart(t); };
    try{
      if(!analyser){ analyser=this.createAnalyser(); analyser.fftSize=2048; sink=this.createGain(); sink.gain.value=0; analyser.connect(sink); sink.connect(this.destination); }
      o.connect(analyser);
    }catch(e){ failed=String(e); }
    return o;
  };
  try{ ['pointerdown','touchstart','click'].forEach(ev=>document.body.dispatchEvent(new MouseEvent(ev,{bubbles:true}))); }catch(e){}
  await new Promise(r=>setTimeout(r,300));
  const stBefore = (window._actx && window._actx.state) || (ac()&&ac().state);
  osc = [];
  sfx('ok');
  let peak=0; const t0=performance.now();
  while(performance.now()-t0 < 750){
    if(analyser){
      const buf=new Uint8Array(analyser.fftSize);
      analyser.getByteTimeDomainData(buf);
      for(let i=0;i<buf.length;i++){ const d=Math.abs(buf[i]-128); if(d>peak)peak=d; }
    }
    await new Promise(r=>setTimeout(r,30));
  }
  const stAfter = (window._actx && window._actx.state) || (ac()&&ac().state);
  resolve(JSON.stringify({acStateBefore:stBefore, acStateAfter:stAfter, oscOk:osc.length, detail:osc, audioPeak0to255:peak, audible:peak>4, hookErr:failed}));
})
"""

def run():
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
        pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
        pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2000)
        # 用 race 防 evaluate 挂死
        try:
            res = pg.evaluate("Promise.race([("+JS+")(), new Promise((_,rej)=>setTimeout(()=>rej(new Error('EVAL_TIMEOUT')),20000))])")
        except Exception as e:
            print('EVAL ERROR:', e); b.close(); return
        try: res = json.loads(res) if isinstance(res,str) else res
        except: pass
        print('SOUND V397:', json.dumps(res, ensure_ascii=False, indent=1))
        b.close()

run()
print('done')
