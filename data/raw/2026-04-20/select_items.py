import json, sys

with open(sys.argv[1]) as f:
    data = json.load(f)

selected = []
seen_ids = set()

def pick(item):
    if item['id'] not in seen_ids:
        seen_ids.add(item['id'])
        selected.append(item)

def find(category=None, **kwargs):
    results = []
    for item in data:
        if category and item['category'] != category:
            continue
        match = True
        for k, v in kwargs.items():
            if k == 'title_contains':
                if v.lower() not in item['title'].lower():
                    match = False
            elif k == 'source_is':
                if item.get('source') != v:
                    match = False
        if match:
            results.append(item)
    return results

# === MAJOR-RELEASE (pick 10) ===
cat = 'major-release'

# 1. Claude Opus 4.7 (multi-source)
for i in find(cat, title_contains='Opus 4.7'):
    if i.get('source_count',1) >= 2:
        pick(i); break

# 2. Gemini 3.1 Flash TTS (multi-source)
for i in find(cat, title_contains='Flash TTS'):
    if i.get('source_count',1) >= 2:
        pick(i); break

# 3. Claude Design
for i in find(cat, title_contains='Claude Design', source_is='anthropic-news'):
    pick(i); break

# 4. Qwen3.6-35B
for i in find(cat, title_contains='Qwen3.6'):
    if 'ai-bot-daily-news' in i.get('sources', []):
        pick(i); break

# 5. Microsoft foundation models
for i in find(cat, title_contains='Microsoft launches'):
    pick(i); break

# 6. DeepSeek融资
for i in find(cat, title_contains='DeepSeek'):
    if '融资' in i['title']:
        pick(i); break

# 7. SAM 3.1
for i in find(cat, title_contains='SAM 3.1'):
    pick(i); break

# 8. Gemini Robotics-ER
for i in find(cat, title_contains='Gemini Robotics'):
    pick(i); break

# 9. Codex upgrade (OpenAI blog)
for i in find(cat, title_contains='Codex for', source_is='openai-blog'):
    pick(i); break

# 10. 腾讯混元3D
for i in find(cat, title_contains='混元3D'):
    pick(i); break

# === INDUSTRY-BUSINESS (pick 8) ===
cat = 'industry-business'

# 1. Cursor融资 
for i in find(cat, title_contains='Cursor'):
    pick(i); break

# 2. DeepSeek融资
for i in find(cat, title_contains='DeepSeek'):
    if '融资' in i['title']:
        pick(i); break

# 3. Anthropic $30B Series G
for i in find(cat, title_contains='Anthropic raises'):
    pick(i); break

# 4. Shield AI融资20亿
for i in find(cat, title_contains='Shield AI'):
    if i.get('language') == 'zh':
        pick(i); break

# 5. 生数科技 B轮融资
for i in find(cat, title_contains='生数科技'):
    pick(i); break

# 6. OpenAI existential questions
for i in find(cat, title_contains="OpenAI"):
    if 'existential' in i['title'].lower():
        pick(i); break

# 7. Anthropic-Trump thawing
for i in find(cat, title_contains='Anthropic'):
    if 'Trump' in i['title'] or 'thawing' in i['title']:
        pick(i); break

# 8. Google AI Mode in Chrome
for i in find(cat, title_contains='AI Mode'):
    pick(i); break

# === RESEARCH-FRONTIER (all 8) ===
cat = 'research-frontier'
for i in find(cat):
    pick(i)

# === TOOLS-RELEASE (pick 8) ===
cat = 'tools-release'

# 1. World Labs Spark 2.0
for i in find(cat, title_contains='World Labs'):
    pick(i); break

# 2. Voicebox
for i in find(cat, title_contains='Voicebox'):
    pick(i); break

# 3. Project Glasswing (Anthropic)
for i in find(cat, title_contains='Glasswing'):
    pick(i); break

# 4. ERNIE-Image (百度)
for i in find(cat, title_contains='ERNIE-Image'):
    pick(i); break

# 5. Audio Flamingo (Nvidia)
for i in find(cat, title_contains='Audio Flamingo'):
    pick(i); break

# 6. LingBot-Map (蚂蚁)
for i in find(cat, title_contains='LingBot'):
    pick(i); break

# 7. MIA memory agent
for i in find(cat, title_contains='记忆智能体'):
    pick(i); break

# 8. Chrome prompt tools
for i in find(cat, title_contains='prompts into'):
    pick(i); break

# === POLICY-REGULATION (pick 6) ===
cat = 'policy-regulation'

# 1. White House AI Policy Framework
for i in find(cat):
    if 'White House' in i['title'] and 'Framework' in i['title']:
        pick(i); break

# 2. 特朗普AI政策
for i in find(cat, title_contains='特朗普'):
    if '政策' in i['title']:
        pick(i); break

# 3. AI governance 19 bills
for i in find(cat, title_contains='Nineteen'):
    pick(i); break

# 4. 防止偏见歧视
for i in find(cat, title_contains='偏见歧视'):
    pick(i); break

# 5. 南非AI政策
for i in find(cat, title_contains='南非'):
    pick(i); break

# 6. Microsoft $5.5B Singapore
for i in find(cat, title_contains='Microsoft invests'):
    pick(i); break

# Output results
cats_count = {}
for item in selected:
    c = item['category']
    cats_count[c] = cats_count.get(c, 0) + 1

all_sources = set()
for item in selected:
    for s in item.get('sources', []):
        all_sources.add(s)

print(f'Total selected: {len(selected)}', file=sys.stderr)
for c, n in sorted(cats_count.items()):
    print(f'  {c}: {n}', file=sys.stderr)
print(f'Unique sources: {len(all_sources)}', file=sys.stderr)
print(f'Sources: {sorted(all_sources)}', file=sys.stderr)

json.dump(selected, sys.stdout, ensure_ascii=False, indent=2)
