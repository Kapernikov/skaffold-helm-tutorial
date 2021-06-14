import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="myapi", # Replace with your own username
    version="0.0.1",
    author="Frank Dekervel",
    author_email="frank@kapernikov.com",
    description="Test",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/notyet",
    packages=setuptools.find_packages(),
    install_requires=[
        'fastapi>=0.63',
        'python-keycloak>=0.24',
        'uvloop>=0.14.0',
        'httptools==0.1',
        'kubernetes==12.0.1',
        'aiofiles'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
)
