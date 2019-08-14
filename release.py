#!/usr/bin/env python3

import json
from urllib.request import urlopen, Request
import random

class Cirrus:
    def __init__(self, token):
        self.token = token

    def graphql(self, query, variables):
        data = json.dumps({
            'query': query,
            'variables': variables,
        }).encode('ascii')
        headers = {
            'Authorization': 'Bearer ' + self.token,
        }

        request = Request('https://api.cirrus-ci.com/graphql', data=data, headers=headers)
        result = urlopen(request)
        text = result.read().decode()
        print(text)
        result_data = json.loads(text)
        return (result.status, result_data)

    latest_build_query = """
query GitHubRepositoryQuery(
  $owner: String!
  $name: String!
  $branch: String
) {
  githubRepository(owner: $owner, name: $name) {
    ...RepositoryBuildList_repository
    id
  }
}

fragment RepositoryBuildList_repository on Repository {
  id
  owner
  name
  masterBranch
  builds(last: 1, branch: $branch) {
    edges {
      node {
        id
        status
        tasks {
            id
            name
            status
        }
      }
    }
  }
}
"""

    def latest_build(self, owner, name, branch):
        variables = {'owner': owner, 'name': name, 'branch': branch}

        status, data = self.graphql(self.latest_build_query, variables)

        builds = data['data']['githubRepository']['builds']['edges']
        last_build = builds[0]['node']
        return last_build


    def build_task(self, build, task_name):
        tasks = filter(lambda x: x['name'] == task_name, build['tasks'])
        return list(tasks)[0]


    trigger_task_query = """
mutation TaskDetailsTriggerMutation($input: TaskTriggerInput!) {
  trigger(input: $input) {
    task {
      id
    }
  }
}
"""

    def trigger_task(self, task_id):
        variables = {
            'input': {
                'taskId': task_id,
            }
        }

        status, data = self.graphql(self.trigger_task_query, variables)

        return (status, data)


from pprint import pprint



with open('config.json') as f:
    config = json.load(f)
token = config['token']

cirrus = Cirrus(token)

build = cirrus.latest_build('duckinator', 'keress', 'test')
task_id = cirrus.build_task(build, 'nightly')['id']
print('task_id={}'.format(task_id))

status, data = cirrus.trigger_task(task_id)
print(status)
pprint(data)
