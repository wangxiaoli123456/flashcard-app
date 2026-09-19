import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'

JS = """
() => new Promise(async (resolve) => {
  // 监听 AudioContext 振荡器创建
  let oscCount = {ok:0, bad:0};
  let captured = {};
  const OrigAC = window.AudioContext || window.webkitAudioContext;
  // 挂钩 createOscillator 记录频率与调用次数
  const proto = OrigAC.prototype;
  const origCreate = proto.createOscillator;
  const origResume = proto.resume;
  let tag = 'none';
  proto.createOscillator = function(){
    const o = origCreate.call(this);
    const realStart = o.start.bind(o);
    o.start = function(t){ oscCount[tag]++; captured[tag] = captured[tag]||[]; captured[tag].push(Math.round(o.frequency.value)); return realStart(t); };
    return o;
  };
  // 解锁音频：真实手势
  const fire = () => { try{ ['pointerdown','touchstart','click'].forEach(ev=>document.body.dispatchEvent(new MouseEvent(ev,{bubbles:true}))); }catch(e){} };
  fire();
  await new Promise(r=>setTimeout(r,300));
  window.__acStateBefore = (window._actx && window._actx.state) || (ac() && ac().state);

  // 直接调用 sfx('ok') 与 sfx('bad')，分别打标
  tag='ok'; sfx('ok');
  await new Promise(r=>setTimeout(r,700));
  tag='bad'; sfx('bad');
  await new Promise(r=>setTimeout(r,700));

  resolve({
    acStateBefore: window.__acStateBefore,
    acStateAfter: (window._actx && window._actx.state) || (ac() && ac().state),
    oscOk: oscCount.ok,
    oscBad: oscCount.bad,
    freqsOk: captured.ok || [],
    freqsBad: captured.bad || [],
    _actxExists: !!window._actx
  });
})
"""

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    res = pg.evaluate(JS)
    print('SOUND TEST:', json.dumps(res, ensure_ascii=False, indent=1))
    b.close()
print('done')
