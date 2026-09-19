import json

import requests

# Only todos belonging to user 1
response = requests.get(
    "https://jsonplaceholder.typicode.com/todos", params={"userId": 1}
)
print(json.dumps(response.json(), indent=2))
