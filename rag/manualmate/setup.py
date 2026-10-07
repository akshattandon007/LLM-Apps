from setuptools import setup, find_packages

setup(
    name="manualmate",
    version="1.0.0",
    description="RAG for home appliance manuals — ask questions about your manuals",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1.0",
        "openai>=1.0.0",
        "numpy>=1.24.0",
        "pypdf>=4.0.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
    ],
)