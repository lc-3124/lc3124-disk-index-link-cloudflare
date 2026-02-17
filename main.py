#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import re
import html
from datetime import datetime

# -------------------------- 配置项 --------------------------
OSS_BUCKET = "oss://lc3124-web-disk/"
OUTPUT_HTML = "index.html"
OSS_PUBLIC_URL = "https://lc3124-web-disk.oss-cn-beijing.aliyuncs.com/"
# ------------------------------------------------------------

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def parse_oss_output(output):
    files_info = []
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) .*? (\d+) .*? oss://lc3124-web-disk/(.*)"
    for line in output.split("\n"):
        line = line.strip()
        if not line or "Object Number is:" in line:
            continue
        match = re.match(pattern, line)
        if match:
            modify_time = match.group(1)
            file_size = int(match.group(2))
            file_path = match.group(3)
            try:
                dt = datetime.strptime(modify_time, "%Y-%m-%d %H:%M:%S")
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = modify_time

            download_url = f"{OSS_PUBLIC_URL}{html.escape(file_path)}"
            files_info.append({
                "path": file_path,
                "size": file_size,
                "size_str": format_file_size(file_size),
                "modify_time": formatted_time,
                "download_url": download_url
            })
    return files_info

def build_directory_tree(files_info):
    root = {"type": "dir", "name": "lc3124-web-disk", "children": {}}
    for file_info in files_info:
        path_parts = file_info["path"].split("/")
        current = root
        for i, part in enumerate(path_parts):
            if not part:
                continue
            if i == len(path_parts) - 1:
                current["children"][part] = {
                    "type": "file",
                    "name": part,
                    "size_str": file_info["size_str"],
                    "modify_time": file_info["modify_time"],
                    "download_url": file_info["download_url"]
                }
            else:
                if part not in current["children"]:
                    current["children"][part] = {"type": "dir", "name": part, "children": {}}
                current = current["children"][part]
    return root

def generate_html_tree(node, level=0):
    html_parts = []
    indent = level * 22
    if node["type"] == "dir":
        dir_name = html.escape(node["name"])
        html_parts.append(f'''
        <div class="directory" style="margin-left:{indent}px">
            <div class="dir-header">
                <span class="icon folder-icon">📁</span>
                <span class="name">{dir_name}</span>
                <button class="btn dl-folder-btn" onclick="downloadFolder(this)">下载文件夹(开发中)</button>
            </div>
            <div class="dir-children" style="display:none">
        ''')
        for child in sorted(node["children"].values(), key=lambda x: (x["type"], x["name"])):
            html_parts.append(generate_html_tree(child, level + 1))
        html_parts.append('</div></div>')
    else:
        name = html.escape(node["name"])
        size = html.escape(node["size_str"])
        mtime = html.escape(node["modify_time"])
        url = node["download_url"]
        html_parts.append(f'''
        <div class="file" style="margin-left:{indent}px">
            <span class="icon file-icon">📄</span>
            <span class="name" title="{name}">{name}</span>
            <span class="meta">{size} · {mtime}</span>
            <div class="btn-group">
                <a href="{url}" target="_blank" class="btn preview-btn">预览</a>
                <a href="{url}" download class="btn download-btn">下载</a>
            </div>
        </div>
        ''')
    return "".join(html_parts)

def generate_html(root_node):
    tree_html = generate_html_tree(root_node)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lc3124的文件库</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,Microsoft YaHei,sans-serif}}
