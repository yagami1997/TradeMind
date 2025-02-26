from setuptools import setup, find_packages

setup(
    name="TradeMind-Alpha",
    version="0.3.0",
    description="量化交易策略和分析工具集",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        'pandas>=1.0.0',
        'pandas_ta>=0.3.0',
        'numpy>=1.18.0',
        'yfinance>=0.1.63',
    ],
    python_requires='>=3.7',
)