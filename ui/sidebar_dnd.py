"""
侧边栏拖拽组件 — 使用 postMessage 通信的纯 HTML/JS 文件夹树
"""
import json as _json
import time as _time


def build_dnd_html(
    conversations: dict,
    folders: dict,
    active_conv_id: str,
    theme_colors: dict,
) -> str:
    """生成可拖拽的文件夹树 HTML"""

    t = theme_colors
    convs_json = _json.dumps(conversations, ensure_ascii=False)
    folders_json = _json.dumps(folders, ensure_ascii=False)

    return f"""<style>
.sb-tree * {{ box-sizing: border-box; margin: 0; padding: 0; }}
.sb-tree {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 0.8rem;
    color: {t['text_primary']};
    user-select: none;
    padding: 4px 0;
}}
.sb-folder-header {{
    display: flex; align-items: center; gap: 4px;
    padding: 5px 6px; border-radius: 8px; cursor: pointer;
    margin: 2px 0; font-weight: 600; font-size: 0.78rem;
    color: {t['text_secondary']};
}}
.sb-folder-header:hover {{ background: {t['bg_hover']}; }}
.sb-folder-body {{ padding-left: 12px; display: none; }}
.sb-folder-body.open {{ display: block; }}
.sb-conv-item {{
    display: flex; align-items: center; gap: 4px;
    padding: 4px 8px; border-radius: 8px; cursor: grab;
    margin: 1px 0; font-size: 0.77rem;
    transition: all 0.15s;
    color: {t['text_primary']};
}}
.sb-conv-item:hover {{ background: {t['bg_hover']}; }}
.sb-conv-item.active {{ background: {t['accent_blue']}22; font-weight: 600; }}
.sb-conv-item.dragging {{ opacity: 0.4; }}
.sb-folder-drop {{
    padding: 2px 6px; border-radius: 8px; margin: 1px 0;
    transition: all 0.15s; font-size: 0.78rem; color: {t['text_secondary']};
}}
.sb-folder-drop.drag-over {{
    background: {t['accent_blue']}22;
    outline: 2px dashed {t['accent_blue']}66;
}}
.sb-folder-drop.uncategorized {{
    font-style: italic;
}}
.sb-new-folder-btn {{
    background: {t['bg_hover']}; border: none; border-radius: 6px;
    color: {t['text_primary']}; cursor: pointer; font-size: 0.75rem;
    padding: 3px 8px; margin: 4px 0;
}}
.sb-new-folder-btn:hover {{ background: {t['accent_blue']}22; }}
.sb-toast {{
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    background: {t['accent_blue']}; color: #fff; padding: 8px 18px;
    border-radius: 20px; font-size: 0.82rem; z-index: 9999;
    opacity: 0; transition: opacity 0.3s;
    pointer-events: none;
}}
.sb-toast.show {{ opacity: 1; }}
</style>

<div class="sb-tree" id="sb-tree"></div>
<div class="sb-toast" id="sb-toast"></div>

<script>
(function() {{
var CONVS = {convs_json};
var FOLDERS = {folders_json};
var ACTIVE = '{active_conv_id}';
var MOVE_QUEUE = null;

function toast(msg) {{
    var t = document.getElementById('sb-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function() {{ t.classList.remove('show'); }}, 1800);
}}

function saveAction(action) {{
    // 通过 postMessage 发送给 Streamlit
    window.postMessage({{type: 'aero_dnd', action: action}}, '*');
}}

function render() {{
    var tree = document.getElementById('sb-tree');
    if (!tree) return;
    var html = '';

    // 文件夹树
    function renderFolder(parentId, depth) {{
        var items = [];
        for (var fid in FOLDERS) {{
            if ((FOLDERS[fid].parent_id||'') === parentId) items.push({{id: fid, data: FOLDERS[fid]}});
        }}
        items.sort(function(a,b) {{ return a.data.name.localeCompare(b.data.name); }});
        for (var i=0; i<items.length; i++) {{
            var f = items[i];
            var indent = '  '.repeat(depth);
            var convsInFolder = [];
            for (var cid in CONVS) {{
                if ((CONVS[cid].folder_id||'') === f.id)
                    convsInFolder.push({{id: cid, data: CONVS[cid]}});
            }}
            convsInFolder.sort(function(a,b) {{ return (b.data.created_at||'').localeCompare(a.data.created_at||''); }});
            html += '<div class="sb-folder-drop" data-fid="'+f.id+'" '
                  + 'ondragover="event.preventDefault();this.classList.add(\'drag-over\');" '
                  + 'ondragleave="this.classList.remove(\'drag-over\');" '
                  + 'ondrop="handleDrop(event, \''+f.id+'\');this.classList.remove(\'drag-over\');">';
            html += '<div class="sb-folder-header" onclick="var b=this.nextElementSibling;b.classList.toggle(\'open\');">'
                  + '📁 '+f.data.name+' ('+convsInFolder.length+')'
                  + '<span style="margin-left:auto;display:flex;align-items:center;gap:10px;">'
                  + '<span class="sb-del-folder" onclick="event.stopPropagation();if(confirm(\'删除文件夹「'+f.data.name+'\」？对话将移到未分类。\'))saveAction({{type:\'delete_folder\',folder_id:\''+f.id+'\'}});toast(\'已删除\');" title="删除文件夹" style="cursor:pointer;opacity:0.7;font-size:0.85rem;color:#e74c3c;">🗑</span>'
                  + '<span style="font-size:0.7rem;opacity:0.6;">▾</span></span></div>';
            html += '<div class="sb-folder-body">';
            for (var j=0; j<convsInFolder.length; j++) {{
                var c = convsInFolder[j];
                var title = c.data.title||'新对话';
                if (title.length > 16) title = title.substring(0,16)+'...';
                var activeCls = c.id === ACTIVE ? ' active' : '';
                html += '<div class="sb-conv-item'+activeCls+'" draggable="true" '
                      + 'data-cid="'+c.id+'" '
                      + 'ondragstart="handleDragStart(event, \''+c.id+'\');" '
                      + 'ondragend="handleDragEnd(event);" '
                      + 'onclick="handleConvClick(\''+c.id+'\');">'
                      + '💬 '+title+'</div>';
            }}
            html += '<button class="sb-new-folder-btn" onclick="saveAction({{type:\'new_subfolder\',parent:\''+f.id+'\'}});toast(\'新建子文件夹\');">+ 子文件夹</button>';
            html += '</div>';
            renderFolder(f.id, depth+1);
            html += '</div>';
        }}
    }}
    renderFolder('', 0);

    // 未分类
    var uncategorized = [];
    for (var cid in CONVS) {{
        if ((CONVS[cid].folder_id||'') === '')
            uncategorized.push({{id: cid, data: CONVS[cid]}});
    }}
    uncategorized.sort(function(a,b) {{ return (b.data.created_at||'').localeCompare(a.data.created_at||''); }});
    if (uncategorized.length > 0) {{
        html += '<div class="sb-folder-drop uncategorized" data-fid="" '
              + 'ondragover="event.preventDefault();this.classList.add(\'drag-over\');" '
              + 'ondragleave="this.classList.remove(\'drag-over\');" '
              + 'ondrop="handleDrop(event, \'\');this.classList.remove(\'drag-over\');">';
        html += '<div style="padding:4px 6px;font-weight:600;">💬 未分类 ('+uncategorized.length+')</div>';
        for (var k=0; k<uncategorized.length; k++) {{
            var uc = uncategorized[k];
            var title = uc.data.title||'新对话';
            if (title.length > 16) title = title.substring(0,16)+'...';
            var activeCls = uc.id === ACTIVE ? ' active' : '';
            html += '<div class="sb-conv-item'+activeCls+'" draggable="true" '
                  + 'data-cid="'+uc.id+'" '
                  + 'ondragstart="handleDragStart(event, \''+uc.id+'\');" '
                  + 'ondragend="handleDragEnd(event);" '
                  + 'onclick="handleConvClick(\''+uc.id+'\');">'
                  + '💬 '+title+'</div>';
        }}
        html += '</div>';
    }}

    tree.innerHTML = html;
}}

window.handleDragStart = function(e, cid) {{
    e.dataTransfer.setData('text/plain', cid);
    e.target.classList.add('dragging');
}};
window.handleDragEnd = function(e) {{
    e.target.classList.remove('dragging');
}};
window.handleDrop = function(e, folderId) {{
    var cid = e.dataTransfer.getData('text/plain');
    if (cid) {{
        saveAction({{type: 'move_conv', conv_id: cid, folder_id: folderId}});
        toast('已移动 → '+(folderId||'未分类'));
    }}
}};
window.handleConvClick = function(cid) {{
    saveAction({{type: 'switch_conv', conv_id: cid}});
    toast('切换对话...');
}};

// 新建文件夹（根目录）
window.createRootFolder = function() {{
    var name = prompt('文件夹名称：');
    if (name && name.trim()) {{
        saveAction({{type: 'new_folder', name: name.trim(), parent: ''}});
        toast('已创建 ' + name.trim());
    }}
}};

render();

// 监听 Streamlit rerun 后重新渲染（页面内容变化时）
var observer = new MutationObserver(function() {{ render(); }});
var sidebar = document.querySelector('section[data-testid="stSidebar"]');
if (sidebar) observer.observe(sidebar, {{ childList: true, subtree: true }});

}})();
</script>"""


def build_folder_actions_html(theme_colors: dict) -> str:
    """新建文件夹按钮"""
    t = theme_colors
    return f"""<style>
.sb-create-btn {{
    display: block; width: 100%; padding: 6px 10px;
    background: {t['bg_hover']}; border: none; border-radius: 8px;
    color: {t['text_primary']}; cursor: pointer; font-size: 0.8rem;
    font-weight: 500; margin-bottom: 6px; text-align: left;
}}
.sb-create-btn:hover {{ background: {t['accent_blue']}22; }}
</style>
<button class="sb-create-btn" onclick="
var name=prompt('文件夹名称：');
if(name&&name.trim()){{window.postMessage({{type:'aero_dnd',action:{{type:'new_folder',name:name.trim(),parent:''}}}},'*');}}
">📁 新建文件夹</button>"""
