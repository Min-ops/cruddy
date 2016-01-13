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

import boto3
import click


class LambdaHandler(object):

    def __init__(self, profile_name, region_name,
                 controller_name, debug=False):
        session = boto3.Session(
            profile_name=profile_name, region_name=region_name)
        self.client = session.client('lambda')
        self.controller_name = controller_name
        self.debug = debug

    def invoke(self, payload):
        response = self.client.invoke(
            FunctionName=self.controller_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        if self.debug:
            click.echo(click.style('Response from Lambda', fg='green'))
            click.echo(response)
        crud_response = json.load(response['Payload'])
        if self.debug:
            click.echo(click.style('CRUD Response', fg='green'))
            click.echo(crud_response)
        if 'status' not in crud_response:
            click.echo(click.style('Something is very wrong', fg='red'))
            click.echo(crud_response)
        elif crud_response['status'] == 'success':
            click.echo(json.dumps(crud_response['data'], indent=4))
        else:
            click.echo(click.style(crud_response['status'], fg='red'))
            click.echo(click.style(crud_response['error_type'], fg='red'))
            click.echo(click.style(crud_response['error_message'], fg='red'))


pass_handler = click.make_pass_decorator(LambdaHandler)


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
    '--controller',
    help='AWS Lambda controller name')
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Turn on debugging output'
)
@click.version_option('0.1.0')
@click.pass_context
def cli(ctx, profile, region, controller, debug):
    """
    cruddy is a CLI interface to an AWS Lambda function that is acting as
    a cruddy controller for a DynamoDB table.

    The cruddy CLI simply invokes the Lambda function, passing in the correct
    data for the various cruddy operations and then displays the results.
    """
    ctx.obj = LambdaHandler(profile, region, controller, debug)


@cli.command()
@pass_handler
def list(handler):
    """List the items"""
    data = {'operation': 'list'}
    handler.invoke(data)


@cli.command()
@click.argument('item_id', nargs=1)
@pass_handler
def get(handler, item_id):
    """Get an item"""
    data = {'operation': 'get',
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
