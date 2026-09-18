"""修 v2.7 openLibModal JS 错误 — 用更简洁的写法（无 onclick 嵌套）"""
from pathlib import Path

fp = Path(r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\.workbuddy\artifacts\lobster-design-jiedan-station.html')
txt = fp.read_text(encoding='utf-8')

# 替换 onclick="recallFromLib(..." → data-lid="..."
# 然后在 openLibModal 末尾用 addEventListener
import re

OLD = '''function openLibModal(){
  var cards = SUB_LIBRARIES.map(function(lib){
    return '<div onclick="recallFromLib(\\''+lib.id+'\\')" style="cursor:pointer;border:2px solid '+lib.color+';border-radius:12px;padding:14px;background:#f8fafc;transition:all .2s" onmouseover="this.style.transform=\\'translateY(-2px)\\';this.style.boxShadow=\\'0 6px 16px rgba(0,0,0,.12)\\'" onmouseout="this.style.transform=\\'\\';this.style.boxShadow=\\'\\'">'+
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
}'''
NEW = '''function openLibModal(){
  var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">';
  for (var i=0;i<SUB_LIBRARIES.length;i++){
    var lib = SUB_LIBRARIES[i];
    html += '<div class="libcard" data-lid="'+lib.id+'" style="cursor:pointer;border:2px solid '+lib.color+';border-radius:12px;padding:14px;background:#f8fafc;transition:all .2s">'+
      '<div style="font-size:14px;font-weight:800;color:'+lib.color+'">📚 '+lib.name+'</div>'+
      '<div style="font-size:11px;color:#64748b;font-family:monospace;margin:5px 0">'+lib.path+'</div>'+
      '<div style="font-size:12px;color:#475569">'+lib.desc+'</div>'+
      '<div style="margin-top:8px;font-size:11px;color:'+lib.color+';font-weight:700">👉 点我调取历史案例</div>'+
    '</div>';
  }
  html += '</div>'+
    '<div style="margin-top:14px;padding:10px;background:#fef3c7;border-radius:8px;font-size:12px;color:#92400e">⚡ 一人公司大脑：每个子库都是 Agent 的"历史记忆"，接单时直接调取，不需要翻聊天记录。</div>';
  showModal('📚 5 大子库 · 一键调取历史（龙虾分身永久复盘）', html, [{label:'✕ 关闭', action:closeModal}]);
  var m = document.getElementById('aLibModal');
  if (m) {
    var cards = m.querySelectorAll('.libcard');
    for (var j=0;j<cards.length;j++){
      cards[j].addEventListener('click', (function(lid){ return function(){ recallFromLib(lid); }; })(cards[j].getAttribute('data-lid')));
      cards[j].addEventListener('mouseover', function(){ this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(0,0,0,.12)'; });
      cards[j].addEventListener('mouseout',  function(){ this.style.transform=''; this.style.boxShadow=''; });
    }
  }
}'''
assert OLD in txt, f'OLD not found'
txt = txt.replace(OLD, NEW, 1)
fp.write_text(txt, encoding='utf-8')
print('✅ openLibModal 重写完成，再校验 JS 语法')

# 再校验
import subprocess, tempfile, os
m = re.search(r'<script>([\s\S]*?)</script>', txt)
js = m.group(1)
tmp = r'C:\Users\Administrator\AppData\Local\Temp\jstest.js'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(js)
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
if r.returncode == 0:
    print('✅ JS 语法 OK')
else:
    print('❌ JS 语法错误:', r.stderr[:300])
