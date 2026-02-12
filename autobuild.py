# autobuild.py

import os
import shutil
import glob
import hashlib
import json
from typing import List, Dict, Any, Set, Optional 
from collections import defaultdict
from datetime import datetime, timezone, timedelta 
import subprocess 
import shlex      

import config
from parser import get_metadata_and_content
import generator

# 尝试导入csscompressor，如果未安装则使用基础压缩
try:
    import csscompressor
    CSS_COMPRESSOR_AVAILABLE = True
except ImportError:
    CSS_COMPRESSOR_AVAILABLE = False
    print("Warning: csscompressor not installed, using basic compression")

# =========================================================================
# 【关键修复】将组合后的输出目录变量移到此处，以解决 config 模块属性缺失的问题
# =========================================================================
# 这些变量现在是 autobuild.py 模块的全局变量，确保可用
POSTS_OUTPUT_DIR = os.path.join(config.BUILD_DIR, config.POSTS_DIR_NAME)
TAGS_OUTPUT_DIR = os.path.join(config.BUILD_DIR, config.TAGS_DIR_NAME)
STATIC_OUTPUT_DIR = os.path.join(config.BUILD_DIR, config.STATIC_DIR)
# =========================================================================


# [恢复] 定义清单文件路径
MANIFEST_FILE = os.path.join(os.path.dirname(__file__), '.build_manifest.json')

# 定义 UTC+8 时区信息
TIMEZONE_OFFSET = timedelta(hours=8)
TIMEZONE_INFO = timezone(TIMEZONE_OFFSET)

# --- Manifest 辅助函数 (增量构建所需) ---
def load_manifest() -> Dict[str, Any]:
    """加载上一次的构建清单文件。"""
    try:
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_manifest(manifest: Dict[str, Any]):
    """保存当前的构建清单文件。"""
    try:
        with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"警告：无法写入构建清单文件 {MANIFEST_FILE}: {e}")

def get_full_content_hash(filepath: str) -> str:
    """计算文件的完整 SHA256 哈希值。用于 Manifest。"""
    h = hashlib.sha256()
    try:
        # 使用路径相对路径进行存储，但在计算哈希时使用绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, filepath)

        with open(full_path, 'rb') as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                h.update(chunk)
    except IOError:
        return ""
    return h.hexdigest()

# [新增] 辅助函数：计算文件哈希
def get_file_hash(filepath: str) -> Optional[str]:
    """计算文件的 SHA256 哈希值。"""
    try:
        # 获取脚本所在目录的绝对路径，用于构建文件的完整路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, filepath)

        if not os.path.exists(full_path):
            return None
            
        sha256 = hashlib.sha256()
        with open(full_path, 'rb') as f:
            # 分块读取文件以处理大文件
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()
    except Exception:
        return None


# 检查依赖 & Hash 文件 (保持不变)
try:
    # 尝试导入 Pygments 以确保代码高亮功能可用
    import pygments
except ImportError:
    pass

def hash_file(filepath: str) -> str:
    """计算文件的 SHA256 哈希值前 8 位。用于 CSS 文件名。"""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()[:8]
    except FileNotFoundError:
        return 'nohash'

