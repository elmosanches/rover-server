import os, sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import ipdb; ipdb.set_trace()
        import tox
        import shlex
        errno = tox.cmdline(args=shlex.split(self.tox_args))
        sys.exit(errno)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    #metadata
    name = "rover_server",
    version = "0.0.1",
    author = "Przemyslaw Rekawiecki",
    author_email = "przemek.rek@gmail.com",
    description = ("""
                    Rover server enabling internet communications between \
                   controller and rover
                   """),
    license = "BSD",
    keywords = "rover server",
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Topic :: RC Rover Utilities",
        "License :: OSI Approved :: BSD License",
    ],

    #package configuration
    packages=['rover_server'],
    install_requires=['twisted'],
    entry_points={
        'console_scripts': [
            'rover_server = rover_server.server:main',
        ]
    },
    tests_require=['tox'],
    cmdclass = {'test': Tox},
)
