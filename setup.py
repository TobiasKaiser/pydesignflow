# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import setuptools

exec(open('pydesignflow/version.py').read()) # --> __version__

setuptools.setup(
    name="pydesignflow",
    version=__version__,
    author="Tobias Kaiser",
    author_email="mail@tb-kaiser.de",
    description="Micro-Framework for FPGA / VLSI Design Flow in Python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires='>=3.8',
    install_requires=[
        "tabulate >= 0.8.0",
        "docutils >= 0.21.2",
        "Sphinx >= 7.3.7",
        "argcomplete >= 3.6.2",
    ],
    entry_points={
        "console_scripts": [
            "flow = pydesignflow.shortcut:main"
        ]
    },
)