# [修复后的 FUNCTION] 获取文件的最后修改时间 (Git -> Filesystem -> Fallback with Microseconds)
def format_file_mod_time(filepath: str) -> str:
    """
    获取文件的最后修改时间。
    优先级：1. Git Author Time -> 2. 文件系统修改时间 -> 3. 当前构建时间。
    并确保输出包含微秒以保证唯一性。
    """
    
    def format_dt(dt: datetime, source: str) -> str:
        # 确保 datetime 对象带有正确的时区信息
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            # ⭐ 关键修复 1: 将 Naive 对象（如 os.path.getmtime 的输出）视为 UTC，再转换为目标时区 UTC+8
            dt = dt.replace(tzinfo=timezone.utc).astimezone(TIMEZONE_INFO) 
        else:
            # 否则直接转换为 UTC+8
            dt = dt.astimezone(TIMEZONE_INFO)
            
        # [核心修复] 使用微秒 (%f) 格式化时间
        time_str = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # 移除末尾的零和点，使输出更简洁，但保留非零微秒
        time_str = time_str.rstrip('0').rstrip('.')
        
        return f"本文构建时间: {time_str} (UTC+8 - {source})"
    
    # --- 1. 尝试获取 Git 最后提交时间 (Author Time) ---
    try:
        git_command = ['git', 'log', '-1', '--pretty=format:%aI', '--', filepath]
        result = subprocess.run(git_command, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            git_time_str = result.stdout.strip()
            if git_time_str:
                try:
                    mtime_dt_tz = datetime.fromisoformat(git_time_str)
                except ValueError:
                    if git_time_str.endswith('Z'):
                        git_time_str = git_time_str.replace('Z', '+00:00')
                    mtime_dt_tz = datetime.fromisoformat(git_time_str)
                
                return format_dt(mtime_dt_tz, 'Git')

    except Exception as e:
        pass 
    
    # --- 2. 尝试获取文件系统修改时间 (次级回退) ---
    try:
        timestamp = os.path.getmtime(filepath)
        # ⭐ 关键修复 2: 明确将时间戳转换为 UTC time-zone aware 对象
        fs_mtime = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return format_dt(fs_mtime, 'Filesystem')
        
    except FileNotFoundError:
        pass

    except Exception as e:
        pass
        
    # --- 3. 最终回退：使用当前构建时间 ---
    now_utc = datetime.now(timezone.utc)
    return format_dt(now_utc, 'Fallback')


def compress_css_content(css_content):
    """
    基础CSS压缩函数，去除注释和多余空白
    """
    import re
    # 移除CSS注释
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # 移除多余的空白字符和换行符
    css_content = re.sub(r'\s+', ' ', css_content)
    
    # 移除选择器和属性之间的多余空格
    css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
    
    # 移除URL周围的空格
    css_content = re.sub(r'url\s*\(\s*', 'url(', css_content)
    css_content = re.sub(r'\s*\)', ')', css_content)
    
    # 移除十六进制颜色值中的多余零
    css_content = re.sub(r'#([a-fA-F0-9])\1([a-fA-F0-9])\2([a-fA-F0-9])\3', r'#\1\2\3', css_content)
    
    # 移除小数点前的零
    css_content = re.sub(r'(?<=[\s:])0+\.([0-9]+)', r'.\1', css_content)
    
    # 移除分号前的空格
    css_content = re.sub(r';}', '}', css_content)
    
    # 去除首尾空格
    css_content = css_content.strip()
    
    return css_content

def compress_css_file(input_path, output_path):
    """
    压缩CSS文件
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        if CSS_COMPRESSOR_AVAILABLE:
            compressed_css = csscompressor.compress(css_content)
        else:
            # 使用基础压缩作为回退
            compressed_css = compress_css_content(css_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(compressed_css)
        
        # 计算压缩率
        original_size = len(css_content.encode('utf-8'))
        compressed_size = len(compressed_css.encode('utf-8'))
        compression_rate = (original_size - compressed_size) / original_size * 100
        
        print(f"   -> CSS compressed: {original_size / 1024:.2f}KB -> {compressed_size / 1024:.2f}KB ({compression_rate:.1f}% reduction)")
        
        return True
    except Exception as e:
        print(f"   -> CSS compression failed: {e}")
        return False

# 检查文章是否应被隐藏
def is_post_hidden(post: Dict[str, Any]) -> bool:
    """检查文章是否应被隐藏。"""
    return post.get('status', 'published').lower() == 'draft' or post.get('hidden') is True

def build_site():
    print("\n" + "="*40)
    print("   🚀 STARTING BUILD PROCESS (Incremental Build Enabled)")
    print("="*40 + "\n")
    
    # ------------------------------------------------------------------------- 
    # [1/5] 准备工作 & 增量构建初始化 (启用增量构建)
    # -------------------------------------------------------------------------
    print("[1/5] Preparing build directory and loading manifest...")
    
    # [关键修复: 移除 shutil.rmtree] 确保目录存在，不清理，从而保留上次的构建文件
    os.makedirs(config.BUILD_DIR, exist_ok=True) 
    # !!! 引用当前文件顶层定义的变量，修复 AttributeError !!!
    os.makedirs(POSTS_OUTPUT_DIR, exist_ok=True) 
    os.makedirs(TAGS_OUTPUT_DIR, exist_ok=True)
    os.makedirs(STATIC_OUTPUT_DIR, exist_ok=True)
    
    # 加载上次的构建清单
    old_manifest = load_manifest()
    new_manifest = {
        'posts': {}, 
        'static_files': {},
        'templates': {} # 模板和核心依赖项都存储在这里
    }
    
    # 存储需要重新生成 HTML 的文章对象
    posts_to_build: List[Dict[str, Any]] = [] 
    # 标志位：文章集合信息是否变化 (影响列表页、RSS、Sitemap)
    posts_data_changed = False      
    # ⭐ 新增标志位：主题或模板文件是否变化
    theme_changed = False

    # -------------------------------------------------------------------------
    # [2/5] 资源处理 & 主题/模板变动检查 (新增)
    # -------------------------------------------------------------------------
    print("\n[2/5] Processing Assets and Checking Theme Changes...")
    assets_dir = os.path.join(config.BUILD_DIR, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # 复制静态文件 (使用顶部定义的 STATIC_OUTPUT_DIR)
    if os.path.exists(config.STATIC_DIR):
        shutil.copytree(config.STATIC_DIR, STATIC_OUTPUT_DIR, dirs_exist_ok=True)

    # -----------------------------------------------------------
    # ⭐ 修复: 检查 CSS 文件变动，并设置 theme_changed
    # -----------------------------------------------------------
    css_source = 'assets/style.css'
    if os.path.exists(css_source):
        css_hash = hash_file(css_source)
        new_css = f"style.{css_hash}.css"
        config.CSS_FILENAME = new_css
        
        # 使用压缩版本
        compressed_css_path = os.path.join(assets_dir, new_css)
        success = compress_css_file(css_source, compressed_css_path)
        
        if not success:
            # 如果压缩失败，回退到普通复制
            shutil.copy2(css_source, compressed_css_path)

        # 检查CSS文件内容是否变动 (使用 get_full_content_hash)
        current_css_content_hash = get_full_content_hash(css_source)
        old_css_content_hash = old_manifest.get('static_files', {}).get(css_source)

        if current_css_content_hash != old_css_content_hash:
            theme_changed = True
            print(f"   -> [CHANGE DETECTED] {css_source} content has changed. (Theme Change)")
        
        new_manifest.setdefault('static_files', {})[css_source] = current_css_content_hash
    else:
        config.CSS_FILENAME = 'style.css'

    # -----------------------------------------------------------
    # ⭐ 修复: 检查 base.html 模板文件变动，并设置 theme_changed
    # -----------------------------------------------------------
    base_template_source = os.path.join('templates', 'base.html')
    if os.path.exists(base_template_source):
        current_template_hash = get_full_content_hash(base_template_source)
        old_template_hash = old_manifest.get('templates', {}).get(base_template_source)

        if current_template_hash != old_template_hash:
            theme_changed = True
            print(f"   -> [CHANGE DETECTED] {base_template_source} has changed. (Theme Change)")
        
        new_manifest.setdefault('templates', {})[base_template_source] = current_template_hash
    # -----------------------------------------------------------
    
    # =========================================================================
    # ⭐ 核心修复: 检查所有核心 Python 文件和模板文件变动 (解决您的根本问题)
    # 这一部分是解决问题的关键，确保构建逻辑更改时强制重建
    # =========================================================================
    CORE_DEPENDENCIES = [
        'autobuild.py', 
        'parser.py', 
        'generator.py', 
        'config.py',
        # 重要的模板文件
        os.path.join('templates', 'post.html'),
        os.path.join('templates', 'list.html'),
        os.path.join('templates', 'archive.html'),
        os.path.join('templates', 'tags_list.html'),
    ]

    for core_file in CORE_DEPENDENCIES:
        if os.path.exists(core_file):
            current_core_hash = get_full_content_hash(core_file)
            # 使用 'templates' 键来存储所有非文章/非静态资源的依赖项哈希
            old_core_hash = old_manifest.get('templates', {}).get(core_file)
            
            if current_core_hash != old_core_hash:
                theme_changed = True
                print(f"   -> [CHANGE DETECTED] Core dependency {core_file} has changed. (Theme/Logic Change)")
                
            new_manifest.setdefault('templates', {})[core_file] = current_core_hash
            
    # =========================================================================

    # =========================================================================
    # ⭐ 新增: 复制 CNAME 文件到 _site 部署目录 (解决自定义域名问题)
    # =========================================================================
    cname_path_source = os.path.join(os.path.dirname(__file__), 'CNAME')
    cname_path_dest = os.path.join(config.BUILD_DIR, 'CNAME')

    if os.path.exists(cname_path_source):
        print("   -> Copying CNAME file...")
        shutil.copyfile(cname_path_source, cname_path_dest)
    else:
        print("   -> WARNING: CNAME file not found. Custom domain might fail (404).")
    # =========================================================================

    # -------------------------------------------------------------------------
    # [3/5] 解析 Markdown (增量构建核心)
    # -------------------------------------------------------------------------
    print("\n[3/5] Parsing Markdown Files...")
    
    md_files = glob.glob(os.path.join(config.MARKDOWN_DIR, '*.md'))
    if not md_files: md_files = glob.glob('*.md')
    
    parsed_posts = []
    tag_map = defaultdict(list)
    source_md_paths: Set[str] = set()

    for md_file in md_files:
        relative_path = os.path.relpath(md_file, os.path.dirname(__file__)).replace('\\', '/')
        source_md_paths.add(relative_path)
        
        # [增量逻辑] 检查内容哈希
        current_hash = get_full_content_hash(md_file)
        old_item = old_manifest.get('posts', {}).get(relative_path, {})
        old_hash = old_item.get('hash')

        needs_full_build = (current_hash != old_hash) or ('link' not in old_item)
        needs_rebuild_html = needs_full_build or theme_changed # <-- 使用 theme_changed 来控制 HTML 重建

        if needs_full_build:
            # 只有内容变更时才打印此信息
            if current_hash != old_hash:
                 print(f"   -> [CONTENT CHANGED] {os.path.basename(md_file)}")
            # 否则，如果是新增文件或缺失链接信息，下面会单独打印
        elif theme_changed: # 只有主题变动时，才打印这条，否则上面的 needs_full_build 已经打印
            print(f"   -> [REBUILD HTML] {os.path.basename(md_file)} (Theme changed)")
        else:
            print(f"   -> [SKIPPED HTML] {os.path.basename(md_file)}")
            
        # 解析内容 (即使跳过 HTML，也要解析元数据来构建列表页)
        metadata, content_md, content_html, toc_html = get_metadata_and_content(md_file)
        
        mod_time_cn = format_file_mod_time(md_file) # 使用修复后的时间获取逻辑

        # 自动补全 slug 和特殊页面处理 (保持不变)
        if 'slug' not in metadata:
            filename_slug = os.path.splitext(os.path.basename(md_file))[0]
            metadata['slug'] = filename_slug

        slug = str(metadata['slug']).lower()
        file_name = os.path.basename(md_file)
        
        # --- 特殊页面处理 (404 / about) ---
        if slug == '404' or file_name == '404.md':
            special_link = '404.html'
            special_post = { 
                **metadata, 'content_html': content_html, 'toc_html': '', 
                'link': special_link, 'footer_time_info': mod_time_cn
            }
            # ⭐ 关键修复：404 页面应使用 generate_page_html，而不是 generate_post_page
            if needs_rebuild_html: # 使用 needs_rebuild_html
                generator.generate_page_html(
                    special_post['content_html'], 
                    special_post['title'], 
                    '404', 
                    special_link, 
                    special_post['footer_time_info']
                )

            new_manifest.setdefault('posts', {})[relative_path] = {'hash': current_hash, 'link': special_link}
            continue 

        if metadata.get('hidden') is True: 
            if slug == 'about' or file_name == config.ABOUT_PAGE:
                 special_link = 'about.html'
                 special_post = { 
                     **metadata, 'content_html': content_html, 'toc_html': '', 
                     'link': special_link, 'footer_time_info': mod_time_cn
                 }
                 # ⭐ 修复: 特殊页面也需要检查 theme_changed
                 if needs_rebuild_html: # 使用 needs_rebuild_html
                     generator.generate_page_html(
                         special_post['content_html'], special_post['title'], 
                         'about', special_link, special_post['footer_time_info']
                     )
            new_manifest.setdefault('posts', {})[relative_path] = {'hash': current_hash, 'link': 'hidden'}
            continue 

        if not all(k in metadata for k in ['date', 'title']): 
            continue
            
        # --- 普通文章处理 ---
        # 链接格式：posts/slug.html (在 generator.py 中会被清洗为 /posts/slug/ 格式)
        post_link = os.path.join(config.POSTS_DIR_NAME, f"{slug}.html").replace('\\', '/')
        post = {
            **metadata, 
            'content_markdown': content_md,
            'content_html': content_html,
            'toc_html': toc_html,
            'link': post_link,
            'footer_time_info': mod_time_cn 
        }
        
        # 1. 准备 NEW metadata for comparison (critical fields for list pages)
        new_manifest_data = {
            'hash': current_hash,
            'title': post.get('title', ''),
            'date_str': post['date'].strftime('%Y-%m-%d') if post.get('date') else '',
            'link': post_link, 
            # 存储排好序的标签名称列表，以便准确对比
            'tags_list': sorted([t['name'] for t in post.get('tags', [])]),
            'hidden': post.get('hidden', False),
            'status': post.get('status', 'published'),
        }

        # 2. 检查元数据是否变化 (忽略 hash 字段)
        metadata_changed = False
        for key, new_value in new_manifest_data.items():
            if key == 'hash': 
                continue
            
            # 使用 str() 确保布尔值、列表等数据类型能被准确对比
            if str(new_value) != str(old_item.get(key)):
                metadata_changed = True
                break
                
        # 只要内容或元数据变化，列表页就需要重建
        needs_rebuild_list = needs_full_build or metadata_changed

        if metadata_changed and not needs_full_build:
            print(f"   -> [METADATA CHANGED] {os.path.basename(md_file)}")
            posts_data_changed = True

        # 如果元数据变化或内容变化，都需要重建列表页
        if needs_rebuild_list and not needs_full_build:
            posts_data_changed = True
        
        # 清理旧的 HTML 文件 (如果 Slug 变化)
        if old_item.get('link') and old_item.get('link') != post_link and old_item.get('link') != 'hidden' and old_item.get('link') != '404.html':
             # 确保路径是基于 BUILD_DIR 的，而不是相对于根目录
             old_html_path_parts = old_item['link'].strip('/').split('/')
             old_html_dir = os.path.join(config.BUILD_DIR, *old_html_path_parts)
             
             try:
                 if os.path.exists(old_html_dir) and os.path.isdir(old_html_dir):
                     # 删除旧的 /slug/ 目录
                     shutil.rmtree(old_html_dir) 
                     print(f"   -> [CLEANUP] Deleted old post directory: {old_html_dir}")
                 elif os.path.exists(old_html_dir):
                    # 处理 /post.html 模式（如果存在）
                    os.remove(old_html_dir)
                    print(f"   -> [CLEANUP] Deleted old HTML file: {old_html_dir}")
             except Exception as e:
                 print(f"   -> [WARNING] Failed to clean up old post path {old_html_dir}: {e}")
                
        for tag_data in post.get('tags', []):
            tag_map[tag_data['name']].append(post)
            
        parsed_posts.append(post)

        # 3. 更新 Manifest (保存 Hash 和所有关键元数据)
        new_manifest.setdefault('posts', {})[relative_path] = new_manifest_data
        
        # 只有当内容或链接/元数据发生变化，或者主题变动时，才需要重建文章详情页
        if needs_rebuild_html:
            posts_to_build.append(post) 
            
    # 清理被删除的源文件
    deleted_paths = set(old_manifest.get('posts', {}).keys()) - source_md_paths
    for deleted_path in deleted_paths:
        item = old_manifest['posts'][deleted_path]
        deleted_link = item.get('link')
        print(f"   -> [DELETED] Source file {deleted_path} removed.")
        posts_data_changed = True 
        
        if deleted_link and deleted_link != 'hidden' and deleted_link != '404.html':
            # 确保路径是基于 BUILD_DIR 的
            deleted_html_path_parts = deleted_link.strip('/').split('/')
            deleted_html_dir = os.path.join(config.BUILD_DIR, *deleted_html_path_parts)
            
            try:
                if os.path.exists(deleted_html_dir) and os.path.isdir(deleted_html_dir):
                    shutil.rmtree(deleted_html_dir)
                    print(f"   -> [CLEANUP] Deleted post directory: {deleted_html_dir}")
                else:
                    # 处理 /post.html 模式（如果存在）
                    deleted_html_file = os.path.join(config.BUILD_DIR, deleted_link.strip('/'))
                    if os.path.exists(deleted_html_file):
                        os.remove(deleted_html_file)
                        print(f"   -> [CLEANUP] Deleted post HTML file: {deleted_html_file}")
            except Exception as e:
                 print(f"   -> [WARNING] Failed to clean up deleted path {deleted_html_dir}: {e}")
                 
            # 从新清单中移除已删除的文章记录
            new_manifest['posts'].pop(deleted_path, None)


    final_parsed_posts = sorted(parsed_posts, key=lambda p: p['date'], reverse=True)
    
    print(f"   -> Successfully parsed {len(final_parsed_posts)} blog posts. ({len(posts_to_build)} HTML files rebuilt)")

    # -------------------------------------------------------------------------
    # [4/5] P/N Navigation Injection & Build Time
    # -------------------------------------------------------------------------
    
    # 仅对可见文章生成上/下导航
    visible_posts_for_nav = [p for p in final_parsed_posts if not is_post_hidden(p)]
    
    for i, post in enumerate(visible_posts_for_nav):
        # 找到 post 在 final_parsed_posts 中的原始引用 (用于 posts_to_build 列表)
        original_post = next(p for p in final_parsed_posts if p['link'] == post['link'])

        prev_post_data = visible_posts_for_nav[i - 1] if i > 0 else None
        next_post_data = visible_posts_for_nav[i + 1] if i < len(visible_posts_for_nav) - 1 else None

        original_post['prev_post_nav'] = None
        if prev_post_data:
            original_post['prev_post_nav'] = {
                'title': prev_post_data['title'],
                'link': prev_post_data['link']
            }

        original_post['next_post_nav'] = None
        if next_post_data:
            original_post['next_post_nav'] = {
                'title': next_post_data['title'],
                'link': next_post_data['link']
            }

    now_utc = datetime.now(timezone.utc)
    now_utc8 = now_utc.astimezone(TIMEZONE_INFO)
    # 列表页使用不带微秒的简洁格式
    global_build_time_cn = f"网站构建时间: {now_utc8.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)"
    
    # -------------------------------------------------------------------------
    # [5/5] 生成 HTML (应用增量逻辑)
    # -------------------------------------------------------------------------
    print("\n[5/5] Generating HTML...")
    
    # 1. 生成普通文章详情页 
    # ⭐ 修复: 如果主题变动，重建所有文章页
    posts_to_build_all = final_parsed_posts if theme_changed else posts_to_build
    
    if theme_changed and not posts_to_build:
        print("   -> [REBUILDING] ALL Post Pages (Theme changed, but no post content changed)")

    # 如果主题/逻辑变动，posts_to_build_all 是所有文章，否则只是变动的文章
    for post in posts_to_build_all:
        generator.generate_post_page(post) 

    # 2. 生成列表页 (应用增量逻辑)
    # ⭐ 修复: 只要 posts_data_changed 为 True，或者主题/模板文件有变动，就重建所有列表页
    if not old_manifest or posts_data_changed or theme_changed: # <-- 关键修改
        print("   -> [REBUILDING] Index, Archive, Tags, RSS (Post data or Theme changed)")
        
        generator.generate_index_html(final_parsed_posts, global_build_time_cn) 
        generator.generate_archive_html(final_parsed_posts, global_build_time_cn) 
        generator.generate_tags_list_html(tag_map, global_build_time_cn) 

        for tag, posts in tag_map.items():
            sorted_tag = sorted(posts, key=lambda p: p['date'], reverse=True)
            generator.generate_tag_page(tag, sorted_tag, global_build_time_cn) 

        generator.generate_robots_txt()
        
        with open(os.path.join(config.BUILD_DIR, config.SITEMAP_FILE), 'w', encoding='utf-8') as f:
            f.write(generator.generate_sitemap(final_parsed_posts))
        with open(os.path.join(config.BUILD_DIR, config.RSS_FILE), 'w', encoding='utf-8') as f:
            f.write(generator.generate_rss(final_parsed_posts))
            
    else:
        print("   -> [SKIPPED] Index, Archive, Tags, RSS (No post data or Theme change)")

    # 3. 保存新的构建清单
    # ⭐ 修复: 保存 new_manifest，其中包含 posts, static_files, templates 的哈希值
    save_manifest(new_manifest)
    print("   -> Manifest file updated.")
    
    print("\n✅ BUILD COMPLETE")

if __name__ == '__main__':
    build_site()