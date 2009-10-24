from setuptools import setup, find_packages


setup(
    name = "snow",
    version = "0.1-alpha",
    author = "Brian Rosner",
    author_email = "brosner@gmail.com",
    description = "Simplified WSGI process management",
    long_description = open("README").read(),
    license = "BSD",
    url = "http://github.com/brosner/snow",
    packages = find_packages(),
    entry_points = {
        "console_scripts": [
            "snow = snow.main:main",
        ],
    },
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ]
)