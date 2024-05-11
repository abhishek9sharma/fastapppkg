from setuptools import find_namespace_packages, find_packages, setup

requirements_core = []
with open("requirements.txt", 'r') as rqfile:
    requirements_core = rqfile.read()


setup(
    name="fastapppkg",
    version="0.0.1",
    description="fastapi starter template",
    long_description_content_type="text/markdown",
    url="https://github.com/abhishek9sharma/fastapppkg",
    author="Abhishek Sharma",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="astapi starter template",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=requirements_core,
    extras_require={}, 
)
