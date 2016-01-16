import logging
import json

import cruddy

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

config = json.load(open('config.json'))
crud = cruddy.CRUD(**config)


def handler(event, context):
    LOG.info(event)
    response = crud.handler(**event)
    return response.flatten()
