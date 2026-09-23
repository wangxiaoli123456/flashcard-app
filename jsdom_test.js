const fs=require('fs');
const {JSDOM,VirtualConsole}=require('jsdom');
const html=fs.readFileSync('/tmp/fc/index.html','utf8');
const vc=new VirtualConsole(); vc.on('jsdomError',e=>{});
const dom=new JSDOM(html,{runScripts:'dangerously',virtualConsole:vc,url:'https://example.com/flashcard-app/',
  beforeParse(window){
    window.fetch=()=>Promise.resolve({ok:false,text:()=>Promise.resolve('')});
    try{Object.defineProperty(window,'localStorage',{value:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},configurable:true});}catch(e){}
    try{window.indexedDB={open:()=>({onsuccess:null,onerror:null,onupgradeneeded:null,result:{createObjectStore:()=>{}}})};}catch(e){}
  }});
const w=dom.window;
setTimeout(()=>{
  // 模拟：用户答错了 2 个词
  try{
    w.eval("recordDrill('drill',10,['CARD_A','CARD_B']);");
    const cnt=w.eval("Object.keys(store.drillWrong).length");
    console.log('写入后 drillWrong 数量:',cnt);
    w.eval("switchTab('wrong');");
    const html=w.document.getElementById('page-wrong').innerHTML;
    console.log('page-wrong 含 dr-item 卡片:', html.includes('dr-item'));
    console.log('page-wrong 含 CARD_A 文本:', html.includes('CARD_A'));
    console.log('page-wrong 含 错 次数 角标:', html.includes('dr-badge'));
    console.log('page-wrong 长度:', html.length);
  }catch(e){ console.log('THROW:',e.message); }
  process.exit(0);
},2500);
