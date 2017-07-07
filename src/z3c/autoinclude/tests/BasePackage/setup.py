from setuptools import find_packages
from setuptools import setup


setup(
    name='BasePackage',
    version='0.0',
    description="",
    long_description="""
""",
    # Get strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    package_data={'': ['*.zcml', ]},
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'z3c.autoinclude',
    ],
    entry_points="""
    # -*- Entry points: -*-
    """,
)
