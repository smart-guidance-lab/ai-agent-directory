import os
import requests
from openai import OpenAI
import json

# --- ユーザー設定エリア ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
BASE_URL = "https://ai-agent-directory-woad.vercel.app"
# ------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_content(repo):
    prompt = f"Write a professional deep-dive on: {repo['name']}. Source: {repo['html_url']}. ROI focused. English."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 1. コンテンツ生成
projects = get_ai_projects()
post_list = []
os.makedirs("posts", exist_ok=True)

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

# 3. サイトマップ修正（Google Search Console完全準拠構造）
# <urlset> 親タグの中に、<url> タグがあり、その中に <loc> タグがある構造にする
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

# トップページの登録
sitemap_content += f'  <url>\n    <loc>{BASE_URL}/</loc>\n  </url>\n'

# 各記事ページの登録
for name in post_list:
    # URLにスペースや特殊文字が含まれる可能性を考慮し、パスを安全に結合
    page_url = f"{BASE_URL}/posts/{name}.md"
    sitemap_content += f'  <url>\n    <loc>{page_url}</loc>\n  </url>\n'

sitemap_content += '</urlset>'

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_content)
