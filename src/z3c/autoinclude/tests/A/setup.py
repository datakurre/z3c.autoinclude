from setuptools import find_packages
from setuptools import setup

import os
import sys


version = '0.0'

setup(name='A',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      package_data = {'': ['*.zcml',]},
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'b.c',
	'z3c.autoinclude',
	'TestDirective',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
