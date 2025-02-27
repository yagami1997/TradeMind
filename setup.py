from setuptools import setup, find_packages

setup(
    name="TradeMind Alpha",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "yfinance",
        "pandas_market_calendars",
    ],
    python_requires=">=3.10",
) 