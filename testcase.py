#!/usr/bin/env python3

# NOTE: Before running this, put a Cirrus CI API token in ./token.txt

import json
from urllib.request import urlopen, Request
from pathlib import Path

token = Path('token.txt').read_text().strip()

query = """
mutation TaskDetailsTriggerMutation($input: TaskTriggerInput!) {
  trigger(input: $input) {
    task {
      id
    }
  }
}
"""

variables = {
    'input': {
        # https://cirrus-ci.com/task/5136260581031936
        'taskId': '5136260581031936',
    }
}

req_data = json.dumps({
    'query': query,
    'variables': variables,
}).encode('ascii')

headers = {
    'Authorization': 'Bearer ' + token,
}

request = Request('https://api.cirrus-ci.com/graphql', data=req_data, headers=headers)
result = urlopen(request)
text = result.read().decode()
print(result.status)
print(text)
