import requests

url = "http://192.168.31.147:7860/api/v1/asr"

files = [
    ('files', ('audio1.wav', open('audio1.wav', 'rb'), 'audio/wav'))
]

data = {
    'keys': 'audio1',
    'lang': 'auto'  
}

response = requests.post(url, files=files, data=data)
print(response.json())