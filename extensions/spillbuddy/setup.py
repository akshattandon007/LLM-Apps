"""Setup for SpillBuddy."""

from setuptools import setup, find_packages

setup(
    name="spillbuddy",
    version="1.0.0",
    description="🧴 Stain removal guide CLI — what to do when you spill something",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "spillbuddy=spillbuddy.cli:main",
        ],
    },
    python_requires=">=3.9",
)