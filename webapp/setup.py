import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-flont',
    version='0.2.0',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='Web client for FLOnt, the French Lexicon Ontology.',
    long_description=README,
    url='https://yohan.chalier.fr/',
    author='Yohan Chalier',
    author_email='yohan@chalier.fr',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.0.3',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        "Django>=3.0.3",
        "wikitextparser",
        "owlready2"
    ],
)
