"""工作台 v2.7 增量更新 — anchor 用 </script> 末尾"""
from pathlib import Path

fp = Path(r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\.workbuddy\artifacts\lobster-design-jiedan-station.html')
txt = fp.read_text(encoding='utf-8')

# JS 在 </script> 前注入
ANCHOR = '</script>\n</body>'
NEW_JS = '''
// ===================== v2.7 嵌入式活动流 + 5子库 =====================
function openActivityIframe(){
  const url = (window.location.protocol==='file:'
    ? 'http://127.0.0.1:18765/.workbuddy/activity_stream.jsonl?ts='+Date.now()
    : '../.workbuddy/activity_stream.jsonl?ts='+Date.now());
  fetch(url).then(function(r){return r.ok?r.text():Promise.reject('HTTP '+r.status);}).then(function(t){
    var lines = t.split('\\n').filter(function(x){return x.trim();});
    var colors = {system:'#0ea5e9',hermes:'#7c3aed',codex:'#16a34a',claude:'#db2777',operator:'#f59e0b'};
    var tail = lines.slice(-80).reverse().map(function(l){
      try{
        var o = JSON.parse(l);
        var c = colors[o.agent]||'#64748b';
        return '<div style="padding:5px 8px;border-bottom:1px dashed #e2e8f0;font-family:monospace;font-size:11px"><span style="color:'+c+';font-weight:700">['+o.agent+'/'+o.channel+']</span> <span style="color:#64748b">'+o.ts+'</span> · '+o.action+'</div>';
      }catch(e){return '';}
    }).join('');
    showModal('📡 活动流 · 最近 80 条（共 '+lines.length+' 条）', tail || '暂无活动流', [
      {label:'🔄 刷新', action:function(){openActivityIframe();}},
      {label:'✕ 关闭', action:closeModal}
    ]);
  }).catch(function(e){
    showModal('⚠️ 活动流加载失败', '<div style="padding:20px;text-align:center;color:#ef4444">'+e+'<br><br>HTTP :18765 未启动？跑 scripts/serve_dashboard.py</div>', [
      {label:'✕ 关闭', action:closeModal}
    ]);
  });
}

var SUB_LIBRARIES = [
  {id:'wecom_jd',   name:'企微接单业务库',  path:'01_正在执行实单',                                              desc:'客户需求/聊天/报价/交付/验收 · 永久复盘',    color:'#7c3aed'},
  {id:'gold_dh',    name:'黄金策略库',      path:'CODEX量化策略20260615/\\\\嘉盛',                                 desc:'黄金黑马EA·回测·参数·复盘·版本日志',         color:'#f59e0b'},
  {id:'btc_dh',     name:'黑马策略库',      path:'CODEX量化策略20260615/\\\\币安',                                 desc:'黑马策略多版本·实盘调参·交易记录·监控',     color:'#16a34a'},
  {id:'wangpan_jc', name:'网盘萃取学习库',  path:'网盘课程资源知识萃取与沉淀体系建设',                       desc:'课程萃取笔记·学习素材·沉淀·复盘',         color:'#0891b2'},
  {id:'xianyu_yw',  name:'闲鱼业务库',      path:'闲鱼自动化系统',                                              desc:'闲鱼文案·话术模板·问答库·运营记录',         color:'#db2777'}
];

function openLibModal(){
  var cards = SUB_LIBRARIES.map(function(lib){
    return '<div onclick="recallFromLib(\\\\''+lib.id+'\\\\\')" style="cursor:pointer;border:2px solid '+lib.color+';border-radius:12px;padding:14px;background:#f8fafc;transition:all .2s" onmouseover="this.style.transform=\\'translateY(-2px)\\';this.style.boxShadow=\\'0 6px 16px rgba(0,0,0,.12)\\'" onmouseout="this.style.transform=\\'\\';this.style.boxShadow=\\'\\'">'+
    '<div style="font-size:14px;font-weight:800;color:'+lib.color+'">📚 '+lib.name+'</div>'+
    '<div style="font-size:11px;color:#64748b;font-family:monospace;margin:5px 0">'+lib.path+'</div>'+
    '<div style="font-size:12px;color:#475569">'+lib.desc+'</div>'+
    '<div style="margin-top:8px;font-size:11px;color:'+lib.color+';font-weight:700">👉 点我调取历史案例</div>'+
    '</div>';
  }).join('');
  showModal('📚 5 大子库 · 一键调取历史（龙虾分身永久复盘）',
    '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">'+cards+'</div>'+
    '<div style="margin-top:14px;padding:10px;background:#fef3c7;border-radius:8px;font-size:12px;color:#92400e">⚡ 一人公司大脑：每个子库都是 Agent 的"历史记忆"，接单时直接调取，不需要翻聊天记录。</div>',
    [{label:'✕ 关闭', action:closeModal}]
  );
}

function recallFromLib(libId){
  var lib = SUB_LIBRARIES.find(function(x){return x.id===libId;});
  if(!lib){return;}
  fetch('http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib='+libId+'&ts='+Date.now())
    .then(function(r){return r.ok?r.json():Promise.reject('HTTP '+r.status);})
    .then(function(j){
      var items = (j.cases||[]).map(function(c){
        return '<div style="padding:10px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:8px"><div style="font-weight:700;color:#0f172a">📦 '+(c.name||'?')+'</div><div style="font-size:11px;color:#94a3b8;margin-top:4px">📅 '+(c.date||'')+' · '+(c.size||0)+'B · '+(c.files||1)+' 文件</div></div>';
      }).join('') || '<div style="padding:20px;text-align:center;color:#94a3b8">该子库暂无案例</div>';
      showModal('📚 '+lib.name+' · 历史调取',
        '<div style="background:#f1f5f9;border-radius:8px;padding:8px;margin-bottom:10px;font-size:12px;color:#475569">调取源：<code style="color:#0f172a">'+lib.path+'</code></div>'+items,
        [{label:'↩ 返回', action:openLibModal},{label:'✕ 关闭', action:closeModal}]
      );
    })
    .catch(function(e){showModal('⚠️ 调取失败', '<div style="color:#ef4444;padding:20px">'+e+'<br><br>HTTP :18765 未启动？</div>', [{label:'✕ 关闭', action:closeModal}]);});
}
</script>
</body>'''
if ANCHOR not in txt:
    # 找
    print('未找到</script>\\n</body>，尝试备用')
    if '</script>' in txt:
        # 只在最后一个</script>前插
        idx = txt.rfind('</script>')
        NEW_JS = NEW_JS.replace('</script>\n</body>', '</script>')
        txt = txt[:idx] + NEW_JS + '</body>' + txt[idx+12+11:]
    else:
        raise SystemExit('failed')
else:
    txt = txt.replace(ANCHOR, NEW_JS, 1)

fp.write_text(txt, encoding='utf-8')
print(f'✅ v2.7 JS注入完成 → {len(txt)} B')
