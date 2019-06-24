# Learn more: https://github.com/Yoshi-E/Python-BEC-RCon
# python setup.py sdist bdist_wheel
# pip install dist/bec_rcon-0.1.0-py3-none-any.whl
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='bec_rcon',
    version='0.1.1',
    description='API for Battleye extended controls - Arma3',
    long_description=readme,
    author='Yoshi_E',
    author_email='notifyYoshi@yahoo.de',
    url='https://github.com/Yoshi-E/Python-BEC-RCon',
    license=license,
    classifiers=[
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 4 - Alpha',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Tools',

    # Pick your license as you wish (should match "license" above)
     'License :: Attribution-NonCommercial-ShareAlike',

    # Specify the Python versions you support here.
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7'
    ],
    keywords='arma rcon battleye bec administration',
    project_urls={
    'Say Thanks!': 'https://forums.bohemia.net/forums/topic/223835-api-bec-rcon-api-for-python-and-discord/',
    'Source': 'https://github.com/Yoshi-E/Python-BEC-RCon',
    'Tracker': 'https://github.com/Yoshi-E/Python-BEC-RCon/issues',
    },
    py_modules=["bec_rcon"],
    python_requires='>=3.6',
    packages=find_packages(exclude=('example'))
)