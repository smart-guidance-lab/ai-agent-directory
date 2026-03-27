import os
import requests
from openai import OpenAI
import json
from datetime import datetime

# --- Config（要書き換え） ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" # ユーザー提供のリンク
BASE_URL = "https://ai-agent-directory-woad.vercel.app" 
# -------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_content(repo):
    prompt = f"Analyze AI project: {repo['name']}. Source: {repo['html_url']}. ROI focused."
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

# 1. コンテンツ生成
projects = get_ai_projects()
post_list = []
os.makedirs("posts", exist_ok=True)
current_date = datetime.now().strftime('%Y-%m-%d')

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    if not os.path.exists(filename):
        content = generate_content(p)
        footer = f"\n\n---\n[🚀 Promote your tool]({STRIPE_LINK}) | [Source]({p['html_url']})"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content + footer)
    post_list.append(name)

# 2. JSON更新
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_list, f, ensure_ascii=False, indent=4)

# 3. サイトマップ生成（Googleのキャッシュを回避するため別名で保存）
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

# トップページ
sitemap_xml += '  <url>\n'
sitemap_xml += f'    <loc>{BASE_URL}/</loc>\n'
sitemap_xml += f'    <lastmod>{current_date}</lastmod>\n'
sitemap_xml += '    <changefreq>daily</changefreq>\n'
sitemap_xml += '    <priority>1.0</priority>\n'
sitemap_xml += '  </url>\n'

# 各記事
for name in post_list:
    page_url = f"{BASE_URL}/posts/{name}.md"
    sitemap_xml += '  <url>\n'
    sitemap_xml += f'    <loc>{page_url}</loc>\n'
    sitemap_xml += f'    <lastmod>{current_date}</lastmod>\n'
    sitemap_xml += '    <changefreq>weekly</changefreq>\n'
    sitemap_xml += '    <priority>0.8</priority>\n'
    sitemap_xml += '  </url>\n'

sitemap_xml += '</urlset>'

# ファイル名をsitemap_v1.xmlに変更（旧キャッシュのバイパス）
with open("sitemap_v1.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)
