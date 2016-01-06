# cruddy

A simple CRUD wrapper around Amazon DynamoDB.

## Installation

```
$ pip install cruddy
```

## Getting Started

The first thing to do is to create a CRUD handler for your DynamoDB table.  The
constructor for the CRUD class takes a number of parameters to help configure
the handler for your application.  The full list of parameters are:

* table_name - name of the backing DynamoDB table (required)
* profile_name - name of the AWS credential profile to use when creating the
  boto3 Session
* region_name - name of the AWS region to use when creating the boto3 Session
* required_attributes - a list of attribute names that the item is required to
  have or else an error will be returned
* supported_ops - a list of operations supported by the CRUD handler
  (choices are list, get, create, update, delete)
* encrypted_attributes - a list of tuples where the first item in the tuple is
  the name of the attribute that should be encrypted and the second
  item in the tuple is the KMS master key ID to use for
  encrypting/decrypting the value.

An easy way to configure your CRUD handler is to gather all of the parameters
together in a dictionary and then pass that dictionary to the class
constructor.

```
import cruddy

params = {
    'profile_name': 'foobar',
    'region_name': 'us-west-2',
    'table_name': 'fiebaz',
    'required_attributes': ['name', 'email'],
}

crud = cruddy.CRUD(**params)
```

Once you have your handler, you can start to use it.

```
item = {'name': 'the dude', 'email': 'the@dude.com', 'twitter': 'thedude'}
response = crud.create(item)
```

The response returned from all CRUD operations looks like this:

```
{'data': {'created_at': 1452095009485,
          'modified_at': 1452095073532,
          'id': '38c64015-b906-46d0-8364-f66d42bec428',
          'name': 'the dude',
          'email': 'the@dude.com',
          'twitter': 'thedude'},
 'status': 'success',
 'response_metadata': {'HTTPStatusCode': 200,
                       'RequestId': 'PIFQ56D78GRRM7F992INCGS1PNVV4KQNSO5AE'}
}
```

The ``status`` attribute will always be either ``success`` or ``error``.

The``response_metadata`` attribute will always contain information about the
underlying call to DynamoDB that was made to satisfy the CRUD operation.

If the call is successful, ``data`` will be the data returned by the call
(e.g. an individual item for a ``get`` operation or a list of items for a
``list`` operation).

If there was an error, the response will also contain an ``error_type``
attribute which will be the class name of the exception raised.  In addition,
the response will contain an ``error_message`` attribute which will contain a
description of the error.

## CRUD operations

The CRUD object supports the following operations.  Note that depending on the
value of the ``supported_operations`` parameter passed to the constructor, some
of these methods may return an ``UnsupportedOperation`` error type.

### list()

Returns a list of items in the database.  Encrypted attributes are not
decrypted when listing items.

### get(*id*, *decrypt=False*)

Returns the item corresponding to ``id``.  If the ``decrypt`` param is not
False (the default) any encrypted attributes in the item will be decrypted
before the item is returned.  If not, the encrypted attributes will contain the
encrypted value.

### create(*item*)

Creates a new item.  You must pass in a dictionary contain values for at least
all of the required attributes associated with the CRUD handler.

### update(*item*)

Updates the item based on the current values of the dictionary passed in.

### delete(*id*)

Deletes the item corresponding to ``id``.


