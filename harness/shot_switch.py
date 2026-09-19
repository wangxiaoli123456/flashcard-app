import json
from playwright.sync_api import sync_playwright
CHROME='/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
LYRICS='''Five Little Ducks

Five little ducks went out one day.
Over the hill and far away.
Mother duck said, "Quack, quack, quack, quack."
But only four little ducks came back.
One, two, three, four.

Four little ducks went out one day.
Over the hill and far away.
Mother duck said, "Quack, quack, quack, quack."
But only three little ducks came back.
One, two, three.

Three little ducks went out one day.
Over the hill and far away.
Mother duck said, "Quack, quack, quack, quack."
But only two little ducks came back.
One, two.

Two little ducks went out one day.
Over the hill and far away.
Mother duck said, "Quack, quack, quack, quack."
But only one little duck came back.
One.

One little duck went out one day.
Over the hill and far away.
Mother duck said, "Quack, quack, quack, quack."
But none of the five little ducks came back.

Sad mother duck went out one day.
Over the hill and far away.
Mother duck said, "Quack, quack, quack, quack."
And all of five little ducks came back.

Five little ducks went out one day.
Over the hill and far away.
Mother duck said, "Quack, quack, quack, quack."
And all of the five little ducks came back!'''

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    pg=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.goto('http://127.0.0.1:8899/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(2200)
    pg.evaluate("() => { setLibTab('passage'); }")
    pg.wait_for_timeout(300)
    # 截图开关（默认整篇）
    whole_on = pg.evaluate("() => document.getElementById('pgModeWhole').classList.contains('on')")
    para_on  = pg.evaluate("() => document.getElementById('pgModePara').classList.contains('on')")
    print('① 默认开关: 整篇on=%s 按段on=%s' % (whole_on, para_on))
    pg.screenshot(path='/tmp/fc/sw_default.png')

    # ===== 整篇模式：传整首歌 → 应=1篇 =====
    pg.evaluate("() => { store.passages={}; renderPassagePage(); }")
    pg.fill('#pgText', LYRICS)
    pg.evaluate("() => savePassage()")
    pg.wait_for_timeout(200)
    w = pg.evaluate("() => ({ count: passageList().length, firstLen: (passageList()[0]?passageList()[0].text.length:0), hasTitle: !!(passageList()[0]&&passageList()[0].text.indexOf('Five Little Ducks')===0), hasSad: !!(passageList()[0]&&passageList()[0].text.indexOf('Sad mother duck')>=0) })")
    print('② 整篇模式: %s' % json.dumps(w,ensure_ascii=False))

    # ===== 按段模式：同样内容 → 应=8篇 =====
    pg.evaluate("() => { store.passages={}; renderPassagePage(); setPgMode('para'); }")
    pg.wait_for_timeout(150)
    para_on2 = pg.evaluate("() => document.getElementById('pgModePara').classList.contains('on')")
    pg.fill('#pgText', LYRICS)
    pg.evaluate("() => savePassage()")
    pg.wait_for_timeout(200)
    q = pg.evaluate("() => ({ count: passageList().length, titles: passageList().map(x=>x.text.split('\\n')[0].slice(0,28)) })")
    print('③ 按段模式: para_on=%s %s' % (para_on2, json.dumps(q,ensure_ascii=False)))
    pg.screenshot(path='/tmp/fc/sw_para.png')
    b.close()
print('OK')
