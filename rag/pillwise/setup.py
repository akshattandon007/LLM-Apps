from setuptools import setup, find_packages

setup(
    name="pillwise",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "sentence-transformers>=2.2.0",
        "faiss-cpu>=1.7.0",
        "requests>=2.28.0",
        "numpy>=1.23.0",
        "scikit-learn>=1.1.0",
    ],
    entry_points={
        "console_scripts": [
            "pillwise=pillwise.cli:main",
        ],
    },
    python_requires=">=3.9",
)
