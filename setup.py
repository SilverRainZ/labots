from setuptools import setup, find_packages
from distutils.command.install_scripts import install_scripts

from labots.common import meta

class labots_install_scripts(install_scripts):
    def run(self):
        import shutil
        install_scripts.run(self)
        for file in self.get_outputs():
            renamed_file = file[:-3]
            shutil.move(file, renamed_file)

setup(name = meta.name,
        version = meta.version,
        description = meta.description,
        url = meta.description,
        author = meta.author,
        author_email = meta.author_email,
        license = meta.license,
        packages = find_packages(),
        scripts = ['labots.py'],
        install_requires=['pyyaml', 'tornado', 'pydle', 'sqlitedict'],
        cmdclass = { 'install_scripts': labots_install_scripts },
        zip_safe = False)
