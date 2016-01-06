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
* debug - if not False this will cause the raw_response to be left
  in the response dictionary

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

The response returned from all CRUD operations is a Python object with the
following attributes.

* **data** is the actual data returned from the CRUD operation (if successful)
* **status** is the status of the response and is either ``success`` or
``error``
* **metadata** is metadata from the underlying DynamoDB API call
* **error_type** will be the type of error, if ``status != 'success'``
* **error_code** will be the code of error, if ``status != 'success'``
* **error_type** will be the full error message, if ``status != 'success'``
* **raw_response** will contain the full response from DynamoDB if the CRUD
handler is in ``debug`` mode.
* **is_successful** a simple short-cut, equivalent to ``status == 'success'``

You can convert the CRUDResponse object into a standard Python dictionary using
the ``flatten`` method

```
>>> response = crud.create(...)
>>> response.flatten()
{'data': {'created_at': 1452109758363,
  'name': 'the dude',
  'email': 'the@dude.com',
  'twitter': 'thedude',
  'id': 'a6ac0fd7-cdde-4170-a1a9-30e139c44897',
  'modified_at': 1452109758363},
 'error_code': None,
 'error_message': None,
 'error_type': None,
 'metadata': {'HTTPStatusCode': 200,
  'RequestId': 'LBBFLMIAVOKR8LOTK7SRGFO4Q3VV4KQNSO5AEMVJF66Q9ASUAAJG'},
 'raw_response': None,
 'status': 'success'}
 >>>
 ```
 
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


