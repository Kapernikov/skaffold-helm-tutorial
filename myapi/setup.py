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
        'uvicorn>=0.16',
        'fastapi>=0.63',
        'psycopg2-binary>=2.9'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
)
