import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

HTML = r"""<html><body><script>
let _actx=null, _count=0;
function ac(){ if(!_actx){ _actx=new (window.AudioContext||window.webkitAudioContext)();
  const P=_actx.constructor.prototype, oc=P.createOscillator;
  P.createOscillator=function(){ _count++; return oc.call(this); }; }
  if(_actx.state==='suspended') _actx.resume(); return _actx; }
function buildSfx(schedule){
  return function(kind){
    const ctx=ac(); const seq={ok:[392,523,659,784]}; const freqs=seq[kind]; if(!freqs)return;
    const play=function(){ const now=ctx.currentTime; freqs.forEach((f,i)=>{ const o=ctx.createOscillator(),g=ctx.createGain(); o.type='triangle'; o.frequency.value=f; const t=now+0.03+i*0.11; g.gain.setValueAtTime(0.0001,t); g.gain.exponentialRampToValueAtTime(0.42,t+0.025); g.gain.exponentialRampToValueAtTime(0.0001,t+0.5); o.connect(g); g.connect(ctx.destination); o.start(t); o.stop(t+0.55); }); };
    if(schedule==='old'){ play(); }
    else { if(ctx.state==='suspended'){ ctx.resume().then(play).catch(play); } else play(); }
  };
}
const sfxOld=buildSfx('old'), sfxNew=buildSfx('new');
window.__reset=function(){ _count=0; };
window.__test=async function(mode, suspendFirst){
  window.__reset();
  const ctx=ac();
  if(suspendFirst){ await ctx.suspend(); await new Promise(r=>setTimeout(r,60)); }
  (mode==='old'?sfxOld:sfxNew)('ok');
  await new Promise(r=>setTimeout(r,400)); // 等 resume().then(play) 执行完
  return {stateAfter:ctx.state, oscillatorsCreated:_count};
};
</script></body></html>"""

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_context(viewport={'width':390,'height':844},has_touch=True).new_page()
    pg.set_content(HTML); pg.wait_for_timeout(300)
    # 运行态用新写法
    r1 = pg.evaluate("window.__test('new', false)")
    # 挂起态用新写法（关键：resume().then 必须仍排下4个音）
    r2 = pg.evaluate("window.__test('new', true)")
    # 挂起态用旧写法
    r3 = pg.evaluate("window.__test('old', true)")
    print('NEW running :', json.dumps(r1))
    print('NEW suspended:', json.dumps(r2))
    print('OLD suspended:', json.dumps(r3))
    b.close()
