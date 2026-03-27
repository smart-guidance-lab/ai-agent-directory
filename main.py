import os
import requests
from openai import OpenAI
import json
from datetime import datetime

# --- Config ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
BASE_URL = "https://ai-agent-directory-woad.vercel.app" 
# --------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    # トピックを広げ、より「次世代感」のあるリポジトリを取得
    url = "https://api.github.com/search/repositories?q=topic:llm-agent+stars:>500&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_content(repo):
    # SEOに強いメタ情報を生成させるプロンプトへ進化
    prompt = f"Analyze: {repo['name']}. Write a 1-sentence SEO summary and a professional ROI report. English."
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

# 1. 記事生成
projects = get_ai_projects()
post_data = [] # JSONに詳細情報を入れる
os.makedirs("posts", exist_ok=True)
current_date = datetime.now().strftime('%Y-%m-%d')

for p in projects:
    name = p['name']
    filename = f"posts/{name}.md"
    content = generate_content(p)
    
    # 常に最新の情報を上書きし、鮮度を保つ（ループ脱出のための積極的更新）
    footer = f"\n\n---\n[🚀 Feature your tool]({STRIPE_LINK}) | [Source]({p['html_url']})"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {name}\nPublished: {current_date}\n\n" + content + footer)
    
    post_data.append({"name": name, "date": current_date})

# 2. JSON更新（フロントエンドでの表示用）
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(post_data, f, ensure_ascii=False, indent=4)

# 3. サイトマップ（極限までシンプルに。エラーを誘発する余計なタグを排除）
sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
sitemap += f'<url><loc>{BASE_URL}/</loc><lastmod>{current_date}</lastmod></url>'
for post in post_data:
    sitemap += f'<url><loc>{BASE_URL}/posts/{post["name"]}.md</loc><lastmod>{post["date"]}</lastmod></url>'
sitemap += '</urlset>'

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap)
