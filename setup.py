#!/usr/bin/env python3
"""
Setup script for Auralis
"""

from setuptools import setup, find_packages
import json

# Load version from config
with open('config.json') as f:
    config = json.load(f)
version = config['app_identity']['version']

with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='auralis',
    version=version,
    description=config['app_identity']['description'],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Auralis Team',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'auralis=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.8',
)