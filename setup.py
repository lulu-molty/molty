from setuptools import setup, find_packages

setup(
    name='molty',
    version='1.0.0',
    description='Digital Currency for AI Agents',
    author='LuluClawd',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'ecdsa>=0.17.0',
        'requests>=2.28.0',
    ],
    python_requires='>=3.8',
)
