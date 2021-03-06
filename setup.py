import setuptools

setuptools.setup(
    name="pydesignflow",
    version="0.1.0",
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
    entry_points={
        "console_scripts": [
            "flow = pydesignflow.flow:main"
        ]
    }
)