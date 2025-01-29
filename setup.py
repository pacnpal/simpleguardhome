from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="simpleguardhome",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "simpleguardhome": ["templates/*", "favicon.ico"]
    },
    python_requires=">=3.7",
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "httpx",
        "pydantic",
        "jinja2",
    ],
)