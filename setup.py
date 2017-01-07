from setuptools import setup

setup(name = 'labots',
        version = '1.1',
        description = 'Flexible IRC bot framework',
        url = 'https://github.com/SilverRainZ/labots',
        author = 'SilverRainZ',
        author_email = 'silverrainz@outlook.com',
        license = 'GPL3',
        packages = ['labots'],
        scripts = ['labots/labots'],
        install_requires=['pyinotify', 'tornado', 'yaml'],
        zip_safe = False)
