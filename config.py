# config.py

import os

# --- 站点配置 ---
# 这里主要是配置站点信息，如标题、描述、作者、CSS 文件名、Markdown 扩展列表、Markdown 扩展配置、列表配置、目录和文件配置、特殊文件名称等。

# 博客的根 URL，也就是外部直接访问的站点的链接

# 当你部署在 GitHub Pages, Netlify 或者 Vercel 这样的平台，你需要修改 BASE_URL 配置项为对应的链接
# 当你在设置了自定义域名的时候，你也需要修改 BASE_URL 配置项为对应的链接
# 也就是最终的访问链接

BASE_URL = "https://PureMo-Blog.vercel.app"

# 假设你的网站部署在 GitHub Pages 且不是 username.github.io 的链接
# 而是 https://username.github.io/your-repo-name/
# 这种情况下，你要修改下面的这个 REPO_SUBPATH 配置项为对应的 子目录路径
# 请将 "/your-repo-name" 替换为你实际的子目录路径或 GitHub 仓库名，填写在下方

REPO_SUBPATH = "" 

# 内部链接的根路径
SITE_ROOT = REPO_SUBPATH.rstrip('/')

# 这里是博客的标题、描述、作者

# 这里是网站的标题
BLOG_TITLE = "PureMo-Blog 的个人网站"

# 描述，通常作为描述信息在搜索引擎的结果页面或者社交链接分享的时候链接中显示
BLOG_DESCRIPTION = "专注于数据科学、极简主义与纯粹的 Web 技术。"
# 作者，主要作用于网站页脚的位置进行显示
BLOG_AUTHOR = "PureMo-Blog"

# 存储 CSS 文件的哈希名
CSS_FILENAME = 'style.css' 

# 定义代码高亮使用的 CSS 类名
CODE_HIGHLIGHT_CLASS = 'highlight'

# 页脚内容配置 - 可选值: 'build_time', 'empty', 'custom'
FOOTER_CONTENT_TYPE = 'build_time'  # 默认显示构建时间
FOOTER_CUSTOM_TEXT = 'Powered by My Blog Generator'  # 自定义文本内容

