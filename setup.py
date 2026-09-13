from setuptools import setup, find_packages

setup(
    name="alarm_cli",
    version="1.0.0",
    description="A lightweight, natural-language command-line alarm clock for Python",
    author="trapti321",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "alarm=alarm_cli.cli:main",
        ],
    },
    python_requires=">=3.7",
)
