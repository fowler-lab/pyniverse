from setuptools import setup

setup(
    install_requires=[
        "numpy >= 1.13",
        "pandas >= 0.21.0",
        "tqdm >= 4.19",
        "ujson >= 1.35",
        "matplotlib >= 2.1.1"
    ],
    name='pyniverse',
    version='1.0.0',
    url='https://github.com/philipwfowler/pyniverse',
    author='Philip W Fowler',
    packages=['pyniverse'],
    license='MIT',
    scripts=['bin/analyse-zooniverse-classifications.py'],
    long_description=open('README.md').read(),
)
