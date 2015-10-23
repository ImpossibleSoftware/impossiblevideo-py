from distutils.core import setup

setup(
    name='ImpossibleVideo',
    version='2.13.0',
    author='Impossible Software GmbH',
    author_email='iv@impossiblesoftware.com',
    packages=['iv',],
    scripts=['bin/ivcmd.py',],
#    url='http://pypi.python.org/pypi/ImpossibleIO/',
    license='LICENSE',
    description='Interface to ImpossibleVideo',
    long_description=open('README.md').read(),
    install_requires=[
        "protobuf >= 2.5.0",
        "httplib2 >= 0.7.7",
        "requests == 2.1.0"
    ],
)