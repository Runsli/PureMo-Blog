# generator.py

import os
import shutil 
import glob   
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional 
from jinja2 import Environment, FileSystemLoader
import json 
import re 
import config
from parser import tag_to_slug 
from bs4 import BeautifulSoup 

# --- Jinja2 环境配置配置 ---
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=True,
    trim_blocks=True, 
    lstrip_blocks=True
)

# --- 辅助函数：路径和 URL (核心路径修正) ---

def get_site_root_prefix() -> str:
    """获取网站在部署环境中的相对子目录路径前缀。"""
    root = config.REPO_SUBPATH.strip()
    if not root or root == '/':
        config.SITE_ROOT = '' 
        return ''
    root = root.rstrip('/')
    config.SITE_ROOT = root if root.startswith('/') else f'/{root}'
    return config.SITE_ROOT

def make_internal_url(path: str) -> str:
    """生成规范化的内部 URL (Pretty URL: /slug/)。"""
    if not path:
        return ""
        
    normalized_path = path if path.startswith('/') else f'/{path}'
    site_root = get_site_root_prefix()
    
    # 移除 .html 后缀，除非是特殊文件
    if normalized_path.lower().endswith('.html') and \
       not normalized_path.lower().endswith(config.RSS_FILE) and \
       not normalized_path.lower().endswith(config.SITEMAP_FILE) and \
       not normalized_path.lower() == '/404.html':
        normalized_path = normalized_path[:-5]
    
    if normalized_path.lower() == '/index': 
        normalized_path = '/'
    elif normalized_path.lower() == '/404' or normalized_path.lower() == '/404.html':
        # 404 页面通常不需要 url 后缀，或者保持原样
        pass 
    elif normalized_path.lower().endswith(config.RSS_FILE):
        pass
    elif normalized_path.lower().endswith(config.SITEMAP_FILE):
        pass
    elif normalized_path != '/' and not normalized_path.endswith('/'):
        normalized_path = f'{normalized_path}/'
    
    if not site_root:
        return normalized_path
    
    if normalized_path == '/':
        return f"{site_root}/"
    
    return f"{site_root}{normalized_path}"

def is_post_hidden(post: Dict[str, Any]) -> bool:
    """检查文章是否应被隐藏。"""
    return post.get('status', 'published').lower() == 'draft' or post.get('hidden') is True

# --- 数据清洗函数 ---

def process_posts_for_template(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """深度清洗文章列表链接。"""
    cleaned_posts = []
    for post in posts:
        new_post = post.copy()
        if 'link' in new_post:
            new_post['link'] = make_internal_url(new_post['link'])
        if 'prev_post_nav' in new_post and new_post['prev_post_nav']:
            nav = new_post['prev_post_nav'].copy()
            nav['link'] = make_internal_url(nav['link'])
            new_post['prev_post_nav'] = nav
        if 'next_post_nav' in new_post and new_post['next_post_nav']:
            nav = new_post['next_post_nav'].copy()
            nav['link'] = make_internal_url(nav['link'])
            new_post['next_post_nav'] = nav
        if 'tags' in new_post and new_post['tags']:
            cleaned_tags = []
            for tag in new_post['tags']:
                tag_copy = tag.copy()
                tag_path = f"{config.TAGS_DIR_NAME}/{tag_copy['slug']}"
                tag_copy['link'] = make_internal_url(tag_path) 
                cleaned_tags.append(tag_copy)
            new_post['tags'] = cleaned_tags
        cleaned_posts.append(new_post)
    return cleaned_posts

# --- 核心生成函数 ---

def get_json_ld_schema(post: Dict[str, Any]) -> str:
    """生成 Article 类型的 JSON-LD 结构化数据。"""
    base_url = config.BASE_URL.rstrip('/')
    image_url = f"{base_url}{config.SITE_ROOT}/static/default-cover.png"
    
    soup = BeautifulSoup(post['content_html'], 'html.parser')
    img_tag = soup.find('img')
    
    if img_tag and 'src' in img_tag.attrs:
        relative_path = img_tag['src'].lstrip('/')
        if not relative_path.startswith(('http', '//')):
            site_root = get_site_root_prefix()
            image_url = f"{base_url}{site_root}/{relative_path}"
            image_url = image_url.replace('//', '/')
            image_url = image_url.replace(':/', '://')
        else:
            image_url = relative_path
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post['title'],
        "image": image_url,
        "datePublished": post['date'].isoformat(),
        "dateModified": post['date'].isoformat(), 
        "author": {
            "@type": "Person",
            "name": config.BLOG_AUTHOR
        },
        "publisher": {
            "@type": "Organization",
            "name": config.BLOG_TITLE,
            "logo": {
                "@type": "ImageObject",
                "url": f"{base_url}{get_site_root_prefix()}/static/logo.png" 
            }
        },
        "description": post.get('excerpt', config.BLOG_DESCRIPTION),
        "mainEntityOfPage": {
            "@type": "WebPage",
            "url": f"{base_url}{make_internal_url(post['link'])}"
        }
    }
    return json.dumps(schema, ensure_ascii=False, indent=4)

