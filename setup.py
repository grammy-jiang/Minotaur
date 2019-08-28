from setuptools import setup

import versioneer

setup(
    cmdclass=versioneer.get_cmdclass(),
    entry_points={"console_scripts": ["minotaur = minotaur.cmdline:execute"]},
    version=versioneer.get_version(),
)
