#!/usr/bin/env python

import os
from setuptools import setup, find_packages

requires = [
    'boto3',
    'click',
]


setup(
    name='cruddy',
    version=open(os.path.join('cruddy', '_version')).read().strip(),
    description='A CRUD wrapper class for Amazon DynamoDB',
    long_description=open('README.md').read(),
    author='Mitch Garnaat',
    author_email='mitch@cloudnative.io',
    url='https://github.com/cloudnative/cruddy',
    packages=find_packages(exclude=['tests*']),
    package_data={'cruddy': ['_version']},
    entry_points="""
        [console_scripts]
        cruddy=cruddy.scripts.cli:cli
    """,
    install_requires=requires,
    license="Apache License 2.0",
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ),
)
