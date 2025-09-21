"""
Setup script for Solana Swarm Intelligence Framework
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="solana-swarm",
    version="0.1.0",
    author="Solana Swarm Team",
    author_email="team@solana-swarm.com",
    description="Solana Swarm Intelligence Framework for AI-powered trading strategies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/solana-swarm/solana-swarm",
    project_urls={
        "Bug Tracker": "https://github.com/solana-swarm/solana-swarm/issues",
        "Documentation": "https://docs.solana-swarm.com",
    },
    packages=find_packages(),
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("dev-requirements.txt"),
    },
    entry_points={
        "console_scripts": [
            "solana-swarm=solana_swarm.cli.main:app",
            "swarm-chat=solana_swarm.cli.chat:main",
        ],
    },
    package_data={
        "solana_swarm": [
            "agents/*/agent.yaml",
            "templates/*/*.py",
            "templates/*/*.yaml",
            "core/config/*.json",
        ],
    },
    include_package_data=True,
)