#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSS文件列表HTML生成工具
功能：调用ossutil获取阿里云OSS桶内文件/文件夹信息，生成带可视化界面的静态HTML文件
核心特性：支持网格/列表视图、目录导航、搜索、下载跳转（./gen.html?path=文件路径）
"""
import subprocess
import re
import html
import json
from datetime import datetime

# -------------------------- 配置项 --------------------------
OSS_BUCKET = "oss://lc3124-web-disk/"  # OSS桶地址
OUTPUT_HTML = "index.html"             # 生成的HTML文件名
OSS_PUBLIC_URL = "https://lc3124-web-disk.oss-cn-beijing.aliyuncs.com/"  # OSS公网访问地址
# ------------------------------------------------------------

def format_file_size(size_bytes):
    """
    将字节数格式化为易读的文件大小
    :param size_bytes: 字节数
    :return: 格式化后的大小字符串（如 1.50 MB）
    """
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_file_icon(file_name):
    """
    根据文件后缀返回对应的emoji图标
    :param file_name: 文件名
    :return: 对应类型的emoji图标
    """
    ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
    
    # 文档类
    if ext in ['txt', 'md', 'doc', 'docx', 'pdf', 'ppt', 'pptx', 'xls', 'xlsx', 'log', 'cue', 'm3u', 'm3u8']:
        return '📄' if ext in ['txt', 'md', 'log', 'cue', 'm3u', 'm3u8'] else '📃' if ext == 'pdf' else '📊'
    # 图片类
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'tif', 'tiff']:
        return '🖼️'
    # 音频类
    elif ext in ['mp3', 'wav', 'flac', 'm4a', 'ogg', 'ape', 'wma']:
        return '🎵'
    # 视频类
    elif ext in ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm']:
        return '🎬'
    # 压缩包
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz']:
        return '🗜️'
    # 代码类
    elif ext in ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'sh', 'bat']:
        return '💻'
    # 可执行文件
    elif ext in ['exe', 'msi', 'deb', 'rpm']:
        return '⚙️'
    # 其他类型
    else:
        return '📎'

def parse_oss_output(output):
    """
    解析ossutil ls命令的输出内容，提取文件/文件夹信息（仅保留纯路径，剔除OSS域名）
    :param output: ossutil命令的输出文本
    :return: 包含文件/文件夹信息的列表
    """
    files_info = []
    # 正则匹配ossutil输出格式：时间 +0800 CST  大小  存储类型  ETAG  路径
    pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \+0800 CST\s+(\d+)\s+(\w+)\s+([\w-]+)\s+oss://lc3124-web-disk/(.*)$",
        re.MULTILINE
    )
    
    for line in output.split("\n"):
        line = line.strip()
        # 跳过空行和统计行
        if not line or "Object Number is:" in line:
            continue
        
        match = pattern.match(line)
        if match:
            modify_time = match.group(1)
            file_size = int(match.group(2))
            file_path = match.group(5)  # 直接获取纯路径，无OSS域名/桶前缀
            
            # 格式化修改时间
            dt = datetime.strptime(modify_time, "%Y-%m-%d %H:%M:%S")
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")

            # 区分文件夹和文件：路径以/结尾且大小为0则为文件夹
            if file_size == 0 and file_path.endswith('/'):
                files_info.append({
                    "type": "dir",
                    "path": file_path,
                    "name": file_path.rstrip('/').split('/')[-1],
                    "size": 0,
                    "size_str": "文件夹",
                    "modify_time": formatted_time
                })
            # 普通文件：仅保留纯路径，用于后续跳转
            else:
                files_info.append({
                    "type": "file",
                    "path": file_path,  # 纯路径，如：管理员用户文件夹/head.png
                    "name": file_path.split('/')[-1],
                    "size": file_size,
                    "size_str": format_file_size(file_size),
                    "modify_time": formatted_time
                })

    return files_info

def generate_html(files_info):
    """
    根据解析的文件信息生成完整的HTML页面（下载跳转：./gen.html?path=文件纯路径）
    :param files_info: 解析后的文件/文件夹信息列表
    :return: 完整的HTML文本内容
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files_json = json.dumps(files_info, ensure_ascii=False)
    head_img_url = "head.png"  # 直接使用纯路径
    
    html_content = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lc3124的文件库</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
        }}

        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-quaternary: #30363d;
            --accent-primary: #58a6ff;
            --accent-secondary: #79c0ff;
            --accent-gold: #d4a574;
            --accent-light: #c9d1d9;
            --text-primary: #f0f6fc;
            --text-secondary: #c9d1d9;
            --text-tertiary: #8b949e;
            --shadow-light: 0 3px 12px rgba(88, 166, 255, 0.08);
            --shadow-medium: 0 6px 20px rgba(88, 166, 255, 0.12);
            --shadow-heavy: 0 12px 48px rgba(0, 0, 0, 0.3);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}

        body {{
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1c2128 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 1rem;
            line-height: 1.6;
            position: relative;
            overflow-x: hidden;
        }}

        body::before {{
            content: '';
            position: fixed;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 50% 50%, rgba(88, 166, 255, 0.02) 0%, transparent 70%);
            pointer-events: none;
            animation: floatGradient 25s ease-in-out infinite;
            z-index: 0;
        }}

        @keyframes floatGradient {{
            0%, 100% {{ transform: translate(0, 0); }}
            50% {{ transform: translate(40px, 40px); }}
        }}

        .container {{
            max-width: 1120px;
            margin: 0 auto;
            padding: 0;
            position: relative;
            z-index: 1;
        }}

        header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2.5rem 2rem;
            border-radius: var(--radius-lg);
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(33, 38, 45, 0.7) 100%);
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 2px rgba(88, 166, 255, 0.08);
            border: 1px solid rgba(88, 166, 255, 0.15);
            position: relative;
            overflow: hidden;
        }}

        header::before {{
            content: '';
            position: absolute;
            top: -100%;
            right: -100%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(88, 166, 255, 0.08) 0%, transparent 70%);
            animation: headerFloat 8s ease-in-out infinite;
        }}

        @keyframes headerFloat {{
            0%, 100% {{ transform: translate(0, 0); }}
            50% {{ transform: translate(50px, 50px); }}
        }}

        header > * {{
            position: relative;
            z-index: 2;
        }}

        header h1 {{
            background: linear-gradient(135deg, #58a6ff 0%, #79c0ff 50%, #b692f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.2rem;
            margin-bottom: 0.6rem;
            letter-spacing: -0.5px;
            font-weight: 700;
        }}

        header .subtitle {{
            color: var(--text-secondary);
            font-size: 1.05rem;
            margin-bottom: 1.8rem;
            font-weight: 400;
            letter-spacing: 0.3px;
        }}

        .header-controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: center;
            align-items: center;
            max-width: 580px;
            margin: 0 auto;
        }}

        .search-box {{
            flex: 1;
            min-width: 240px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            padding: 12px 18px;
            border: 2px solid rgba(88, 166, 255, 0.25);
            border-radius: 50px;
            background: rgba(33, 38, 45, 0.6);
            color: var(--text-primary);
            font-size: 0.95rem;
            transition: var(--transition);
            outline: none;
            backdrop-filter: blur(10px);
        }}

        .search-box input:focus {{
            border-color: var(--accent-primary);
            background: rgba(33, 38, 45, 0.9);
            box-shadow: 0 0 0 4px rgba(88, 166, 255, 0.15), 0 8px 16px rgba(88, 166, 255, 0.15);
            transform: translateY(-2px);
        }}

        .search-box input::placeholder {{
            color: var(--text-tertiary);
        }}

        .view-toggle {{
            display: flex;
            background: rgba(33, 38, 45, 0.6);
            border-radius: 50px;
            padding: 4px;
            border: 2px solid rgba(88, 166, 255, 0.25);
            backdrop-filter: blur(10px);
            gap: 2px;
        }}

        .view-btn {{
            padding: 8px 16px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .view-btn:hover {{
            color: var(--accent-primary);
            transform: translateY(-1px);
        }}

        .view-btn.active {{
            background: linear-gradient(135deg, #58a6ff, #79c0ff);
            color: #0d1117;
            box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3);
            font-weight: 600;
        }}

        .breadcrumb {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
            margin-bottom: 1.5rem;
            padding: 12px 16px;
            background: rgba(33, 38, 45, 0.6);
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            font-size: 0.9rem;
            border: 1px solid rgba(88, 166, 255, 0.15);
            backdrop-filter: blur(10px);
        }}

        .breadcrumb-item {{
            cursor: pointer;
            transition: var(--transition);
            padding: 4px 10px;
            border-radius: var(--radius-sm);
            font-weight: 500;
        }}

        .breadcrumb-item:hover {{
            color: var(--accent-primary);
            background: rgba(88, 166, 255, 0.1);
            transform: translateX(2px);
        }}

        .breadcrumb-item.active {{
            color: var(--accent-primary);
            font-weight: 600;
        }}

        .breadcrumb-separator {{
            color: var(--text-tertiary);
            opacity: 0.6;
        }}

        main {{
            background: rgba(22, 27, 34, 0.8);
            border-radius: var(--radius-lg);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), inset 0 1px 2px rgba(88, 166, 255, 0.08);
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(88, 166, 255, 0.12);
            min-height: 400px;
            backdrop-filter: blur(20px);
        }}

        .grid-view {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 1.2rem;
        }}

        .list-view {{
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }}

        .card {{
            background: linear-gradient(135deg, rgba(48, 54, 61, 0.6) 0%, rgba(33, 38, 45, 0.4) 100%);
            border-radius: var(--radius-md);
            padding: 1.3rem;
            transition: var(--transition);
            cursor: pointer;
            border: 1px solid rgba(88, 166, 255, 0.15);
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(88, 166, 255, 0.12), transparent);
            transition: left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
            pointer-events: none;
        }}

        .card:hover {{
            background: linear-gradient(135deg, rgba(58, 72, 90, 0.8) 0%, rgba(48, 54, 61, 0.6) 100%);
            transform: translateY(-4px);
            border-color: var(--accent-primary);
            box-shadow: 0 16px 32px rgba(88, 166, 255, 0.15), inset 0 1px 2px rgba(88, 166, 255, 0.08);
        }}

        .card:hover::before {{
            left: 100%;
        }}

        .list-view .card {{
            flex-direction: row;
            align-items: center;
            padding: 1rem 1.3rem;
            gap: 1.2rem;
        }}

        .list-view .card:hover {{
            transform: translateX(4px);
        }}

        .card-icon {{
            font-size: 2.4rem;
            text-align: center;
            position: relative;
            z-index: 1;
            filter: drop-shadow(0 2px 4px rgba(88, 166, 255, 0.1));
        }}

        .list-view .card-icon {{
            font-size: 1.6rem;
            min-width: 50px;
        }}

        .card-name {{
            font-size: 0.98rem;
            font-weight: 600;
            color: var(--text-primary);
            text-align: center;
            word-break: break-word;
            position: relative;
            z-index: 1;
        }}

        .list-view .card-name {{
            text-align: left;
            flex: 1;
            font-size: 0.95rem;
        }}

        .card-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-tertiary);
            margin-top: auto;
            position: relative;
            z-index: 1;
        }}

        .list-view .card-meta {{
            margin-top: 0;
            flex-direction: column;
            gap: 3px;
            min-width: 140px;
            text-align: right;
        }}

        .card-actions {{
            display: flex;
            gap: 8px;
            margin-top: 0.5rem;
            position: relative;
            z-index: 1;
        }}

        .list-view .card-actions {{
            margin-top: 0;
            min-width: 150px;
            gap: 10px;
        }}

        .card-actions .btn {{
            flex: 1;
            text-align: center;
            text-decoration: none;
        }}

        .btn {{
            padding: 8px 14px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 0.8rem;
            cursor: pointer;
            transition: var(--transition);
            font-weight: 500;
            display: inline-block;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, #58a6ff, #79c0ff);
            color: #0d1117;
            box-shadow: 0 4px 12px rgba(88, 166, 255, 0.25);
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(88, 166, 255, 0.35);
        }}

        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-secondary);
        }}

        .empty-state-icon {{
            font-size: 4rem;
            margin-bottom: 1.2rem;
            opacity: 0.4;
            animation: floatIcon 3s ease-in-out infinite;
        }}

        @keyframes floatIcon {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}

        .empty-state p {{
            font-size: 1rem;
        }}

        footer {{
            border-radius: var(--radius-lg);
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(33, 38, 45, 0.7) 100%);
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 2px rgba(88, 166, 255, 0.08);
            padding: 3rem 2rem;
            border: 1px solid rgba(88, 166, 255, 0.15);
        }}

        .footer-content {{
            max-width: 780px;
            margin: 0 auto;
            text-align: center;
        }}

        .author-section {{
            margin-bottom: 2.5rem;
        }}

        .author-avatar {{
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: linear-gradient(135deg, #58a6ff, #79c0ff);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.2rem;
            overflow: hidden;
            box-shadow: 0 12px 32px rgba(88, 166, 255, 0.3);
            border: 3px solid rgba(88, 166, 255, 0.3);
            animation: floatAvatar 3.5s cubic-bezier(0.45, 0, 0.55, 1) infinite;
        }}

        @keyframes floatAvatar {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}

        .author-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .author-name {{
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #58a6ff, #79c0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.6rem;
        }}

        .author-tagline {{
            color: var(--text-secondary);
            font-size: 1rem;
            margin-bottom: 1.8rem;
            font-style: italic;
            font-weight: 400;
        }}

        .author-links {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.9rem;
            margin-bottom: 2.5rem;
        }}

        .author-link {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 10px 18px;
            background: rgba(88, 166, 255, 0.08);
            border-radius: 50px;
            color: var(--text-secondary);
            text-decoration: none;
            transition: var(--transition);
            font-size: 0.85rem;
            border: 1.5px solid rgba(88, 166, 255, 0.25);
            font-weight: 500;
        }}

        .author-link:hover {{
            background: rgba(88, 166, 255, 0.15);
            color: var(--accent-primary);
            border-color: var(--accent-primary);
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(88, 166, 255, 0.2);
        }}

        .footer-info {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.9;
            padding-top: 2rem;
            border-top: 1px solid rgba(88, 166, 255, 0.12);
        }}

        .footer-info p {{
            margin-bottom: 0.8rem;
        }}

        .footer-info a {{
            color: var(--accent-gold);
            text-decoration: none;
            transition: var(--transition);
            font-weight: 500;
        }}

        .footer-info a:hover {{
            color: var(--accent-light);
            text-decoration: underline;
        }}

        .highlight {{
            color: var(--accent-gold);
            font-weight: 600;
        }}

        .footer-divider {{
            display: inline-block;
            color: var(--text-tertiary);
            margin: 0 0.8rem;
            opacity: 0.5;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 0;
            }}
            
            header {{
                padding: 1.8rem 1.2rem;
                margin-bottom: 1.5rem;
            }}
            
            header h1 {{
                font-size: 1.7rem;
            }}
            
            .header-controls {{
                flex-direction: column;
                gap: 0.8rem;
            }}
            
            .search-box {{
                width: 100%;
                min-width: auto;
            }}
            
            main {{
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            
            .grid-view {{
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 1rem;
            }}
            
            .card {{
                padding: 1rem;
            }}
            
            .card-icon {{
                font-size: 2rem;
            }}
            
            .card-name {{
                font-size: 0.88rem;
            }}
            
            .list-view .card {{
                flex-wrap: wrap;
                gap: 0.8rem;
                padding: 1rem;
            }}
            
            .list-view .card-icon {{
                min-width: auto;
                order: 0;
            }}
            
            .list-view .card-name {{
                width: 100%;
                order: 1;
                text-align: left;
            }}
            
            .list-view .card-meta {{
                min-width: auto;
                flex-direction: row;
                justify-content: space-between;
                width: 100%;
                order: 2;
                text-align: left;
            }}
            
            .list-view .card-actions {{
                width: 100%;
                order: 3;
                min-width: auto;
                margin-top: 0.6rem;
            }}
            
            .author-links {{
                flex-direction: column;
                align-items: center;
            }}
            
            .author-link {{
                width: 100%;
                max-width: 260px;
                justify-content: center;
            }}

            footer {{
                padding: 2rem 1.2rem;
            }}

            .footer-info {{
                font-size: 0.85rem;
            }}
        }}

        @media (max-width: 480px) {{
            header h1 {{
                font-size: 1.4rem;
            }}

            header .subtitle {{
                font-size: 0.95rem;
            }}
            
            .grid-view {{
                grid-template-columns: 1fr 1fr;
                gap: 0.8rem;
            }}

            .card {{
                padding: 0.9rem;
            }}

            .card-icon {{
                font-size: 1.8rem;
            }}

            .card-name {{
                font-size: 0.8rem;
            }}

            .card-meta {{
                font-size: 0.7rem;
            }}

            main {{
                padding: 1.2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>✨ Lc3124 的文件库</h1>
            <p class="subtitle">欢迎来到这里，随意看看吧</p>
            <p class="subtitle">目录分级跳转还没有修好，凑合着用用吧～</p>
            
            <div class="header-controls">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="🔍 搜索文件或文件夹...">
                </div>
                
                <div class="view-toggle">
                    <button class="view-btn active" id="gridViewBtn" title="网格视图">
                        <span>▦</span> 网格
                    </button>
                    <button class="view-btn" id="listViewBtn" title="列表视图">
                        <span>☰</span> 列表
                    </button>
                </div>
            </div>
        </header>

        <div class="breadcrumb" id="breadcrumb">
            <span class="breadcrumb-item active" data-path="">🏠 根目录</span>
        </div>

        <main>
            <div class="grid-view" id="contentGrid">
            </div>
            
            <div class="empty-state" id="emptyState" style="display: none;">
                <div class="empty-state-icon">📭</div>
                <p>什么都没有找到呢...</p>
            </div>
        </main>

        <footer>
            <div class="footer-content">
                <div class="author-section">
                    <div class="author-avatar">
                        <img src="{head_img_url}" alt="头像" onerror="this.style.display='none'">
                    </div>
                    <div class="author-name">Lc3124</div>
                    <div class="author-tagline">诶，你好哇 >w< !!</div>
                    
                    <div class="author-links">
                        <a href="mailto:lc3124@aliyun.com" class="author-link">
                            ✉️ 联系邮箱
                        </a>
                        <a href="https://github.com/lc-3124" target="_blank" class="author-link">
                            💻 GitHub
                        </a>
                        <a href="tencent://message/?uin=3418746552" class="author-link">
                            💝 赞助
                        </a>
                        <a href="https://lc3124.discourse.group" target="_blank" class="author-link">
                            💬 留言交流板
                        </a>
                    </div>
                </div>
                
                <div class="footer-info">
                    <p>
                        <span class="highlight">Index</span> 由脚本自动生成 ~ 
                        <a href="mailto:lc3124@aliyun.com">联系方式：lc3124@aliyun.com</a>
                    </p>
                    <p>
                        可以联系我来托管文件
                        <span class="footer-divider">|</span>
                        本页由 <span class="highlight">Cloudflare</span> 托管
                        <span class="footer-divider">|</span>
                        文件由 <span class="highlight">阿里云 OSS</span> 存储和分发
                    </p>
                    <p style="margin-top: 1rem; font-style: italic;">
                        📝 这是 Lc 和朋友萌分享和存储文件的地方，请不要到处传播哦～
                    </p>
                    <p style="margin-top: 0.8rem;">
                        🚨 <span class="highlight">请不要无意义大量下载文件</span>，OSS 服务很贵的 qwq，压岁钱经不起下载😭
                    </p>
                    <p style="margin-top: 1.2rem; color: var(--text-tertiary); font-size: 0.8rem;">
                        最后更新: <span class="highlight">{now}</span>
                    </p>
                </div>
            </div>
        </footer>
    </div>

    <script>
        const allFiles = {files_json};
        let currentPath = '';
        let searchQuery = '';
        let currentView = localStorage.getItem('viewMode') || 'grid';
        
        document.addEventListener('DOMContentLoaded', function() {{
            initViewToggle();
            renderContent();
            document.getElementById('searchInput').addEventListener('input', function(e) {{
                searchQuery = e.target.value.toLowerCase().trim();
                renderContent();
            }});
        }});
        
        function initViewToggle() {{
            const gridBtn = document.getElementById('gridViewBtn');
            const listBtn = document.getElementById('listViewBtn');
            const grid = document.getElementById('contentGrid');
            
            function setView(view) {{
                currentView = view;
                localStorage.setItem('viewMode', view);
                
                if (view === 'grid') {{
                    gridBtn.classList.add('active');
                    listBtn.classList.remove('active');
                    grid.className = 'grid-view';
                }} else {{
                    listBtn.classList.add('active');
                    gridBtn.classList.remove('active');
                    grid.className = 'list-view';
                }}
            }}
            
            gridBtn.addEventListener('click', () => setView('grid'));
            listBtn.addEventListener('click', () => setView('list'));
            
            setView(currentView);
        }}
        
        function getCurrentItems() {{
            const items = {{}};
            
            allFiles.forEach(file => {{
                const filePath = file.path;
                
                // 搜索逻辑：匹配全路径
                if (searchQuery && !filePath.toLowerCase().includes(searchQuery)) {{
                    return;
                }}
                
                // 搜索模式下直接显示所有匹配的文件/文件夹
                if (searchQuery) {{
                    items[filePath] = file;
                    return;
                }}
                
                // 非搜索模式：过滤当前目录下的直接内容
                if (!filePath.startsWith(currentPath)) {{
                    return;
                }}
                
                const relativePath = filePath.slice(currentPath.length);
                const parts = relativePath.split('/').filter(p => p);
                
                if (parts.length === 0) {{
                    return;
                }}
                
                const itemName = parts[0];
                
                // 当前目录下的直接文件/文件夹
                if (parts.length === 1) {{
                    items[itemName] = file;
                }} else {{
                    // 子目录，生成文件夹条目（避免重复）
                    if (!items[itemName]) {{
                        items[itemName] = {{
                            type: 'dir',
                            name: itemName,
                            path: currentPath + itemName + '/'
                        }};
                    }}
                }}
            }});
            
            // 排序：文件夹在前，中文按拼音升序
            return Object.values(items).sort((a, b) => {{
                if (a.type !== b.type) {{
                    return a.type === 'dir' ? -1 : 1;
                }}
                return a.name.localeCompare(b.name, 'zh-CN');
            }});
        }}
        
        function renderContent() {{
            const grid = document.getElementById('contentGrid');
            const emptyState = document.getElementById('emptyState');
            const items = getCurrentItems();
            
            grid.innerHTML = '';
            
            if (items.length === 0) {{
                emptyState.style.display = 'block';
                return;
            }}
            
            emptyState.style.display = 'none';
            
            items.forEach(item => {{
                const card = document.createElement('div');
                card.className = 'card';
                
                if (item.type === 'dir') {{
                    // 文件夹：仅显示图标、名称、元信息，无操作按钮
                    card.innerHTML = `
                        <div class="card-icon">📁</div>
                        <div class="card-name">${{escapeHtml(item.name)}}</div>
                        <div class="card-meta">
                            <span>${{item.size_str || '文件夹'}}</span>
                            <span>${{item.modify_time || ''}}</span>
                        </div>
                    `;
                    card.addEventListener('click', () => {{
                        if (!searchQuery) {{
                            navigateTo(item.path);
                        }}
                    }});
                }} else {{
                    // 文件：显示图标、名称、元信息，添加【去下载】按钮，跳转至./gen.html?path=纯路径
                    const icon = getFileIcon(item.path);
                    card.innerHTML = `
                        <div class="card-icon">${{icon}}</div>
                        <div class="card-name">${{escapeHtml(item.name || item.path.split('/').pop())}}</div>
                        <div class="card-meta">
                            <span>${{item.size_str}}</span>
                            <span>${{item.modify_time}}</span>
                        </div>
                        <div class="card-actions">
                            <a href="./gen.html?path=${{encodeURIComponent(item.path)}}" class="btn btn-primary" target="_self">去下载</a>
                        </div>
                    `;
                    // 阻止文件卡片点击的默认行为，仅按钮可跳转
                    card.addEventListener('click', (e) => {{
                        if (e.target.tagName !== 'A') e.preventDefault();
                    }});
                }}
                
                grid.appendChild(card);
            }});
            
            renderBreadcrumb();
        }}
        
        function navigateTo(path) {{
            currentPath = path;
            renderContent();
        }}
        
        function goToPath(path) {{
            currentPath = path;
            renderContent();
        }}
        
        function renderBreadcrumb() {{
            const breadcrumb = document.getElementById('breadcrumb');
            breadcrumb.innerHTML = '';
            
            if (searchQuery) {{
                const item = document.createElement('span');
                item.className = 'breadcrumb-item active';
                item.textContent = `🔍 搜索: "${{searchQuery}}"`;
                breadcrumb.appendChild(item);
                
                const clearBtn = document.createElement('span');
                clearBtn.className = 'breadcrumb-item';
                clearBtn.textContent = '✕ 清除搜索';
                clearBtn.style.marginLeft = 'auto';
                clearBtn.addEventListener('click', () => {{
                    searchQuery = '';
                    document.getElementById('searchInput').value = '';
                    renderContent();
                }});
                breadcrumb.appendChild(clearBtn);
                return;
            }}
            
            const parts = currentPath.split('/').filter(p => p);
            
            // 根目录
            const rootItem = document.createElement('span');
            rootItem.className = 'breadcrumb-item' + (parts.length === 0 ? ' active' : '');
            rootItem.textContent = '🏠 根目录';
            if (parts.length > 0) {{
                rootItem.addEventListener('click', () => goToPath(''));
            }}
            breadcrumb.appendChild(rootItem);
            
            // 多级目录
            let pathSoFar = '';
            parts.forEach((part, index) => {{
                pathSoFar += part + '/';
                
                const separator = document.createElement('span');
                separator.className = 'breadcrumb-separator';
                separator.textContent = '/';
                breadcrumb.appendChild(separator);
                
                const item = document.createElement('span');
                item.className = 'breadcrumb-item' + (index === parts.length - 1 ? ' active' : '');
                item.textContent = part;
                
                if (index < parts.length - 1) {{
                    item.addEventListener('click', () => goToPath(pathSoFar));
                }}
                
                breadcrumb.appendChild(item);
            }});
        }}
        
        function getFileIcon(fileName) {{
            const ext = fileName.toLowerCase().split('.').pop() || '';
            if (['txt', 'md', 'doc', 'docx', 'pdf', 'ppt', 'pptx', 'xls', 'xlsx', 'log', 'cue', 'm3u', 'm3u8'].includes(ext)) {{
                if (['txt', 'md', 'log', 'cue', 'm3u', 'm3u8'].includes(ext)) return '📄';
                if (ext === 'pdf') return '📃';
                return '📊';
            }}
            if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'tif', 'tiff'].includes(ext)) return '🖼️';
            if (['mp3', 'wav', 'flac', 'm4a', 'ogg', 'ape', 'wma'].includes(ext)) return '🎵';
            if (['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'].includes(ext)) return '🎬';
            if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'].includes(ext)) return '🗜️';
            if (['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'sh', 'bat'].includes(ext)) return '💻';
            if (['exe', 'msi', 'deb', 'rpm'].includes(ext)) return '⚙️';
            return '📎';
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
    </script>
</body>
</html>
'''
    return html_content

def main():
    """主函数：执行OSS列表获取、解析、HTML生成"""
    # 调用ossutil获取文件列表
    print("正在获取OSS文件列表...")
    r = subprocess.run(
        ["ossutil", "ls", OSS_BUCKET],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    
    # 检查命令执行结果
    if r.returncode != 0:
        print(f"OSS命令执行失败: {r.stderr.strip() or '未知错误'}")
        return
    
    # 解析输出内容（仅保留纯路径）
    files = parse_oss_output(r.stdout)
    if not files:
        print("未解析到任何文件/文件夹")
        return
    
    # 生成HTML文件
    print(f"成功解析 {len(files)} 个文件/文件夹")
    html_content = generate_html(files)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML文件生成完成：{OUTPUT_HTML}")

if __name__ == "__main__":
    main()

