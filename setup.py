from setuptools import setup, find_packages

setup(
    name="fairscape_models",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic",
        "pymongo"
    ],
    python_requires=">=3.7",
    description="Fairscape metadata models",
)