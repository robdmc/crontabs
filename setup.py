# import multiprocessing to avoid this bug (http://bugs.python.org/issue15881#msg170215)
import multiprocessing
assert multiprocessing
import re
from setuptools import setup, find_packages


def get_version():
    """
    Extracts the version number from the version.py file.
    """
    VERSION_FILE = 'crontabs/version.py'
    mo = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', open(VERSION_FILE, 'rt').read(), re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError('Unable to find version string in {0}.'.format(VERSION_FILE))


install_requires = [
    'fleming',
    'daiquiri[json]'
]

tests_require = [
    'coverage',
    'flake8',
    'mock',
    'pytest',
    'pytest-cov',
    'pytest-xdist',
    'wheel',
]

docs_require = [
    # 'Sphinx',
    # 'sphinx_rtd_theme'
]

extras_require = {
    'dev': tests_require + docs_require,
}

setup(
    name='crontabs',
    version=get_version(),
    description='Simple job scheduling for python',
    long_description='Simple job scheduling for python',
    url='https://github.com/robdmc/crontabs',
    author='Rob deCarvalho',
    author_email='unlisted@unlisted.net',
    keywords='',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    license='MIT',
    include_package_data=True,
    test_suite='nose.collector',
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    zip_safe=False,
)
