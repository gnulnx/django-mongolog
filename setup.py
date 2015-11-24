import os
import subprocess
from setuptools import setup

try:
    VERSION=subprocess.check_output(["git", "describe", "--tags"]).strip()
except:
    VERSION="N/A"

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-mongolog',
    version=VERSION,
    packages=['mongolog'],
    include_package_data=True,
    license='GPL V3',
    description='A simple mongo based logger',
    long_description=README,
    url='https://github.com/gnulnx/django-mongolog',
    download_url='https://github.com/gnulnx/django-mongolog/tree/%s'%(VERSION),
    author='John Furr',
    author_email='john.furr@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.2',
        #'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
