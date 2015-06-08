# coding: utf-8

from setuptools import setup

setup(
    name='pocket-importer',
    description='API wrapper and importer for getpocket.com',
    long_description=open('README.md').read(),

    version='0.1',
    author='maxint',
    author_email='lnychina@gmail.com',

    url='http://github.com/maxint/pocket-importer',
    license='BSD',

    requires=['requests', ],
    platforms=['Windows', 'POSIX', 'MacOS'],

    py_modules=['pocket', 'pocket_importer'],
    entry_points={
        'console_scripts': [
            'pocket-importer=pocket_importer:main',
        ]
    },

    zip_safe=True,
)