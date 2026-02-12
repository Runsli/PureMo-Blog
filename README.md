# 🌟 PureMo-Blog 是什么

回归极简的 Python 静态博客框架 

PureMo-Blog 是一款为开发者和创作者量身打造的 Python 静态网站生成器。旨在让你摆脱复杂的配置，重新回归创作本身。 

🎬 **在线演示**：[Vercel Pages](https://PureMo-Blog.vercel.app)

## ✨ 主要特性
- 极速生成 (Blazing Fast): 基于 Python 异步架构优化，即便有数百篇博文，也能在毫秒级完成构建。
- 原生支持 Python 生态: 完美集成 Jinja2 模板引擎与 Pygments 代码高亮，你可以利用熟悉的 Python 脚本扩展插件。
- SEO 与性能巅峰: 零 JavaScript 依赖（可选），生成符合 100 分 Lighthouse 评分的纯 HTML/CSS 页面。
- 自动化流水线: 一键部署至 GitHub Pages、Vercel 或 Cloudflare Pages，自带敏捷的热重载预览功能。


# 🛠️ 快速上手
你需要安装 Python 和依赖后才能正常使用这个项目，Python 3.7+ 是正常运行这个项目所必须的。 
## 📋 使用方法
1. [使用此模板](https://github.com/new?template_name=PureMo-Blog&template_owner=Runsil)创建新的仓库或 [Fork](https://github.com/Runsli/PureMo-Blog/fork) 此仓库。
2. 运行如下命令进入到项目目录：
下面这条命令需要你的电脑安装 Git 后才能正常使用。
```sh
git clone <your-repo-url>
cd <your-repo-name>
```
3. 运行如下命令安装依赖：
```sh
pip install -r requirements.txt
```
4. 确保项目目录结构如下:
```
PureMo-Blog/
├── assets/
│   └── style.css           # CSS 样式文件
├── markdown/               # Markdown 文章目录
├── static/                 # 静态资源目录
│   ├── logo.png
│   └── default-cover.png
├── templates/              # HTML 模板目录
│   └── base.html
├── config.py               # 配置文件
├── parser.py               # 解析器
├── generator.py            # 生成器
├── autobuild.py            # 自动构建脚本
└── requirements.txt        # 依赖文件
```
5. 编辑 `config.py` 文件，根据实际情况修改：
- 具体的修改建议提示已经体现在`config.py` 文件注释当中，可以根据需要调整
6. 📝 如何创建新的文章？
创建新的 Markdown 文件，并保存在 `markdown/` 目录下。确保文件名以 `.md` 结尾。 
以下面的格式为例：
```md

---
title: "Hello World" # 这里的标题主要显示在网站内容里
date: 2026-01-01 # 这里主要是网页内容区域上面显示的发布时间
summary: 简介，主要显示在博客列表里面，在列表里显示的文章概述
tags: [python, blog] # 这里是文章的标签，用于分类
---

下面是正文，这里可以写 Markdown 格式的内容
```
7. 🔧 如何生成静态页面？ 

运行自动构建脚本：

```bash
python autobuild.py
```
8. 👀 如何本地预览？ 

- 方法1. 使用 Python 运行服务器：
```bash
cd _site
python -m http.server 8000
```
 
- 方法2. 使用 VSCode 的 Live Server 插件 

如果你使用 VS Code，可以安装 `Live Server` 扩展，右键点击 `_site/index`.html 选择 "Open with Live Server" 

# 🔧 进行其他修改 

## 🎨 修改样式
1. 编辑 `assets/style.css`
2. 运行 `python autobuild.py` 重新生成
3. 刷新浏览器查看样式变化
## 🧩 修改模板
1. 编辑 `templates/base.html`
2. 运行 `python autobuild.py` 重新生成
3. 刷新浏览器查看模板变化

# 🚀 部署
你可以通过下方的按钮进行一键部署： 

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Runsli/PureMo-Blog)
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/Runsli/PureMo-Blog) 

部署完成后，你需要将 `config.py` 文件中的 `BASE_URL` 修改为实际访问链接，否则可能会出现 css 样式加载异常或其他问题
# 🔍 常见问题排查

如果遇到问题，可以检查： 

- 检查 Python 环境是否正确安装
- 检查项目依赖文件是否正确
- 检查项目目录结构是否正确
- 检查 Markdown 文件格式是否正确
- 检查 Markdown 文件编码是否正确
# 🛠️ 如何贡献？
1. Fork 这个项目
2. 创建一个分支
3. 提交你的修改
4. 创建一个 Pull Request
# 📜 许可协议
本项目遵循 [MIT 许可协议](https://opensource.org/licenses/MIT)