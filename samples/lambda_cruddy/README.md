# lambda-cruddy

This is a small sample application that shows how to create a Lambda cruddy
handler.

## Getting Started

### Creating the DynamoDB table

The first thing you have to do is create the DynamoDB table that will be used
by the controller.  The sample includes a CloudFormation template file that can
be used to create the table using the AWSCLI.

```
$ awscli cloudformation create-stack --stack-name lambda-cruddy --template-body file://lambda_cruddy_cf_template.json
```

You can use the ``--profile`` and ``--region`` options of AWSCLI to make sure
the table is created in the right AWS account and region.

Once the CloudFormation stack creation is complete, you should have a new
DynamoDB table called ``lambda-cruddy`` that has a primary has key of ``id`` (a
string) and a global secondary index that indexes another string property
called ``foo``.

Note that the above command creates actual AWS resources and will probably cost
you a small amount of money.

### Installing dependencies

The source code for our Lambda handler is in the ``_src`` directory.  You must
also install the dependencies (in this case, cruddy) as well.  To do that:

```
$ cd _src
$ pip install --no-deps -r requirements.txt -t .
```

This installs the dependencies within the ``_src`` directory and does not
install anything into system directories on any other location.

### Creating the Lambda handler

#### Edit the kappa config file

To create the AWS Lambda controller, this sample uses the
[kappa](https://github.com/garnaat/kappa) CLI tool to deploy the Lambda handler
to the AWS Lambda service.

First, copy the ``kappa_sample.yml`` file to ``kappa.yml`` and edit the
``kappa.yml`` file in this directory to adjust the ``profile`` and ``region``
values to match your environment.  Also, edit the ``arn`` properties to match
the ARN of your newly created DynamoDB table and index.

#### Edit the Lambda function config file

There is also a config file in the ``_src`` directory called
``dev_config.json``.  The only thing you may need to edit in this file is the
``region`` attribute.  Make sure it matches the region you are using the the
``kappa.yml`` file.

Once the ``kappa.yml`` file and ``_src/dev_config.json`` file have been edited,
you can run kappa.

```
$ kappa --env dev deploy
```

This will create the IAM policy and role required for the Lambda function and
upload the Lambda function and all dependencies to the AWS Lambda service.

### Try it out!

Assuming you already have cruddy installed in your environment, you can try out
the cruddy CLI.

```
$ cruddy --lambda-fn lambda-cruddy list
[]
$
```

Of course, our table is empty so we don't get any results.  So, let's create a
new item in our table.

```
$ cruddy --lambda-fn lambda-cruddy create item1.json
{
    "modified_at": 1453003915424, 
    "created_at": 1453003915424, 
    "foo": "abcde", 
    "bar": 1, 
    "id": "9103a503-3e0b-4859-ab9c-e27ce228a23b"
}
$
```

The file ``item1.json`` is just a sample JSON file containing new item data.
It looks like this:

```
{
    "foo": "abcde"
}
```

As you can see, the only explicit field we create in the JSON file is one
called ``foo`` with a value of ``"abcde"```.  But the item returned by the
create operation contains more attributes.  That's because the configuration
file we have associated with our Lambda handler function defines a
**prototype** for items in our table.  It looks like this:

```
{
...
    "prototype": {"id": "<on-create:uuid>",
                  "created_at": "<on-create:timestamp>",
                  "modified_at": "<on-update:timestamp>",
                  "foo": "",
                  "bar": 1}
...
}
```

This prototype says that the item will have an attribute called ``foo`` which
will be a string and another attribute called ``bar`` which will be an int.  If
you don't supply values for these attributes they will be initialized to
whatever value you provide in the prototype.

In addition, there are three calculated values.  One, ``id`` is a UUID that
will be stored in the object when it is created.  The others are timestamp
objects.  One of them, ``created_at`` will be stored in the object at creation
time and the other, ``modified_at`` will be written into the object at create
time and any time the object is modified.

Now let's create another item:

```
$ cruddy --lambda-fn lambda-cruddy create item2.json
{
    "modified_at": 1453004030544, 
    "created_at": 1453004030544, 
    "foo": "fghij", 
    "bar": 10, 
    "id": "851170cf-c0d4-4c1e-8cc0-82958415d0c0"
}
$
```

Now let's list our items again:

```
$ cruddy --lambda-fn lambda-cruddy list
[
    {
        "bar": 10, 
        "created_at": 1453004030544, 
        "foo": "fghij", 
        "modified_at": 1453004030544, 
        "id": "851170cf-c0d4-4c1e-8cc0-82958415d0c0"
    }, 
    {
        "bar": 1, 
        "created_at": 1453003915424, 
        "foo": "abcde", 
        "modified_at": 1453003915424, 
        "id": "9103a503-3e0b-4859-ab9c-e27ce228a23b"
    }
]
$
```

You can ``get`` a particular item:

```
$ cruddy --lambda-fn lambda-cruddy get 851170cf-c0d4-4c1e-8cc0-82958415d0c0
{
    "bar": 10, 
    "created_at": 1453004030544, 
    "foo": "fghij", 
    "modified_at": 1453004030544, 
    "id": "851170cf-c0d4-4c1e-8cc0-82958415d0c0"
}
$
```

You can search based on any index.  In our case, we defined a GSI for the
``foo`` attribute so we can search on that:

```
$ cruddy --lambda-fn lambda-cruddy search foo=abcde
[
    {
        "bar": 1, 
        "created_at": 1453003915424, 
        "foo": "abcde", 
        "modified_at": 1453003915424, 
        "id": "9103a503-3e0b-4859-ab9c-e27ce228a23b"
    }
]
$
```

You can do an atomic increment of any integer attribute, such as ``bar``:

```
$ cruddy --lambda-fn lambda-cruddy increment 851170cf-c0d4-4c1e-8cc0-82958415d0c0 bar
11
$ cruddy --lambda-fn lambda-cruddy get 851170cf-c0d4-4c1e-8cc0-82958415d0c0
{
    "bar": 11, 
    "created_at": 1453004030544, 
    "foo": "fghij", 
    "modified_at": 1453004030544, 
    "id": "851170cf-c0d4-4c1e-8cc0-82958415d0c0"
}
$
```

And you can, of course, delete an item:

```
$ cruddy --lambda-fn lambda-cruddy delete 851170cf-c0d4-4c1e-8cc0-82958415d0c0
true
$
```
