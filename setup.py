#!/usr/bin/env python3
"""
Setup script for neo4j-graph-lib.

This file is maintained for backward compatibility.
For modern Python packaging, see pyproject.toml.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements from requirements.txt
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="neo4j-graph-lib",
    version="0.1.0",
    author="Neo4j Graph Library Team",
    author_email="contact@example.com",
    description="A Python library for Neo4j graph database operations with schema management, CRUD, and advanced querying",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/neo4j-graph-lib",
    project_urls={
        "Bug Tracker": "https://github.com/example/neo4j-graph-lib/issues",
        "Documentation": "https://neo4j-graph-lib.readthedocs.io/",
        "Source Code": "https://github.com/example/neo4j-graph-lib",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "examples": [
            "jupyter>=1.0.0",
            "matplotlib>=3.5.0",
        ],
    },
    keywords="neo4j graph database crud schema cypher",
    include_package_data=True,
    zip_safe=False,
)