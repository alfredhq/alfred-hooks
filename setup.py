from setuptools import setup, find_packages


setup(
    name='alfred-hooks',
    version='0.1.dev',
    license='ISC',
    description='Alfred github hooks manager',
    url='https://github.com/alfredhq/alfred-hooksmanager',
    author='Alfred Developers',
    author_email='team@alfredhq.com',
    packages=find_packages(),
    install_requires=[
        'alfred-db',
        'SQLAlchemy',
        'PyYAML',
        'msgpack-python',
        'pyzmq',
        'PyGithub',
    ],
    entry_points={
        'console_scripts': [
            'alfred-hooks = alfred_hooks.__main__:main'
        ],
    }
)