def generate_index_html(sorted_posts: List[Dict[str, Any]], build_time_info: str):
    """生成首页"""
    try:
        output_path = os.path.join(config.BUILD_DIR, 'index.html')
        visible_posts = [p for p in sorted_posts if not is_post_hidden(p)][:config.MAX_POSTS_ON_INDEX]

        template = env.get_template('base.html')
        context = {
            'page_id': 'index',
            'page_title': "首页",
            'blog_title': config.BLOG_TITLE,
            'blog_description': config.BLOG_DESCRIPTION,
            'blog_author': config.BLOG_AUTHOR,
            'posts': process_posts_for_template(visible_posts),
            'max_posts_on_index': config.MAX_POSTS_ON_INDEX,
            'site_root': get_site_root_prefix(),
            'current_year': datetime.now().year,
            'css_filename': config.CSS_FILENAME,
            'canonical_url': f"{config.BASE_URL.rstrip('/')}{get_site_root_prefix()}/",
            'footer_time_info': build_time_info,
            'footer_content_type': config.FOOTER_CONTENT_TYPE,
            'footer_custom_text': config.FOOTER_CUSTOM_TEXT,
        }
        
        html_content = template.render(context)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Generated: index.html")
    except Exception as e:
        print(f"Error index.html: {e}")


def generate_archive_html(sorted_posts: List[Dict[str, Any]], build_time_info: str):
    """生成归档页 (archive/index.html)"""
    try:
        output_dir = os.path.join(config.BUILD_DIR, 'archive')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'index.html')
        
        visible_posts = [p for p in sorted_posts if not is_post_hidden(p)]
        
        archive_by_year = defaultdict(list)
        for post in visible_posts:
            archive_by_year[post['date'].year].append(post)
        
        sorted_archive = sorted(archive_by_year.items(), key=lambda item: item[0], reverse=True)

        template = env.get_template('base.html')
        
        # --- UI 重构: 自定义归档列表样式 ---
        archive_html = "<div class=\"archive-page\">\n"
        
        for year, posts in sorted_archive:
            archive_html += f"<h2 class=\"archive-year\">{year} <small>({len(posts)})</small></h2>\n"
            archive_html += "<ul class=\"archive-list\">\n"
            
            for post in posts:
                link = make_internal_url(post['link']) 
                date_str = post['date'].strftime('%m-%d')
                
                archive_html += f"""
                <li class="archive-item">
                    <span class="archive-date">{date_str}</span>
                    <a class="archive-link" href="{link}">{post['title']}</a>
                </li>
                """
            archive_html += "</ul>\n"
            
        archive_html += "</div>"
            
        context = {
            'page_id': 'archive',
            'page_title': "归档",
            'blog_title': config.BLOG_TITLE,
            'blog_description': '归档',
            'blog_author': config.BLOG_AUTHOR,
            'content_html': archive_html, 
            'posts': [],
            'site_root': get_site_root_prefix(),
            'current_year': datetime.now().year,
            'css_filename': config.CSS_FILENAME,
            'canonical_url': f"{config.BASE_URL.rstrip('/')}{make_internal_url('/archive')}",
            'footer_time_info': build_time_info,
            'footer_content_type': config.FOOTER_CONTENT_TYPE,
            'footer_custom_text': config.FOOTER_CUSTOM_TEXT,
        }
        
        html_content = template.render(context)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Generated: archive/index.html")
    except Exception as e:
        print(f"Error archive.html: {e}")


