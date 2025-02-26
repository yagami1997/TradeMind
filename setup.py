from setuptools import setup, find_packages

setup(
    name="TradeMind Alpha",
    version="0.3",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'pandas_ta',
        'numpy',
    ]
) 