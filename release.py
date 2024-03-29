#!/usr/bin/env python3

import json
import logging
from pathlib import Path
from pprint import pprint
from sys import stdout
from urllib.request import urlopen, Request


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stdout))


class Cirrus:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = json.load(f)

        self.token = self.config['token']

    def _graphql_query(self, query_name):
        data_dir = Path(__file__).resolve().parent
        query_file = data_dir / 'graphql-queries' / '{}.graphql'.format(query_name)
        return query_file.read_text()

    def graphql(self, query_name, variables):
        query = self._graphql_query(query_name)

        data = json.dumps({
            'query': query,
            'variables': variables,
        }, indent=4).encode('ascii')
        headers = {
            'Authorization': 'Bearer ' + self.token,
        }

        request = Request('https://api.cirrus-ci.com/graphql', data=data, headers=headers)
        result = urlopen(request)
        text = result.read().decode()
        result_data = json.loads(text)

        return (result.status, result_data)

    def latest_build(self, owner, name, branch):
        variables = {'owner': owner, 'name': name, 'branch': branch}

        status, data = self.graphql('latest-build', variables)

        builds = data['data']['githubRepository']['builds']['edges']
        last_build = builds[0]['node']
        return last_build

    def find_task(self, build, task_name):
        tasks = filter(lambda x: x['name'] == task_name, build['tasks'])
        return list(tasks)[0]

    def trigger_task(self, task_id):
        variables = {
            'input': {
                'taskId': task_id,
                'clientMutationId': 'rerun-' + task_id,
            }
        }

        status, data = self.graphql('trigger-task', variables)

        return (status, data)


repo_dir = Path(__file__).resolve().parent
cirrus = Cirrus(repo_dir / 'config.json')

for task in cirrus.config['tasks']:
    logger.info('Running {} task for {}.'.format(task['task'], task['repo']))

    user, repo = task['repo'].split('/')
    branch = task['branch']
    task_name = task['task']

    build = cirrus.latest_build(user, repo, task['branch'])
    task_id = cirrus.find_task(build, task_name)['id']

    status, data = cirrus.trigger_task(task_id)
    if 'errors' in data:
        logger.info('')
        for error in data['errors']:
            logger.error(error['message'] + '\n')
            pprint(data)
