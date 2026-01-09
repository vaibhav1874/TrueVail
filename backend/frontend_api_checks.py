import requests, json

end = 'http://127.0.0.1:5001/analyze'
cases = [
    {'text':'Breaking: unbelievable event just happened!!!','type':'news'},
    {'text':'https://example.com/news/article-123','type':'news'},
    {'text':'The user email is test@example.com and phone 555-1234','type':'privacy'},
    {'text':'suspected_deepfake_video_ai_generated.mp4','type':'deepfake'}
]

for c in cases:
    try:
        r = requests.post(end, json=c, timeout=10)
        print('REQUEST:', c)
        print('STATUS:', r.status_code)
        print(json.dumps(r.json(), indent=2))
        print('-'*60)
    except Exception as e:
        print('ERROR for', c, e)
        print('-'*60)
