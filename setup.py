from setuptools import setup, find_packages

setup(
    name="fairscape-models",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "pydantic",
    ],
    python_requires=">=3.8",
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