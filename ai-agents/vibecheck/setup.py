from setuptools import setup, find_packages

setup(
    name="vibecheck",
    version="1.0.0",
    description="Communication Tone Analyzer — Analyze any text for tone, subtext, and communication style",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "vibecheck=vibecheck.cli:main",
        ],
    },
)