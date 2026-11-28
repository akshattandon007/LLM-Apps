"""Setup for MintDocs — SEC Filing & Annual Report Q&A with RAG."""

from setuptools import find_packages, setup

setup(
    name="mintdocs",
    version="0.1.0",
    description="SEC Filing & Annual Report Q&A with RAG — fetch, chunk, embed, and query 10-K/10-Q filings",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="MintDocs",
    url="https://github.com/mintdocs/mintdocs",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.27.0",
    ],
    extras_require={
        "full": [
            "sentence-transformers>=2.2.0",
            "faiss-cpu>=1.7.0",
            "numpy>=1.24.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-httpx>=0.30.0",
            "httpx>=0.27.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mintdocs = mintdocs.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)