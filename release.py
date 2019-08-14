#!/usr/bin/env python3

from __future__ import absolute_import
import json
from logging import getLogger, INFO, StreamHandler
from sys import stdout
from pathlib import Path
from urllib.request import urlopen, Request
from pprint import pprint
import random


logger = logging.getLogger()
logger.setLevel(INFO)
logger.addHandler(StreamHandler(stdout))


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
        }, indent=4).encode('ascii')
        headers = {
            'Authorization': 'Bearer ' + self.token,
        }

        logger.info('=== REQUEST ===')
        logger.info(data.decode())
        logger.debug()

        request = Request('https://api.cirrus-ci.com/graphql', data=data, headers=headers)
        result = urlopen(request)
        text = result.read().decode()
        result_data = json.loads(text)

        logger.info('=== RESPONSE ===')
        logger.info(text)
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
            }
        }

        status, data = self.graphql('trigger-task', variables)

        return (status, data)


with open('config.json', mode="r") as f:
    config = json.load(f)

cirrus = Cirrus(config)


for task in config['tasks']:
    #logger.info(task)
    user, repo = task['repo'].split('/')
    branch = task['branch']
    task_name = task['task']

    build = cirrus.latest_build(user, repo, task['branch'])
    task_id = cirrus.find_task(build, task_name)['id']
    #logger.info('task_id={}'.format(task_id))

    status, data = cirrus.trigger_task(task_id)
    #logger.info(status)
    #pprint(data)
