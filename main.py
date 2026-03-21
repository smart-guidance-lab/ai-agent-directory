import os
import requests
from openai import OpenAI

# 1. 初期設定
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # 自動付与される

def get_ai_projects():
    # GitHubから「AI Agent」関連のトレンドリポジトリを検索
    url = "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&order=desc"
    res = requests.get(url).json()
    return res.get('items', [])[:3] # 1日3件に絞りコスト節約

def summarize_project(repo):
    prompt = f"Summarize this GitHub project for a business audience in English. Name: {repo['name']}, Description: {repo['description']}. Focus on: 1. Value Proposition, 2. Target User, 3. Ease of Setup. Format: Markdown."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# メイン処理
projects = get_ai_projects()
for p in projects:
    summary = summarize_project(p)
    filename = f"posts/{p['name']}.md"
    os.makedirs("posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {p['name']}\n\nSource: {p['html_url']}\n\n{summary}")
