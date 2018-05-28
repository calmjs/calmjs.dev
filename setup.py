from setuptools import setup
from setuptools import find_packages

version = '2.1.0'

long_description = (
    open('README.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')

classifiers = """
Development Status :: 5 - Production/Stable
Environment :: Console
Environment :: Plugins
Framework :: Setuptools Plugin
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)
Operating System :: MacOS :: MacOS X
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: POSIX :: BSD
Operating System :: POSIX :: Linux
Operating System :: OS Independent
Programming Language :: JavaScript
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Testing
Topic :: Software Development :: Build Tools
Topic :: System :: Software Distribution
Topic :: Utilities
""".strip().splitlines()

package_json = {
    "devDependencies": {
        "chai": "^2.3.0",
        "coveralls": "~2.11.2",
        "karma": "~1.3.0",
        "karma-chai": "^0.1.0",
        "karma-chrome-launcher": "~2.0.0",
        "karma-coverage": "~0.3.1",
        "karma-expect": "~1.1.2",
        "karma-firefox-launcher": "~1.1.0",
        "karma-junit-reporter": "~0.2.2",
        "karma-mocha": "~1.2.0",
        "karma-phantomjs-launcher": "~1.0.2",
        "karma-sinon": "~1.0.5",
        "karma-spec-reporter": "~0.0.26",
        "karma-wrap-preprocessor": "~0.1.0",
        "mocha": "~3.1.2",
        "phantomjs-prebuilt": "~2.1.0",
        "sinon": "~1.17.4"
    },
}


setup(
    name='calmjs.dev',
    version=version,
    description=(
        "Package for aiding the development of JavaScript code to be provided "
        "as part of Python packages through integration with Node.js "
        "development tools into a Python environment via the Calmjs framework."
    ),
    long_description=long_description,
    classifiers=classifiers,
    keywords='',
    author='Tommy Yu',
    author_email='tommy.yu@auckland.ac.nz',
    url='https://github.com/calmjs/calmjs.dev',
    license='gpl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['calmjs'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'calmjs>=3.1.0,<4',
        'calmjs.parse>=1.0.0',
    ],
    package_json=package_json,
    entry_points={
        'calmjs.registry': [
            # for pure development of calmjs.dev
            'calmjs.dev.module = calmjs.module:ModuleRegistry',
            'calmjs.dev.module.tests = calmjs.module:ModuleRegistry',
            'calmjs.artifacts.tests = '
            'calmjs.dev.artifact:ArtifactTestRegistry',
        ],
        'calmjs.dev.module': [
            'calmjs.dev = calmjs.dev',
        ],
        'calmjs.dev.module.tests': [
            'calmjs.dev.tests = calmjs.dev.tests',
        ],
        'calmjs.runtime': [
            'karma = calmjs.dev.runtime:karma',
        ],
        'calmjs.runtime.artifact': [
            'karma = calmjs.dev.runtime:artifact_karma',
        ],
        'calmjs.dev.runtime.karma': [
            'run = calmjs.dev.runtime:run',
        ],
    },
    test_suite="calmjs.dev.tests.make_suite",
)
