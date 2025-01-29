from setuptools import setup, find_namespace_packages

if __name__ == "__main__":
    try:
        setup(
            package_dir={"": "src"},
            packages=find_namespace_packages(where="src", include=["simpleguardhome*"]),
            package_data={
                "simpleguardhome": [
                    "templates/*",
                    "favicon.ico"
                ]
            },
            include_package_data=True,
            install_requires=[
                "fastapi",
                "uvicorn",
                "python-dotenv",
                "httpx",
                "pydantic",
                "jinja2",
            ]
        )
    except Exception as e:
        print(f"\n\nAn error occurred while building the project: {e}\n"
              "Please ensure you have the most updated version of setuptools, "
              "setuptools_scm and wheel with:\n"
              "   pip install -U setuptools setuptools_scm wheel\n\n")