function todayKey(){const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
function addDays(ds,n){const[y,m,d]=ds.split('-').map(Number);const t=new Date(y,m-1,d);t.setDate(t.getDate()+n);return t.getFullYear()+'-'+String(t.getMonth()+1).padStart(2,'0')+'-'+String(t.getDate()).padStart(2,'0');}
function passageNextDay(nights){ return [0,7,15,30,30,30][nights]||30; }
const MAX=3;
function mk(){ return {state:'new',nights:0,streak:0,next:todayKey()}; }
function mark(p,good,t){
  if(good){
    if(p.state==='hist'){ p.nights=Math.min((p.nights||1)+1,3); p.next=addDays(t,passageNextDay(p.nights)); }
    else { p.streak=(p.streak||0)+1; if(p.streak>=2){ p.state='hist'; p.nights=1; p.next=addDays(t,passageNextDay(1)); } else { p.next=addDays(t,1); } }
  } else { p.streak=0; p.state='wrong'; p.next=addDays(t,1); }
  return p;
}
let pass=0, fail=0;
function chk(name,cond){ if(cond){pass++; console.log('  ✓ '+name);} else {fail++; console.log('  ✗ FAIL: '+name);} }
let t=todayKey();
let p=mk(); chk('新短文当天到期', p.next===t);
mark(p,true,t); chk('第1次会: 未掌握 streak=1', p.state!=='hist'&&p.streak===1);
chk('第1次会: next=明天(隔夜确认)', p.next===addDays(t,1));
const d1=addDays(t,1); mark(p,true,d1); chk('第2次会: 已掌握', p.state==='hist');
chk('掌握: 从确认日+7天 (=t+8)', p.next===addDays(d1,7));
// 复现：掌握后 next=d1+7 = t+8；复现日取 t+8
const r1=addDays(d1,7); mark(p,true,r1); chk('复现L1→L2: +15 (=t+23)', p.next===addDays(r1,15));
const r2=addDays(r1,15); mark(p,true,r2); chk('复现L2→L3: +30', p.next===addDays(r2,30));
const r3=addDays(r2,30); mark(p,true,r3); chk('复现L3保持: +30', p.next===addDays(r3,30));
// 掌握后点不会→降级
mark(p,false,addDays(t,8)); chk('掌握后点不会: 降级wrong', p.state==='wrong');
// 中间点不会清零重数
p=mk(); mark(p,true,t); mark(p,false,addDays(t,1));
chk('点不会: wrong且streak=0', p.state==='wrong'&&p.streak===0);
mark(p,true,addDays(t,2)); mark(p,true,addDays(t,3)); chk('重数2次: 掌握', p.state==='hist');
// 每日上限
chk('到期5/已读0 → 取3', Math.min(5,Math.max(0,MAX-0))===3);
chk('到期5/已读2 → 取1', Math.min(5,Math.max(0,MAX-2))===1);
chk('到期5/已读3 → 取0', Math.min(5,Math.max(0,MAX-3))===0);
console.log('\n结果: 通过 '+pass+' / 失败 '+fail);
process.exit(fail?1:0);
