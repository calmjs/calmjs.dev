from setuptools import setup
from setuptools import find_packages

version = '0.0'

long_description = (
    open('README.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')

package_json = {
    "devDependencies": {
        "chai": "^2.3.0",
        "coveralls": "~2.11.2",
        "extend": "~2.0.1",
        "grunt": "~0.4.5",
        "grunt-cli": "~0.1.13",
        "grunt-contrib-copy": "~0.8.0",
        "grunt-contrib-jshint": "~0.11.2",
        "grunt-contrib-less": "~1.0.1",
        "grunt-contrib-uglify": "~0.9.1",
        "grunt-contrib-watch": "~0.6.1",
        "grunt-karma": "~0.10.1",
        "grunt-sed": "~0.1.1",
        "karma": "~0.12.31",
        "karma-chai": "^0.1.0",
        "karma-expect": "~1.1.2",
        "karma-chrome-launcher": "~0.1.8",
        "karma-coverage": "~0.3.1",
        "karma-firefox-launcher": "~0.1.4",
        "karma-junit-reporter": "~0.2.2",
        "karma-mocha": "~0.1.10",
        "karma-phantomjs-launcher": "~0.2.1",
        "karma-sauce-launcher": "~0.2.10",
        "karma-script-launcher": "~0.1.0",
        "karma-sinon": "~1.0.5",
        "karma-spec-reporter": "0.0.19",
        "lcov-result-merger": "~1.0.2",
        "less": "~1.7.0",
        "mocha": "~2.2.4",
        "phantomjs-prebuilt": "~2.1.0",
        "sinon": "~1.17.4"
    },
}


setup(name='calmjs.dev',
      version=version,
      description="JavaScript development tools through the calmjs framework",
      long_description=long_description,
      classifiers=[
          "Programming Language :: Python",
      ],
      keywords='',
      author='Tommy Yu',
      author_email='tommy.yu@auckland.ac.nz',
      url='https://github.com/calmjs/calmjs.dev',
      license='gpl',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['calmjs'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'calmjs',
      ],
      package_json=package_json,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
