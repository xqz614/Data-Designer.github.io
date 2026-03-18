#!/usr/bin/env python3
"""
arXiv 论文获取脚本 - Data-Designer.github.io
每天定时更新各研究方向的最新论文（每个方向50篇）
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import time
from datetime import datetime
from pathlib import Path

# 研究方向配置 - 来自 index.html 的 Research Keywords
RESEARCH_KEYWORDS = [
    {
        "name": "AI for Healthcare",
        "slug": "ai-for-healthcare",
        "arxiv_query": "all:AI for healthcare OR all:medical AI OR all:clinical AI OR all:health informatics",
        "desc": "人工智能在医疗健康领域的应用研究"
    },
    {
        "name": "Generative Recommendation",
        "slug": "generative-recommendation",
        "arxiv_query": "all:generative recommendation OR all:LLM recommendation OR all:conversational recommendation",
        "desc": "生成式推荐系统研究"
    },
    {
        "name": "AI for Marketing",
        "slug": "ai-for-marketing",
        "arxiv_query": "all:AI for marketing OR all:computational marketing OR all:marketing analytics OR all:customer analytics",
        "desc": "人工智能在市场营销领域的应用研究"
    },
    {
        "name": "Heterogeneous Graph",
        "slug": "heterogeneous-graph",
        "arxiv_query": "all:heterogeneous graph OR all:HIN OR all:heterogeneous information network OR all:heterogeneous network",
        "desc": "异构图神经网络研究"
    },
    {
        "name": "LLM Reasoning",
        "slug": "llm-reasoning",
        "arxiv_query": "all:LLM reasoning OR all:language model reasoning OR all:chain of thought OR all:CoT",
        "desc": "大语言模型推理能力研究"
    },
    {
        "name": "Agent Evolving",
        "slug": "agent-evolving",
        "arxiv_query": "all:LLM agent OR all:autonomous agent OR all:agent learning OR all:multi-agent",
        "desc": "智能体演化与学习研究"
    },
    {
        "name": "Reinforced Learning",
        "slug": "reinforced-learning",
        "arxiv_query": "all:reinforcement learning OR all:RLHF OR all:PPO OR all:reward learning",
        "desc": "强化学习与人类反馈研究"
    },
    {
        "name": "Retrieval-augmented Generation",
        "slug": "rag",
        "arxiv_query": "all:RAG OR all:retrieval augmented generation OR all:retrieval-augmented OR all:retrieval generation",
        "desc": "检索增强生成研究"
    }
]

# 获取脚本目录
SCRIPT_DIR = Path(__file__).parent.absolute()

def fetch_arxiv_papers(query, max_results=50):
    """从 arXiv API 获取论文"""
    base_url = "http://export.arxiv.org/api/query?"
    all_papers = []
    batch_size = 100
    start = 0
    
    while len(all_papers) < max_results:
        params = {
            "search_query": query,
            "start": start,
            "max_results": min(batch_size, max_results - len(all_papers)),
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        url = base_url + urllib.parse.urlencode(params)
        
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                xml_data = response.read().decode('utf-8')
            
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
            
            count = 0
            for entry in root.findall('atom:entry', ns):
                paper = {
                    'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                    'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
                    'summary': entry.find('atom:summary', ns).text.strip()[:400] + '...',
                    'published': entry.find('atom:published', ns).text[:10],
                    'link': entry.find('atom:id', ns).text,
                    'pdf': None
                }
                
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        paper['pdf'] = link.get('href')
                
                all_papers.append(paper)
                count += 1
            
            if count == 0:
                break
                
            start += batch_size
            time.sleep(3)
            
        except Exception as e:
            print(f"获取论文失败: {e}")
            break
    
    return all_papers[:max_results]

def generate_html(keyword_data, papers):
    """生成子页面 HTML"""
    
    name = keyword_data['name']
    slug = keyword_data['slug']
    desc = keyword_data['desc']
    today = datetime.now().strftime('%Y-%m-%d')
    
    papers_html = ""
    for i, paper in enumerate(papers, 1):
        authors_str = ', '.join(paper['authors'][:3])
        if len(paper['authors']) > 3:
            authors_str += f" et al. ({len(paper['authors'])} authors)"
        
        papers_html += f'''
    <div class="paper-card">
      <div class="paper-number">{i}</div>
      <div class="paper-content">
        <a href="{paper['link']}" target="_blank" class="paper-title">{paper['title']}</a>
        <div class="paper-authors">{authors_str}</div>
        <div class="paper-date">📅 {paper['published']}</div>
        <div class="paper-abstract">{paper['summary']}</div>
        <div class="paper-links">
          <a href="{paper['link']}" target="_blank" class="paper-link">arXiv →</a>
          {f'<a href="{paper["pdf"]}" target="_blank" class="paper-link">PDF</a>' if paper['pdf'] else ''}
        </div>
      </div>
    </div>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} - Latest arXiv Papers</title>
  <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --bg-primary: #ffffff;
      --bg-secondary: #f8f9fa;
      --bg-tertiary: #e9ecef;
      --primary: #003366;
      --secondary: #0059b3;
      --accent: #0077b6;
      --text-primary: #333333;
      --text-secondary: #666666;
      --text-tertiary: #888888;
      --border-light: #dee2e6;
      --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
      --shadow-md: 0 4px 8px rgba(0,0,0,0.1);
      --radius-sm: 4px;
      --radius-md: 8px;
    }}
    
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    body {{
      font-family: 'Source Serif 4', Georgia, serif;
      font-size: 16px;
      line-height: 1.6;
      color: var(--text-primary);
      background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
      min-height: 100vh;
      padding: 40px 20px;
    }}
    
    .container {{
      max-width: 900px;
      margin: 0 auto;
    }}
    
    .header {{
      text-align: center;
      margin-bottom: 3rem;
    }}
    
    .back-link {{
      display: inline-block;
      color: var(--secondary);
      text-decoration: none;
      margin-bottom: 1rem;
      font-size: 0.9rem;
    }}
    
    .back-link:hover {{ text-decoration: underline; }}
    
    h1 {{
      font-size: 2.2rem;
      color: var(--primary);
      margin-bottom: 0.5rem;
    }}
    
    .subtitle {{
      color: var(--text-secondary);
      font-size: 1.1rem;
      margin-bottom: 1rem;
    }}
    
    .stats {{
      display: flex;
      justify-content: center;
      gap: 2rem;
      margin-bottom: 1rem;
    }}
    
    .stat {{
      background: var(--bg-secondary);
      padding: 0.5rem 1rem;
      border-radius: var(--radius-md);
      font-size: 0.9rem;
      color: var(--text-tertiary);
    }}
    
    .paper-card {{
      background: var(--bg-primary);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-sm);
      margin-bottom: 1.5rem;
      padding: 1.5rem;
      display: flex;
      gap: 1rem;
      border: 1px solid var(--border-light);
      transition: box-shadow 0.2s ease;
    }}
    
    .paper-card:hover {{
      box-shadow: var(--shadow-md);
    }}
    
    .paper-number {{
      flex: 0 0 40px;
      width: 40px;
      height: 40px;
      background: var(--primary);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 1.1rem;
    }}
    
    .paper-content {{
      flex: 1;
    }}
    
    .paper-title {{
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
      font-size: 1.1rem;
      line-height: 1.4;
      display: block;
      margin-bottom: 0.5rem;
    }}
    
    .paper-title:hover {{ text-decoration: underline; }}
    
    .paper-authors {{
      color: var(--text-secondary);
      font-size: 0.9rem;
      margin-bottom: 0.25rem;
    }}
    
    .paper-date {{
      color: var(--text-tertiary);
      font-size: 0.85rem;
      margin-bottom: 0.75rem;
    }}
    
    .paper-abstract {{
      color: var(--text-secondary);
      font-size: 0.95rem;
      line-height: 1.6;
      margin-bottom: 0.75rem;
      padding: 0.75rem;
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      border-left: 3px solid var(--accent);
    }}
    
    .paper-links {{
      display: flex;
      gap: 1rem;
    }}
    
    .paper-link {{
      color: var(--secondary);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
    }}
    
    .paper-link:hover {{ text-decoration: underline; }}
    
    .footer {{
      text-align: center;
      margin-top: 3rem;
      padding-top: 2rem;
      border-top: 1px solid var(--border-light);
      color: var(--text-tertiary);
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <a href="index.html" class="back-link">← Back to Homepage</a>
      <h1>{name}</h1>
      <p class="subtitle">{desc}</p>
      <div class="stats">
        <span class="stat">📊 {len(papers)} Papers</span>
        <span class="stat">📅 Updated: {today}</span>
      </div>
    </div>
    
    <div class="papers-list">
{papers_html if papers else '<div class="no-papers" style="text-align:center;padding:3rem;color:var(--text-tertiary);">No papers found</div>'}
    </div>
    
    <div class="footer">
      <p>Auto-generated from arXiv API | <a href="index.html">Chuang Zhao</a></p>
    </div>
  </div>
</body>
</html>'''
    
    return html

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取 arXiv 论文...")
    
    for i, keyword in enumerate(RESEARCH_KEYWORDS):
        print(f"\n处理: {keyword['name']}")
        
        papers = fetch_arxiv_papers(keyword['arxiv_query'], max_results=50)
        print(f"  获取到 {len(papers)} 篇论文")
        
        html = generate_html(keyword, papers)
        
        output_path = SCRIPT_DIR / f"{keyword['slug']}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  已保存: {output_path}")
        
        if i < len(RESEARCH_KEYWORDS) - 1:
            print("  等待 5 秒...")
            time.sleep(5)
    
    meta = {
        'last_update': datetime.now().isoformat(),
        'keywords': [k['name'] for k in RESEARCH_KEYWORDS]
    }
    with open(SCRIPT_DIR / 'arxiv_meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完成! 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
