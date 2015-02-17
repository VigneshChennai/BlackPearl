from distutils.core import setup

setup(
    name='BlackPearl',
    version='1',
    packages=['BlackPearl.testing', 'dwm', 'dwm.test', 'testing', 'testing.test'],
    package_dir={'': 'bin'},
    url='https://github.com/VigneshChennai/BlackPearl',
    license='GNU GENERAL PUBLIC LICENSE v3',
    author='Vigneshwaran P',
    author_email='vigneshchennai@live.in',
    description='Highly scalable python wsgi application server '
)
