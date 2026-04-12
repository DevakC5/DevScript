from setuptools import setup

setup(
    name="devlang",
    version="1.0.0",
    description="DevLang – a clean beginner-friendly programming language",
    packages=["devlang"],
    install_requires=["rich"],
    entry_points={
        "console_scripts": [
            "dev=devlang.cli:main",
        ],
    },
    python_requires=">=3.7",
)