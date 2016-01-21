# Copyright (c) 2016 CloudNative, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import json

import click

from cruddy import CRUD
from cruddy.lambdaclient import LambdaClient


class CLIHandler(object):

    def __init__(self, profile_name, region_name,
                 lambda_fn, config_file, debug=False):
        self.lambda_fn = lambda_fn
        self.lambda_client = None
        if lambda_fn:
            self.lambda_client = LambdaClient(
                profile_name=profile_name, region_name=region_name,
                func_name=lambda_fn, debug=debug)
        if config_file:
            config = json.load(config_file)
            self.crud = CRUD(**config)
        self.debug = debug

    def _handle_response(self, response):
        if response.status == 'success':
            click.echo(json.dumps(response.data, indent=4))
        else:
            click.echo(click.style(response.status, fg='red'))
            click.echo(click.style(response.error_type, fg='red'))
            click.echo(click.style(response.error_message, fg='red'))

    def _invoke_lambda(self, payload):
        response = self.lambda_client.invoke(payload)
        self._handle_response(response)

    def _invoke_cruddy(self, payload):
        response = self.crud.handler(**payload)
        self._handle_response(response)

    def invoke(self, payload):
        if self.lambda_fn:
            self._invoke_lambda(payload)
        elif self.crud:
            self._invoke_cruddy(payload)
        else:
            msg = 'You must specify either --lambda-fn or --config'
            click.echo(click.style(msg, fg='red'))

pass_handler = click.make_pass_decorator(CLIHandler)


@click.group()
@click.option(
    '--profile',
    default=None,
    help='AWS credential profile')
@click.option(
    '--region',
    default=None,
    help='AWS region')
@click.option(
    '--lambda-fn',
    help='AWS Lambda controller name')
@click.option(
    '--config',
    help='cruddy config file', type=click.File('rb'))
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Turn on debugging output'
)
@click.version_option('0.11.1')
@click.pass_context
def cli(ctx, profile, region, lambda_fn, config, debug):
    """
    cruddy is a CLI interface to the cruddy handler.  It can be used in one
    of two ways.

    First, you can pass in a ``--config`` option which is a JSON file
    containing all of your cruddy parameters and the CLI will create a cruddy
    handler to manipulate the DynamoDB table directly.

    Alternatively, you can pass in a ``--lambda-fn`` option which is the
    name of an AWS Lambda function which contains a cruddy handler.  In this
    case the CLI will call the Lambda function to make the changes in the
    underlying DynamoDB table.
    """
    ctx.obj = CLIHandler(profile, region, lambda_fn, config, debug)


@cli.command()
@pass_handler
def describe(handler):
    """Describe the cruddy handler"""
    data = {'operation': 'describe'}
    handler.invoke(data)


@cli.command()
@pass_handler
def list(handler):
    """List the items"""
    data = {'operation': 'list'}
    handler.invoke(data)


@cli.command()
@click.option(
    '--decrypt/--no-decrypt',
    default=False,
    help='Decrypt any encrypted attributes')
@click.argument('item_id', nargs=1)
@pass_handler
def get(handler, item_id, decrypt):
    """Get an item"""
    data = {'operation': 'get',
            'decrypt': decrypt,
            'id': item_id}
    handler.invoke(data)


@cli.command()
@click.argument('item_id', nargs=1)
@pass_handler
def delete(handler, item_id):
    """Delete an item"""
    data = {'operation': 'delete',
            'id': item_id}
    handler.invoke(data)


@cli.command()
@click.argument('query', nargs=1)
@pass_handler
def search(handler, query):
    """Perform a search"""
    data = {'operation': 'search',
            'query': query}
    handler.invoke(data)


@cli.command()
@click.option('--increment', default=1, help='increment by this much')
@click.argument('item_id', nargs=1)
@click.argument('counter_name', nargs=1)
@pass_handler
def increment(handler, increment, item_id, counter_name):
    """Increment a counter attribute atomically"""
    data = {'operation': 'increment_counter',
            'id': item_id,
            'counter_name': counter_name,
            'increment': increment}
    handler.invoke(data)


@cli.command()
@click.argument('item_document', type=click.File('rb'))
@pass_handler
def create(handler, item_document):
    """Create a new item from a JSON document"""
    data = {'operation': 'create',
            'item': json.load(item_document)}
    handler.invoke(data)


@cli.command()
@click.argument('item_document', type=click.File('rb'))
@pass_handler
def update(handler, item_document):
    """Update an item from a JSON document"""
    data = {'operation': 'update',
            'item': json.load(item_document)}
    handler.invoke(data)


if __name__ == '__main__':
    list()
