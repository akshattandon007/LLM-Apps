from setuptools import setup, find_packages

setup(
    name="triptome",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "chromadb>=0.6.0,<1.0.0",
        "pypdf>=5.0.0,<6.0.0",
        "rich>=13.0.0,<14.0.0",
        "httpx>=0.27.0,<1.0.0",
        "click>=8.1.0,<9.0.0",
        "pydantic>=2.0.0,<3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "triptome=triptome.cli:main",
        ],
    },
    python_requires=">=3.10",
)