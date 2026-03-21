import os
import requests
from openai import OpenAI
import json
from datetime import datetime

# --- Config（要書き換え） ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
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
        footer = f"\n\n---\n[🚀 Feature your tool]({STRIPE_LINK}) | [Source]({p['html_url']})"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content + footer)
    post_list.append(name)

# 2. JSON更新
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_list, f, ensure_ascii=False, indent=4)

# 3. サイトマップ生成（Googleのキャッシュを回避するため別名で保存）
# XMLヘッダーとurlsetタグの間に改行を入れず、パースミスを最小化する
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

# トップページ
sitemap_xml += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>'

# 各記事
for name in post_list:
    page_url = f"{BASE_URL}/posts/{name}.md"
    sitemap_xml += f'<url><loc>{page_url}</loc><lastmod>{current_date}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>'

sitemap_xml += '</urlset>'

# ファイル名をsitemap_v1.xmlに変更（旧ファイルのキャッシュを捨てる）
with open("sitemap_v1.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)
