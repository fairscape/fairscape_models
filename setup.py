from setuptools import setup, find_packages

setup(
    name="fairscape-models",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic",
        "pymongo"
    ],
    python_requires=">=3.7",
    description="Fairscape metadata models",
    author="Justin Niestroy",
    author_email="jniestroy@gmail.com",
    url="https://github.com/fairscape/fairscape_models",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)