body{{
    background:linear-gradient(145deg,#0f172a 0%,#1e293b 50%,#0f172a 100%);
    color:#e2e8f0;
    padding:2rem;
    max-width:1400px;
    margin:0 auto;
    min-height:100vh
}}
.header{{
    text-align:center;
    margin-bottom:2rem;
    padding-bottom:1rem;
    border-bottom:2px solid #38bdf8
}}
.header h1{{
    color:#38bdf8;
    font-size:2.2rem
}}
.header p{{
    color:#94a3b8;
    margin-top:8px
}}
.directory-tree{{
    background:#1e293b;
    border-radius:12px;
    box-shadow:0 0 30px rgba(56,189,248,0.15);
    padding:2.5rem;
    border:1px solid #334155;
    overflow-x:auto
}}
.directory{{margin:6px 0}}
.dir-header{{
    padding:10px 16px;
    border-radius:8px;
    background:#27374d;
    display:flex;
    align-items:center;
    gap:10px;
    cursor:pointer;
    transition:.2s
}}
.dir-header:hover{{
    background:#334155;
    border-left:3px solid #38bdf8
}}
.dir-header .name{{
    flex:1;
    font-weight:600;
    color:#38bdf8
}}
.file{{
    padding:9px 16px;
    border-radius:8px;
    background:#212f45;
    display:flex;
    align-items:center;
    gap:12px;
    margin:4px 0;
    transition:.2s
}}
.file:hover{{
    background:#27374d;
    border-left:3px solid #60a5fa
}}
.file .name{{
    flex:1;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis
}}
.meta{{
    color:#94a3b8;
    font-size:0.85rem;
    white-space:nowrap
}}
.icon{{width:24px;text-align:center}}
.folder-icon{{color:#fbbf24}}
.file-icon{{color:#60a5fa}}
.btn-group{{display:flex;gap:6px}}
.btn{{
    padding:4px 10px;
    border:none;
    border-radius:6px;
    font-size:0.85rem;
    cursor:pointer;
    text-decoration:none;
    transition:.2s
}}
.preview-btn{{
    background:#27374d;
    color:#93c5fd
}}
.download-btn,.dl-folder-btn{{
    background:#0369a1;
    color:#fff
}}
.btn:hover{{opacity:0.85}}
.footer{{
    margin-top:2.5rem;
    text-align:center;
    color:#94a3b8;
    padding-top:1rem;
    border-top:1px solid #334155
}}
</style>
</head>
<body>
<div class="header">
    <h1>Lc3124的文件库</h1>
    <p>文件目录 · 点击文件夹展开/折叠</p>
    <p>更新时间: {now}</p>
</div>
<div class="directory-tree">{tree_html}</div>
<div class="footer">
    <p>index由脚本生成～ 联系方式：lc3124@aliyun.com</p>
    <p>          可以联系我来托管文件</p>
    <p>本页由cloudflare托管，文件由aliyunOSS存储和分发</p>
    <p> PS:请不要无意义大量下载文件哦，OSS服务很贵的qwq</p>
</div>

<script>
// 文件夹展开/折叠
document.querySelectorAll('.dir-header').forEach(h => {{
    h.querySelector('.dl-folder-btn').onclick = e => e.stopPropagation()
    h.onclick = () => {{
        const c = h.nextElementSibling
        const icon = h.querySelector('.folder-icon')
        if(c.style.display === 'none'){{
            c.style.display = 'block'
            icon.textContent = '📂'
        }}else{{
            c.style.display = 'none'
            icon.textContent = '📁'
        }}
    }}
}})

// 文件夹批量下载（连续发起下载请求）
function downloadFolder(btn){{
    const dirEl = btn.closest('.directory')
    const files = dirEl.querySelectorAll('.file a[download]')
    files.forEach((a, i) => {{
        setTimeout(() => {{
            const link = document.createElement('a')
            link.href = a.href
            link.download = a.download
            link.style.display = 'none'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        }}, i * 120)
    }})
}}
</script>
</body>
</html>
'''

def main():
    try:
        print("获取文件列表...")
        r = subprocess.run(["ossutil", "ls", OSS_BUCKET], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print("ossutil 错误:", r.stderr)
            return
        files = parse_oss_output(r.stdout)
        tree = build_directory_tree(files)
        html = generate_html(tree)
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"生成完成: {OUTPUT_HTML}，共 {len(files)} 个文件")
    except Exception as e:
        print("错误:", e)

if __name__ == "__main__":
    main()

