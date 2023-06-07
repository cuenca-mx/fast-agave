from importlib.machinery import SourceFileLoader

from setuptools import find_packages, setup

version = SourceFileLoader('version', 'fast_agave/version.py').load_module()


with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='fast_agave',
    version=version.__version__,
    author='Cuenca',
    author_email='dev@cuenca.com',
    description='Rest api blueprints for fast-api',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cuenca-mx/fast-agave',
    packages=find_packages(),
    include_package_data=True,
    package_data=dict(agave=['py.typed']),
    python_requires='>=3.8',
    install_requires=[
        'aiobotocore>=1.0.0,<3.0.0',
        'types-aiobotocore-sqs>=2.1.0.post1,<3.0.0',
        'cuenca-validations>=0.9.4,<1.0.0',
        'fastapi @ git+https://github.com/Kludex/fastapi.git@0fa8c6275e9d36ee8ae38429408279158c68db9e',
        'mongoengine-plus>=0.0.2,<1.0.0',
        'starlette>=0.28.0,<1.0.0',
        'starlette-context>=0.3.2,<0.4.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
