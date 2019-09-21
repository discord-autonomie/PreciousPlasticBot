"""Discord bot for Autonomie community
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='BOT-integration',
    version="1.0.0",
    description='Discord bot for Autonomie community',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/discord-autonomie/BOT-integration',
    author='Sygmei/olaxe',
    author_email='sygmei@sygmei.io/olaxe@pm.me',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='discord bot integration',
    packages=find_packages(include=['botintegration']),
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
            "botintegration=botintegration.main:run"
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/discord-autonomie/BOT-integration/issues',
        'Source': 'https://github.com/discord-autonomie/BOT-integration',
    },
)
