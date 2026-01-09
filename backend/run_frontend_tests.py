import requests, json

r = requests.post('http://127.0.0.1:5001/analyze', json={'text':'Breaking: unbelievable event just happened!!!','type':'news'})
print('NEWS', r.status_code)
print(json.dumps(r.json(), indent=2))

r2 = requests.post('http://127.0.0.1:5001/analyze', json={'text':'suspected_deepfake_video_ai_generated.mp4','type':'deepfake'})
print('\nDEEPFAKE', r2.status_code)
print(json.dumps(r2.json(), indent=2))
