#!/usr/bin/env python
from distutils.core import setup

setup(
    name='django-smart-serializers',
    version='0.0.1b',
    description='More flexible serializers for Django',
    author='Travis cline',
    author_email='travis.cline@gmail.com',
    url='http://example.com',
    packages=[
        'smart_serializers',
    ],
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Utilities'],
)