# config.py 中添加完整的版权配置
# --- 版权声明配置 ---
COPYRIGHT_LICENSE = {
    'enable': True,  # 是否启用版权申明
    'type': 'CC_BY_NC_SA_4.0',  # 许可协议类型
    'custom_text': '',  # 自定义版权文本，当 type 为 CUSTOM 时使用
    'show_license_icon': True,  # 是否显示许可协议图标
    'show_standard_format': True,  # 是否显示标准格式
    'additional_note': '本文内容受相应许可证保护，商业用途请查阅具体许可证条款。转载或引用时请保留原作者署名及原文链接。',  # 附加说明
    'format_template': '''本文标题：{title}
作者：{author}
原文链接：<a href="{url}">{url}</a>''',  # 标准格式模板
    'allowed_types': {
        # Creative Commons 许可证
        'CC_BY_4.0': {
            'text': '本文依据 <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="license noopener noreferrer">CC BY 4.0 许可协议</a> 发布。',
            'icon': '<i title="Creative Commons Attribution">CC-BY</i>'
        },
        'CC_BY_SA_4.0': {
            'text': '本文依据 <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="license noopener noreferrer">CC BY-SA 4.0 许可协议</a> 发布。',
            'icon': '<i title="Creative Commons Attribution ShareAlike">CC-BY-SA</i>'
        },
        'CC_BY_NC_4.0': {
            'text': '本文依据 <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="license noopener noreferrer">CC BY-NC 4.0 许可协议</a> 发布。',
            'icon': '<i title="Creative Commons Attribution NonCommercial">CC-BY-NC</i>'
        },
        'CC_BY_NC_SA_4.0': {
            'text': '本文依据 <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="license noopener noreferrer">CC BY-NC-SA 4.0 许可协议</a> 发布。',
            'icon': '<i title="Creative Commons Attribution NonCommercial ShareAlike">CC-BY-NC-SA</i>'
        },
        'CC_BY_NC_ND_4.0': {
            'text': '本文依据 <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank" rel="license noopener noreferrer">CC BY-NC-ND 4.0 许可协议</a> 发布。',
            'icon': '<i title="Creative Commons Attribution NonCommercial NoDerivatives">CC-BY-NC-ND</i>'
        },
        'CC_BY_ND_4.0': {
            'text': '本文依据 <a href="https://creativecommons.org/licenses/by-nd/4.0/" target="_blank" rel="license noopener noreferrer">CC BY-ND 4.0 许可协议</a> 发布。',
            'icon': '<i title="Creative Commons Attribution NoDerivatives">CC-BY-ND</i>'
        },
        'CC_ZERO_1.0': {
            'text': '本文依据 <a href="https://creativecommons.org/publicdomain/zero/1.0/" target="_blank" rel="license noopener noreferrer">CC0 1.0 通用公共领域贡献</a> 发布。',
            'icon': '<i title="Creative Commons Zero">CC0</i>'
        },
        
        # 开源软件许可证
        'MIT': {
            'text': '本文采用 <a href="https://opensource.org/licenses/MIT" target="_blank" rel="license noopener noreferrer">MIT 许可证</a> 发布。',
            'icon': '<i title="MIT License">MIT</i>'
        },
        'BSD_2_CLAUSE': {
            'text': '本文采用 <a href="https://opensource.org/licenses/BSD-2-Clause" target="_blank" rel="license noopener noreferrer">BSD 2-Clause 许可证</a> 发布。',
            'icon': '<i title="BSD 2-Clause License">BSD-2</i>'
        },
        'BSD_3_CLAUSE': {
            'text': '本文采用 <a href="https://opensource.org/licenses/BSD-3-Clause" target="_blank" rel="license noopener noreferrer">BSD 3-Clause 许可证</a> 发布。',
            'icon': '<i title="BSD 3-Clause License">BSD-3</i>'
        },
        'APACHE_2.0': {
            'text': '本文依据 <a href="https://www.apache.org/licenses/LICENSE-2.0" target="_blank" rel="license noopener noreferrer">Apache License 2.0</a> 发布。',
            'icon': '<i title="Apache License 2.0">Apache-2.0</i>'
        },
        'GPL_2.0': {
            'text': '本文依据 <a href="https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html" target="_blank" rel="license noopener noreferrer">GNU General Public License v2.0</a> 发布。',
            'icon': '<i title="GNU General Public License v2.0">GPL-2.0</i>'
        },
        'GPL_3.0': {
            'text': '本文依据 <a href="https://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank" rel="license noopener noreferrer">GNU General Public License v3.0</a> 发布。',
            'icon': '<i title="GNU General Public License v3.0">GPL-3.0</i>'
        },
        'LGPL_2.1': {
            'text': '本文依据 <a href="https://www.gnu.org/licenses/lgpl-2.1.en.html" target="_blank" rel="license noopener noreferrer">GNU Lesser General Public License v2.1</a> 发布。',
            'icon': '<i title="GNU Lesser General Public License v2.1">LGPL-2.1</i>'
        },
        'LGPL_3.0': {
            'text': '本文依据 <a href="https://www.gnu.org/licenses/lgpl-3.0.en.html" target="_blank" rel="license noopener noreferrer">GNU Lesser General Public License v3.0</a> 发布。',
            'icon': '<i title="GNU Lesser General Public License v3.0">LGPL-3.0</i>'
        },
        'MPL_2.0': {
            'text': '本文采用 <a href="https://www.mozilla.org/en-US/MPL/2.0/" target="_blank" rel="license noopener noreferrer">Mozilla Public License 2.0</a> 发布。',
            'icon': '<i title="Mozilla Public License 2.0">MPL-2.0</i>'
        },
        'EPL_2.0': {
            'text': '本文采用 <a href="https://www.eclipse.org/org/documents/epl-2.0/EPL-2.0.txt" target="_blank" rel="license noopener noreferrer">Eclipse Public License 2.0</a> 发布。',
            'icon': '<i title="Eclipse Public License 2.0">EPL-2.0</i>'
        },
        
        # 其他常见许可证
        'UNLICENSE': {
            'text': '本文已放弃所有版权及相关权利，依据 <a href="https://unlicense.org/" target="_blank" rel="license noopener noreferrer">Unlicense</a> 发布。',
            'icon': '<i title="The Unlicense">Unlicense</i>'
        },
        'WTFPL': {
            'text': '本文采用 <a href="http://www.wtfpl.net/about/" target="_blank" rel="license noopener noreferrer">DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE</a> 发布。',
            'icon': '<i title="Do What The F*ck You Want To Public License">WTFPL</i>'
        },
        'AGPL_3.0': {
            'text': '本文依据 <a href="https://www.gnu.org/licenses/agpl-3.0.en.html" target="_blank" rel="license noopener noreferrer">GNU Affero General Public License v3.0</a> 发布。',
            'icon': '<i title="GNU Affero General Public License v3.0">AGPL-3.0</i>'
        },
        
        # 自定义许可证
        'CUSTOM': {
            'text': '',  # 由 custom_text 字段决定
            'icon': '<i title="Custom License">Custom</i>'
        }
    }
}
# --- Markdown 配置 ---
# 1. 扩展列表 (使用短名称)
MARKDOWN_EXTENSIONS = [
    'extra',              # 包含 fenced_code (```), tables, footnotes
    'codehilite',         # 代码高亮 (必须安装 Pygments)
    'toc',                # 目录
    'admonition',         # 提示块
    'sane_lists',         # 更好的列表
    'pymdownx.tasklist',  # 任务列表支持 (- [ ])
    'pymdownx.tilde',     # [新增] 删除线支持 (~~text~~)
]

# 2. 扩展具体配置
MARKDOWN_EXTENSION_CONFIGS = {
    'toc': {
        'baselevel': 2,
        'anchorlink': True,
    },
    'codehilite': {
        'linenums': False,             
        'css_class': CODE_HIGHLIGHT_CLASS, # 强制指定类名为 'highlight'
        'use_pygments': True,          # 强制使用 Pygments
        'noclasses': False,            # ⭐ 关键修复：改为 False，使用 CSS 类而不是内联样式
        'guess_lang': True,            # 自动猜测语言
    },
    'pymdownx.tasklist': {
        'custom_checkbox': True,      # 允许使用 CSS 自定义样式
        'clickable_checkbox': False,  # 静态页面通常设为不可点击
    }
}
# --- Markdown 配置结束 ---


# --- 列表配置 ---
MAX_POSTS_ON_INDEX = 5 

# --- 目录和文件配置 ---
MARKDOWN_DIR = 'markdown'
BUILD_DIR = '_site'
POSTS_DIR_NAME = 'posts' 
TAGS_DIR_NAME = 'tags' 
STATIC_DIR = 'static'
MEDIA_DIR = 'media'

ABOUT_PAGE = 'about.md'

# 特殊文件名称
SITEMAP_FILE = 'sitemap.xml'
RSS_FILE = 'rss.xml'
ARCHIVE_FILE = 'archive.html' 
TAGS_LIST_FILE = 'tags.html'