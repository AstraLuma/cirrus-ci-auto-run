#!/usr/bin/env python3

import json
from pathlib import Path
from urllib.request import urlopen, Request
import random

class Cirrus:
    def __init__(self, config):
        self.config = config
        self.token = config['token']

    def _graphql_query(self, query_name):
        data_dir = Path(__file__).resolve().parent
        query_file = data_dir / 'graphql-queries' / '{}.graphql'.format(query_name)
        return query_file.read_text()

    def graphql(self, query_name, variables):
        query = self._graphql_query(query_name)

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

    def latest_build(self, owner, name, branch):
        variables = {'owner': owner, 'name': name, 'branch': branch}

        status, data = self.graphql('latest-build', variables)

        builds = data['data']['githubRepository']['builds']['edges']
        last_build = builds[0]['node']
        return last_build

    def build_task(self, build, task_name):
        tasks = filter(lambda x: x['name'] == task_name, build['tasks'])
        return list(tasks)[0]

    def trigger_task(self, task_id):
        variables = {
            'input': {
                'taskId': task_id,
            }
        }

        status, data = self.graphql('trigger-task', variables)

        return (status, data)


from pprint import pprint



with open('config.json') as f:
    config = json.load(f)

cirrus = Cirrus(config)

build = cirrus.latest_build('duckinator', 'keress', 'test')
task_id = cirrus.build_task(build, 'nightly')['id']
print('task_id={}'.format(task_id))

status, data = cirrus.trigger_task(task_id)
print(status)
pprint(data)
