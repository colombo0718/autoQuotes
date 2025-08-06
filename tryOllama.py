import requests
response = requests.post('http://localhost:11434/api/generate', json={
    # 'model': 'deepseek-r1:14b',
    'model': 'gemma3:12b',
    'prompt': '你好，今天天氣如何？  用繁體中文回答',
    'stream': False
})
print(response.json()['response'])