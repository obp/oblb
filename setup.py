#!/usr/bin/env python
"""
One Banana Load Balancer
=========================

"If it appears on a resume, its too complicated"

"""

from setuptools import setup

setup(
    name='oblb',
    version='0.0.0',
    author='Adam DePrince',
    author_email='adeprince@nypublicradio.org',
    description='One Banana Load Balancing',
    long_description=__doc__,
    py_modules = [
        "oblb/__init__",
        ],
    packages = ["oblb"],
    zip_safe=True,
    license='GPL',
    include_package_data=True,
    classifiers=[
        ],
    scripts = [
         'scripts/oblb',
        ],
    url = "https://github.com/wnyc/oblb",
    install_requires = [
        ]
)

