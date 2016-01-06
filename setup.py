#!/usr/bin/env python

from setuptools import setup, find_packages

requires = [
    'boto3',
]


setup(
    name='cruddy',
    version='0.1.5',
    description='A CRUD wrapper class for AWS Lambda',
    long_description=open('README.md').read(),
    author='Mitch Garnaat',
    author_email='mitch@cloudnative.io',
    url='https://github.com/cloudnative/cruddy',
    packages=find_packages(exclude=['tests*']),
    install_requires=requires,
    license=open("LICENSE").read(),
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
