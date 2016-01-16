Installing Dependencies
-----------------------

This module is using cruddy and needs to list it as a dependency.  However,
cruddy, in turn, has a dependency on boto3 and everything that it brings with
it.  Since that is our only dependency, to avoid huge zip files I am installing
my dependencies like this:

    $ pip install --no-dep -r requirements.txt -t .

This will install all of the dependencies inside the code directory so they can
be bundled with your own code and deployed to Lambda.

If you have other dependencies in your Lambda function, don't use this
approach.  Just live with the big zip files.

The ``setup.cfg`` file in this directory is required if you are running on
MacOS and are using brew.  It may not be needed on other platforms.
