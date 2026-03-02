# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="teachverse-auth",
    version="0.1.0",
    description="Production-ready FastAPI authentication with hierarchical permissions like AWS IAM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TEACHVERSE Team",
    author_email="info@teachverse.com",
    url="https://github.com/teachverse/teachverse-auth",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.0",
        "sqlmodel>=0.0.22",
        "pyjwt",  # This provides 'jwt' module
        "pwdlib[argon2]",
        "python-multipart>=0.0.9",
        "pydantic>=2.9.0",
        "pydantic-settings>=2.4.0",
        "psycopg2-binary>=2.9.0",
        "email-validator>=2.1.0",
        "python-dotenv>=1.0.0",
        "typer>=0.12.0",
        "alembic>=1.13.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "black>=24.0.0",
            "isort>=5.13.0",
            "mypy>=1.8.0",
            "ipython>=8.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "teachverse-auth=teachverse_auth.cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Session",
    ],
)