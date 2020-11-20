from setuptools import setup, find_packages

# with open("README.md", "r") as fh:
#     long_description = fh.read()
long_description = ""

setup(
    name="registrar_pycsw",
    version="1.0.0-rc.1",
    author="",
    author_email="",
    description="registrar for PVS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EOEPCA/rm-data-access/tree/master/core",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
