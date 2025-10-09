from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="auralis",
    version="1.0.0",
    description="Terminal-based AI assistant with offline-first voice and text conversation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "auralis=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)