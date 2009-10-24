from distutils.core import setup


setup(
    name = "snow",
    version = "0.1-alpha",
    author = "Brian Rosner",
    author_email = "brosner@gmail.com",
    description = "Simplified WSGI process management",
    long_description = open("README").read(),
    license = "BSD",
    url = "http://github.com/brosner/snow",
    packages = [
        "snow",
    ],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ]
)