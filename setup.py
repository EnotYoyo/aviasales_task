import os
from setuptools import setup, find_packages

__pckg__ = "aviasales-task"
__dpckg__ = __pckg__.replace("-", "_")
__version__ = "0.0.1"


def load_requirements():
    with open(os.path.join(os.getcwd(), "requirements.txt")) as requirements:
        return requirements.read().splitlines()


setup(
    name=__pckg__,
    version=__version__,
    author="Andrey Lemets",
    author_email="a.lemets@gmail.com",
    license="MIT License",
    platforms=["linux"],
    packages=find_packages(),
    install_requires=load_requirements(),
    include_package_data=True,
)
