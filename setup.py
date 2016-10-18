from distutils.core import setup

name = 'pluginphotodynam'
version = 'devel'
description = 'PHOEBE 2.0 plugin to run a modified version of Josh Carter\'s photodynam code'

setup(name=name,
      version=version,
      description=description,
      packages = [name])
