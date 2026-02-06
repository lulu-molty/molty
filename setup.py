from setuptools import setup, find_packages

setup(
    name='molty',
    version='1.0.0',
    description='MOLTY Coin - Digital Currency for AI Agents',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='LuluClawd',
    url='https://github.com/lulu-molty/molty',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'ecdsa>=0.17.0',
        'requests>=2.28.0',
    ],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    entry_points={
        'console_scripts': [
            'molty-wallet=wallet.wallet_manager:main',
        ],
    },
)