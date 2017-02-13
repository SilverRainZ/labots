from setuptools import setup
from distutils.command.install_scripts import install_scripts

class labots_install_scripts(install_scripts):
    def run(self):
        import shutil
        install_scripts.run(self)
        for file in self.get_outputs():
            renamed_file = file[:-3]
            shutil.move(file, renamed_file)

setup(name = 'labots',
        version = '1.1',
        description = 'Flexible IRC bot framework',
        url = 'https://github.com/SilverRainZ/labots',
        author = 'SilverRainZ',
        author_email = 'silverrainz@outlook.com',
        license = 'GPL3',
        packages = ['labots', 'labots.irc'],
        scripts = ['labots.py'],
        install_requires=['pyinotify', 'tornado', 'yaml', 'shutil'],
        cmdclass = { 'install_scripts': labots_install_scripts },
        zip_safe = False)
