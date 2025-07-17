from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gacha-reroll-automation",
    version="1.0.0",
    author="Reroll Automation",
    description="A Python-based automation tool for monitoring and detecting specific characters in gacha games using LDPlayer Android emulator instances.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gacha-reroll-automation",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.7",
    include_package_data=True,
    package_data={"": ["*.ini", "*.txt"]},
    entry_points={
        "console_scripts": [
            "gacha-reroll=simple_reroll_monitor:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
) 