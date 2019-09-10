"""Discord bot for Precious Plastic France community
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='plasticomatic',
    version="1.0.0",
    description='Discord bot for Precious Plastic France community',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Sygmei/PreciousPlasticBot',
    author='Sygmei',
    author_email='sygmei@sygmei.io',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='discord bot preciousplastic',
    packages=find_packages(include=['plasticomatic']),
    python_requires='>=3.6, <4',
    install_requires=[
        "discord"
    ],
    extras_require={
        'test': [
            'coverage',
            'tox',
            'pytest',
            'flake8'
        ],
    },
    entry_points={
        'console_scripts': [
            "plasticomatic=plasticomatic.main:run"
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/Sygmei/PreciousPlasticBot/issues',
        'Source': 'https://github.com/Sygmei/PreciousPlasticBot',
    },
)