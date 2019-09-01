#!/usr/bin/env python3

import json
import logging
from pathlib import Path
from pprint import pprint
from sys import stdout
import gqlmod

gqlmod.enable_gql_import()

import queries  # noqa: E402


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stdout))


class Cirrus:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = json.load(f)

        self.token = self.config['token']

    def latest_build(self, owner, name, branch):
        res = queries.GitHubRepositoryQuery(
            owner=owner,
            name=name,
            branch=branch,
        )
        assert not res.errors

        builds = res.data['data']['githubRepository']['builds']['edges']
        last_build = builds[0]['node']
        return last_build

    def find_task(self, build, task_name):
        tasks = filter(lambda x: x['name'] == task_name, build['tasks'])
        return list(tasks)[0]

    def trigger_task(self, task_id):
        resp = queries.TaskDetailsTriggerMutation(input={
            'taskId': task_id,
            'clientMutationId': 'rerun-' + task_id,
        })

        return (resp.errors, resp.data)


repo_dir = Path(__file__).resolve().parent
cirrus = Cirrus(repo_dir / 'config.json')

with gqlmod.with_provider('cirrus-ci', token=cirrus.token):
    for task in cirrus.config['tasks']:
        logger.info('Running {} task for {}.'.format(task['task'], task['repo']))

        user, repo = task['repo'].split('/')
        branch = task['branch']
        task_name = task['task']

        build = cirrus.latest_build(user, repo, task['branch'])
        task_id = cirrus.find_task(build, task_name)['id']

        errors, data = cirrus.trigger_task(task_id)
        if errors:
            logger.info('')
            for error in errors:
                logger.error(error)
            pprint(data)
