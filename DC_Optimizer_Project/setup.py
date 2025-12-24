from setuptools import setup, find_packages

setup(
    name="scari",
    version="2.0.0",
    description="Server Cooling AI with Reinforcement Intelligence",
    author="Your Name",
    author_email="email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "gymnasium>=0.28.0",
        "stable-baselines3>=2.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "tensorboard>=2.13.0",
        "pyyaml>=6.0",
        "tqdm>=4.65.0",
        "click>=8.0.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
