import os
import requests
from openai import OpenAI
import json

# --- ユーザー設定エリア ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
BASE_URL = "https://ai-agent-directory-woad.vercel.app/" # 自分のVercel URLを確認
# ------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_content(repo):
    prompt = f"Write a professional analysis of the AI project: {repo['name']}. URL: {repo['html_url']}. Focus on Business Impact and ROI. Format: Markdown."
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
        footer = f"\n\n---\n[🚀 Promote your tool]({STRIPE_LINK}) | [Source]({p['html_url']})"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content + footer)
    post_list.append(name)

# 2. JSON更新
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_list, f, ensure_ascii=False, indent=4)

# 3. サイトマップ修正（正しいXML構造）
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
# トップページ
sitemap_content += f'  <url><loc>{BASE_URL}/</loc></url>\n'
# 各記事
for name in post_list:
    # URLの末尾が.mdでもVercelは表示可能ですが、index.html経由で呼ぶならパスを正規化
    sitemap_content += f'  <url><loc>{BASE_URL}/posts/{name}.md</loc></url>\n'
sitemap_content += '</urlset>'

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_content)
