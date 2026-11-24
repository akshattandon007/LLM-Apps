from setuptools import setup, find_packages

setup(
    name="storyweaver",
    version="1.0.0",
    description="Interactive branching fiction powered by AI",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests>=2.31.0"],
    entry_points={
        "console_scripts": [
            "storyweaver=storyweaver.cli:main",
        ],
    },
    python_requires=">=3.10",
)
