#!/usr/bin/env python

import io

try:
    from setuptools import find_packages, setup
except ImportError:
    raise ImportError(
        "'setuptools' is required but not installed. To install it, "
        "follow the instructions at "
        "https://pip.pypa.io/en/stable/installing/#installing-with-get-pip-py"
    )


def read(*filenames, **kwargs):
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", "\n")
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


install_req = [
    "tornado",
]


setup(
    name="Dixit",
    version="0.1.0",
    author="Aaron Voelker",
    author_email="arvoelke@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/arvoelke/Dixit/",
    license="Free for personal (non-commercial) use",
    description="Online version of the board game Dixit",
    long_description=read("README.rst"),
    install_requires=install_req,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'dixit = dixit:start',
        ]
    },
    python_requires=">=3.5",
    classifiers=[  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Topic :: Games/Entertainment :: Board Games",
    ],
)
