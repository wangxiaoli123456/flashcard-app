import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

JS = r"""
() => new Promise(async (resolve) => {
  let osc=[];
  const P=(window.AudioContext||window.webkitAudioContext).prototype;
  const oc=P.createOscillator;
  P.createOscillator=function(){const o=oc.call(this);const rs=o.start.bind(o);o.start=function(t){osc.push({f:Math.round(o.frequency.value),type:o.type});return rs(t);};return o;};
  ['pointerdown','touchstart','click'].forEach(ev=>document.body.dispatchEvent(new MouseEvent(ev,{bubbles:true})));
  await new Promise(r=>setTimeout(r,300));
  const before=(window._actx&&window._actx.state)||(ac()&&ac().state);
  osc=[]; sfx('ok');
  await new Promise(r=>setTimeout(r,700));
  resolve({acState:before, oscOk:osc.length, detail:osc});
})
"""

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    res=pg.evaluate(JS)
    print('RESULT:'+json.dumps(res,ensure_ascii=False))
    b.close()
