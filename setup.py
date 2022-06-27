# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in addon_customization/__init__.py
from addon_customization import __version__ as version

setup(
	name='addon_customization',
	version=version,
	description='Addon Customization',
	author='riconova',
	author_email='suprayoto.riconova@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
