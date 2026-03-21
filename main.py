import os
import requests
from openai import OpenAI
from datetime import datetime

# --- 設定（ここを自分のStripeリンクに書き換えてください） ---
STRIPE_LINK = "https://buy.stripe.com/aFafZgepV8NW7Cwc788so07" 
# --------------------------------------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_projects():
    # トレンドのAIエージェントを取得
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    res = requests.get(url).json()
    return res.get('items', [])[:5] # 1日5件に拡大

def generate_content(repo):
    # SEOと読者利益を最大化するプロンプト
    prompt = f"""
    Analyze this GitHub project and create a professional review in English for a business audience.
    Name: {repo['name']}
    URL: {repo['html_url']}
    Description: {repo['description']}
    
    Structure:
    1. Catchy Title (H1)
    2. Executive Summary (Why this matters?)
    3. Key Features (Bullet points)
    4. Target Audience
    5. How to Get Started (Simple steps)
    
    Requirement: Use Markdown, SEO friendly keywords, and be concise.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def update_sitemap(filenames):
    # Google Search Console用の簡易インデックスページ(README.md)を作成
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# Global AI Agent Directory\n\n")
        f.write("Daily updated directory of the most powerful AI Agents on GitHub.\n\n")
        f.write("## Newest Agents\n")
        for name in filenames:
            f.write(f"- [{name}](./posts/{name}.md)\n")
        f.write(f"\n\n---\n[🚀 Want to feature your tool here? Click here to Promote for $49]({STRIPE_LINK})")

# メイン実行部
projects = get_ai_projects()
processed_names = []

os.makedirs("posts", exist_ok=True)

for p in projects:
    name = p['name']
    content = generate_content(p)
    
    # 記事の下にStripeリンクを自動挿入
    footer = f"\n\n---\n### 📢 Support & Promotion\n- [Promote your AI tool on this page]({STRIPE_LINK})\n- [Original Source]({p['html_url']})"
    
    with open(f"posts/{name}.md", "w", encoding="utf-8") as f:
        f.write(content + footer)
    processed_names.append(name)

# 全記事のリストをトップページに反映（簡易SEO対策）
update_sitemap(os.listdir("posts"))
