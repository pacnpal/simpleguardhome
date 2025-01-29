from setuptools import setup, find_packages

setup(
    name="simpleguardhome",
    version="0.1.0",
    packages=find_packages(where="src", include=["simpleguardhome*"]),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "simpleguardhome": ["templates/*"]
    },
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "httpx",
        "pydantic",
        "jinja2",
    ],
)