import os
from setuptools import setup

VERSION = "0.9.2"

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-mongolog',
    version=VERSION,
    packages=['mongolog'],
    install_requires=(
        # TODO Can this actually work with a lower django version?
        'django>=1.9.8',
        'pymongo>=3.0',
        'requests>=2.8',
        'coverage',
    ),
    include_package_data=True,
    license='GPL V3',
    description='A simple mongo based log handler for python/django',
    long_description=README,
    url='https://github.com/gnulnx/django-mongolog',
    download_url='https://github.com/gnulnx/django-mongolog/tree/%s' % (VERSION),
    author='John Furr',
    author_email='john.furr@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 2.0',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
