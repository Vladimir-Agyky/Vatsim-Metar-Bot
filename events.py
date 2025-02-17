import requests

url = "https://my.vatsim.net/api/v2/events/latest"

payload={}
headers = {
  'Accept': 'application/json'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)