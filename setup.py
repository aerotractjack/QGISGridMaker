from setuptools import setup, find_packages

setup(
    name="qgisgridmaker",
    version="0.1",
    packages=find_packages(),
    author="Jack",
    author_email="jackw@aerotract.com",
    description="Aerotract QGIS Plot Grid Generation library",
    long_description=open('readme.md').read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