def generate_tags_list_html(tag_map: Dict[str, List[Dict[str, Any]]], build_time_info: str):
    """生成标签列表页"""
    try:
        output_dir = os.path.join(config.BUILD_DIR, 'tags')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'index.html')
        
        sorted_tags = sorted(tag_map.items(), key=lambda item: len(item[1]), reverse=True)
        tags_html = "<h1>标签列表</h1>\n<div class=\"tag-cloud\">\n"
        
        for tag, posts in sorted_tags:
            tag_slug = tag_to_slug(tag)
            link = make_internal_url(f"{config.TAGS_DIR_NAME}/{tag_slug}")
            count = len(posts)
            font_size = max(1.0, min(2.5, 0.8 + count * 0.15))
            tags_html += f"<a href=\"{link}\" style=\"font-size: {font_size}rem;\" class=\"tag-cloud-item\">{tag} ({count})</a>\n"
        tags_html += "</div>\n"

        template = env.get_template('base.html')
        context = {
            'page_id': 'tags',
            'page_title': "标签",
            'blog_title': config.BLOG_TITLE,
            'blog_description': '标签',
            'blog_author': config.BLOG_AUTHOR,
            'content_html': tags_html,
            'site_root': get_site_root_prefix(),
            'current_year': datetime.now().year,
            'css_filename': config.CSS_FILENAME,
            'canonical_url': f"{config.BASE_URL.rstrip('/')}{make_internal_url('/tags')}",
            'footer_time_info': build_time_info,
            'footer_content_type': config.FOOTER_CONTENT_TYPE,
            'footer_custom_text': config.FOOTER_CUSTOM_TEXT,
        }
        
        html_content = template.render(context)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Generated: tags/index.html")
    except Exception as e:
        print(f"Error tags.html: {e}")


def generate_tag_page(tag_name: str, sorted_tag_posts: List[Dict[str, Any]], build_time_info: str):
    """生成单个标签页面"""
    try:
        tag_slug = tag_to_slug(tag_name)
        output_dir = os.path.join(config.BUILD_DIR, config.TAGS_DIR_NAME, tag_slug)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'index.html')

        template = env.get_template('base.html')
        processed_posts = process_posts_for_template(sorted_tag_posts)
        
        context = {
            'page_id': 'tag',
            'page_title': f"标签: {tag_name}",
            'blog_title': config.BLOG_TITLE,
            'blog_description': config.BLOG_DESCRIPTION,
            'blog_author': config.BLOG_AUTHOR,
            'posts': processed_posts, 
            'tag': tag_name, 
            'site_root': get_site_root_prefix(),
            'current_year': datetime.now().year,
            'css_filename': config.CSS_FILENAME,
            'canonical_url': f"{config.BASE_URL.rstrip('/')}{make_internal_url(f'{config.TAGS_DIR_NAME}/{tag_slug}')}",
            'footer_time_info': build_time_info,
            'footer_content_type': config.FOOTER_CONTENT_TYPE,
            'footer_custom_text': config.FOOTER_CUSTOM_TEXT,
        }
        
        html_content = template.render(context)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Generated tag page: {tag_name}")
    except Exception as e:
        print(f"Error tag page {tag_name}: {e}")

def generate_robots_txt():
    """生成 robots.txt"""
    try:
        output_path = os.path.join(config.BUILD_DIR, 'robots.txt')
        content = f"User-agent: *\nAllow: /\nSitemap: {config.BASE_URL.rstrip('/')}{make_internal_url(config.SITEMAP_FILE)}\n"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Generated: robots.txt")
    except Exception as e:
        print(f"Error robots.txt: {e}")

def generate_sitemap(parsed_posts: List[Dict[str, Any]]) -> str:
    """生成 sitemap.xml"""
    urls = []
    base_url = config.BASE_URL.rstrip('/')
    
    for path, prio in [('/', '1.0'), ('/archive', '0.8'), ('/tags', '0.8'), ('/404', '0.1'), (config.RSS_FILE, '0.1')]:
        urls.append(f"<url><loc>{base_url}{make_internal_url(path)}</loc><priority>{prio}</priority></url>")

    if os.path.exists(os.path.join(config.BUILD_DIR, 'about', 'index.html')):
         urls.append(f"<url><loc>{base_url}{make_internal_url('/about')}</loc><priority>0.8</priority></url>")

    all_tags = set()
    for post in parsed_posts:
        if is_post_hidden(post) or not post.get('link'): continue
        link = f"{base_url}{make_internal_url(post['link'])}"
        lastmod = post['date'].strftime('%Y-%m-%d')
        urls.append(f"<url><loc>{link}</loc><lastmod>{lastmod}</lastmod><priority>0.6</priority></url>")
        for tag in post.get('tags', []):
            all_tags.add(tag['name'])
    
    for tag in all_tags:
        slug = tag_to_slug(tag)
        link = f"{base_url}{make_internal_url(f'{config.TAGS_DIR_NAME}/{slug}')}"
        urls.append(f"<url><loc>{link}</loc><priority>0.5</priority></url>")

    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{"".join(urls)}</urlset>'

