#!/usr/bin/env python
import os
import sys
from setuptools import setup, find_packages

repo_base_dir = os.path.abspath(os.path.dirname(__file__))
# pull in the packages metadata
package_about = {}
with open(os.path.join(repo_base_dir, "chainlet", "__about__.py")) as about_file:
    exec(about_file.read(), package_about)

with open('long_description.rst', 'r') as description_file:
    long_description = description_file.read()


if __name__ == '__main__':
    setup(
        name=package_about['__title__'],
        version=package_about['__version__'],
        description=package_about['__summary__'],
        long_description=long_description.strip(),
        author=package_about['__author__'],
        author_email=package_about['__email__'],
        url=package_about['__url__'],
        packages=find_packages(),
        zip_safe=True,
        # dependencies
        install_requires=[],
        # metadata for package seach
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Topic :: System :: Monitoring',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.4',
            'Programming Language :: Python :: 2.5',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],
        keywords='chaining generator coroutine stream pipeline chain bind tree graph',
        # unit tests
        test_suite='chainlet_unittests',
        # use unittest backport to have subTest etc.
        tests_require=['unittest2'] if sys.version_info < (3, 4) else [],
    )
