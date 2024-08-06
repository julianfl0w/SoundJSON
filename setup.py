#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="SoundJSON",
    version="1.0",
    description="A Novel Sound Sample File Standard for Python and Javascript",
    author="Julian Loiacono",
    author_email="jcloiacon@gmail.com",
    url="https://github.com/julianfl0w/SoundJSON",
    packages=find_packages(exclude=("examples")),
    package_data={
        # everything
        # "": ["*"]
        "": ["."]
    },
    include_package_data=True,
)
