from setuptools import setup, find_packages

setup(
    name="stock_tracker",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "pytz>=2024.1",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "black>=24.1.0",
            "flake8>=7.0.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'stock_tracker=stock_tracker.__main__:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for tracking stock prices from Google Finance",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="stock, finance, tracker, google-finance",
    url="https://github.com/yourusername/stock-tracker",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)