def generate_rss(parsed_posts: List[Dict[str, Any]]) -> str:
    """生成 RSS Feed"""
    items = []
    base_url = config.BASE_URL.rstrip('/')
    visible_posts = [p for p in parsed_posts if not is_post_hidden(p)]
    
    for post in visible_posts[:10]:
        if not post.get('link'): continue
        link = f"{base_url}{make_internal_url(post['link'])}"
        pub_date = datetime.combine(post['date'], datetime.min.time(), tzinfo=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000') 
        items.append(f"<item><title>{post['title']}</title><link>{link}</link><pubDate>{pub_date}</pubDate><guid isPermaLink=\"true\">{link}</guid><description><![CDATA[{post['content_html']}]]></description></item>")
    
    rss_link = make_internal_url(config.RSS_FILE) 
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>{config.BLOG_TITLE}</title><link>{base_url}{make_internal_url("/")}</link><description>{config.BLOG_DESCRIPTION}</description><language>zh-cn</language><atom:link href="{base_url}{rss_link}" rel="self" type="application/rss+xml" /><lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>{"".join(items)}</channel></rss>'

def generate_page_html(content_html: str, page_title: str, page_id: str, canonical_path_with_html: str, build_time_info: str):
    """生成通用页面 (已修复：404页面生成在根目录)"""
    try:
        # --- 修复开始：针对 404 页面的特殊路径处理 ---
        if page_id == '404':
            # 404 页面必须生成在根目录，文件名为 404.html
            output_dir = config.BUILD_DIR
            output_path = os.path.join(output_dir, '404.html')
        else:
            # 其他页面（如 about）生成在子目录，如 /about/index.html
            output_dir = os.path.join(config.BUILD_DIR, page_id)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'index.html')
        # --- 修复结束 ---
        
        template = env.get_template('base.html')
        canonical_path = make_internal_url(canonical_path_with_html) 
        
        context = {
            'page_id': page_id,
            'page_title': page_title,
            'blog_title': config.BLOG_TITLE,
            'blog_description': config.BLOG_DESCRIPTION,
            'blog_author': config.BLOG_AUTHOR,
            'content_html': content_html, 
            'site_root': get_site_root_prefix(),
            'current_year': datetime.now().year,
            'css_filename': config.CSS_FILENAME,
            'canonical_url': f"{config.BASE_URL.rstrip('/')}{canonical_path}",
            'footer_time_info': build_time_info,
            'footer_content_type': config.FOOTER_CONTENT_TYPE,
            'footer_custom_text': config.FOOTER_CUSTOM_TEXT,
            'json_ld_schema': None, 
        }
        
        html_content = template.render(context)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Generated: {output_path} (Page ID: {page_id})")

    except Exception as e:
        print(f"Error {page_id}: {e}")

# 在 generator.py 中添加以下函数

def get_copyright_notice(title, author, url, license_config=None):
    """根据配置生成版权申明文本"""
    if license_config is None:
        license_config = {
            'type': 'CC_BY_NC_4.0',
            'custom_text': '',
            'additional_note': '转载请遵循协议，务必保留作者署名及原文链接。'
        }
    
    if license_config.get('type') == 'CC_BY_NC_4.0':
        return f"本文依据 <a href='https://creativecommons.org/licenses/by-nc/4.0/' target='_blank' rel='license noopener noreferrer'>CC BY-NC 4.0 许可协议</a> 发布。"
    elif license_config.get('type') == 'CC_BY_SA_4.0':
        return f"本文依据 <a href='https://creativecommons.org/licenses/by-sa/4.0/' target='_blank' rel='license noopener noreferrer'>CC BY-SA 4.0 许可协议</a> 发布。"
    elif license_config.get('type') == 'MIT':
        return f"本文采用 MIT 许可证发布。"
    elif license_config.get('type') == 'CUSTOM':
        return license_config.get('custom_text', '')
    else:
        return f"本文依据 <a href='https://creativecommons.org/licenses/by-nc/4.0/' target='_blank' rel='license noopener noreferrer'>CC BY-NC 4.0 许可协议</a> 发布。"

