import os
import requests
from openai import OpenAI
import json

# --- 設定 ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" # 自分のリンクに！
# ------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    # トレンドのAIエージェントを取得
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    res = requests.get(url, headers=headers).json()
    return res.get('items', [])[:5]

def generate_content(repo):
    prompt = f"""
    Create a professional, SEO-optimized review for this AI project: {repo['name']}. 
    Description: {repo['description']}. URL: {repo['html_url']}.
    Output in Markdown with clear sections: # Title, ## Overview, ## Use Cases, ## Key Features.
    Make it sound like a tech expert's analysis.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def update_directory_data(posts):
    # index.htmlが読み込むためのデータファイルをJSONで作成
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

def generate_sitemap(posts):
    # Googlebot用のサイトマップをXML形式で自動生成
    base_url = "https://your-vercel-domain.vercel.app" # 自分のVercel URLに！
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in posts:
        sitemap += f"  <url><loc>{base_url}/posts/{p}.md</loc></url>\n"
    sitemap += "</urlset>"
    with open("sitemap.xml", "w") as f:
        f.write(sitemap)

# メイン実行
projects = get_ai_projects()
post_list = []
os.makedirs("posts", exist_ok=True)

for p in projects:
    name = p['name']
    content = generate_content(p)
    footer = f"\n\n---\n[🚀 Promote your AI tool here]({STRIPE_LINK}) | [Source Code]({p['html_url']})"
    
    with open(f"posts/{name}.md", "w", encoding="utf-8") as f:
        f.write(content + footer)
    post_list.append(name)

update_directory_data(post_list)
generate_sitemap(post_list)

# READMEも更新（GitHubからのSEO流入用）
with open("README.md", "w", encoding="utf-8") as f:
    f.write(f"# Global AI Agent Directory\n\nLatest tools updated daily.\n\n")
    for name in post_list:
        f.write(f"- [{name}](./posts/{name}.md)\n")
    f.write(f"\n\n---\n[📢 Featured Listing]({STRIPE_LINK})")