def get_copyright_format(title, author, url, license_config=None):
    """生成标准引用格式"""
    if license_config is None:
        license_config = {
            'format_template': '''本文标题：{title}
作者：{author}
原文链接：<a href="{url}">{url}</a>'''
        }
    
    template = license_config.get('format_template', '''本文标题：{title}
作者：{author}
原文链接：<a href="{url}">{url}</a>''')
    
    return template.format(title=title, author=author, url=url)

# 在 generator.py 中替换整个 generate_post_page 函数
def generate_post_page(post: Dict[str, Any]):
    """生成单篇文章页面"""
    try:
        relative_link = post.get('link')
        if not relative_link: return
        # 404 页面不通过此函数生成
        if relative_link.lower() == '404.html': return

        clean_name = relative_link[:-5] if relative_link.lower().endswith('.html') else relative_link
        clean_name = clean_name.strip('/')
        output_dir = os.path.join(config.BUILD_DIR, clean_name)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'index.html')

        template = env.get_template('base.html')
        processed_list = process_posts_for_template([post])
        current_post_processed = processed_list[0]
        json_ld_schema = get_json_ld_schema(post)

        # 版权相关函数
        def get_copyright_notice(title, author, url):
            license_config = config.COPYRIGHT_LICENSE
            if not license_config.get('enable', False):
                return ""
            
            license_type = license_config.get('type', 'CC_BY_NC_4.0')
            if license_type == 'CUSTOM':
                return license_config.get('custom_text', '')
            elif license_type in license_config.get('allowed_types', {}):
                license_info = license_config['allowed_types'][license_type]
                # 替换模板中的占位符
                text = license_info['text']
                text = text.replace('{url}', url).replace('{title}', title).replace('{author}', author)
                return text
            else:
                # 默认返回 CC BY-NC 4.0
                default_license = license_config['allowed_types'].get('CC_BY_NC_4.0', {})
                text = default_license.get('text', '本文依据 <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="license noopener noreferrer">CC BY-NC 4.0 许可协议</a> 发布。')
                text = text.replace('{url}', url).replace('{title}', title).replace('{author}', author)
                return text

        def get_copyright_format(title, author, url):
            license_config = config.COPYRIGHT_LICENSE
            template_str = license_config.get('format_template', '''本文标题：{title}
作者：{author}
原文链接：<a href="{url}">{url}</a>''')
            return template_str.format(title=title, author=author, url=url)

        context = {
            'page_id': 'post',
            'page_title': post['title'],
            'blog_title': config.BLOG_TITLE,
            'blog_description': post.get('excerpt', config.BLOG_DESCRIPTION),
            'blog_author': config.BLOG_AUTHOR,
            'content_html': post['content_html'],
            'post': current_post_processed,
            'post_date': post.get('date_formatted', ''),
            'post_tags': current_post_processed.get('tags', []),
            'toc_html': post.get('toc_html'),
            'prev_post_nav': current_post_processed.get('prev_post_nav'),
            'next_post_nav': current_post_processed.get('next_post_nav'),
            'site_root': get_site_root_prefix(),
            'current_year': datetime.now().year,
            'css_filename': config.CSS_FILENAME,
            'canonical_url': f"{config.BASE_URL.rstrip('/')}{make_internal_url(relative_link)}",
            'footer_time_info': post.get('footer_time_info', ''),
            'footer_content_type': config.FOOTER_CONTENT_TYPE,
            'footer_custom_text': config.FOOTER_CUSTOM_TEXT,
            'json_ld_schema': json_ld_schema,
            # 版权相关
            'copyright_notice': get_copyright_notice,
            'copyright_format': get_copyright_format,
            'copyright_config': config.COPYRIGHT_LICENSE,
        }

        html_content = template.render(context)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Generated: {output_path}")

    except Exception as e:
        print(f"Error generating post {post.get('title')}: {e}")