# Copyright 2009-2014 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from distutils.command.build_py import build_py
from distutils.command.build_scripts import build_scripts
from distutils.command.install_scripts import install_scripts
from distutils.command.sdist import sdist
import glob
import os.path
import sys

from setuptools import find_packages, setup

from euca2ools import __version__


REQUIREMENTS = ['lxml',
                'requestbuilder>=0.2.0-pre3',
                'requests',
                'six>=1.4']
if sys.version_info < (2, 7):
    REQUIREMENTS.append('argparse')


# Cheap hack:  install symlinks separately from regular files.
# cmd.copy_tree accepts a preserve_symlinks option, but when we call
# ``setup.py install'' more than once the method fails when it encounters
# symlinks that are already there.

class build_scripts_except_symlinks(build_scripts):
    '''Like build_scripts, but ignoring symlinks'''
    def copy_scripts(self):
        orig_scripts = self.scripts
        self.scripts = [script for script in self.scripts
                        if not os.path.islink(script)]
        build_scripts.copy_scripts(self)
        self.scripts = orig_scripts


class install_scripts_and_symlinks(install_scripts):
    '''Like install_scripts, but also replicating nonexistent symlinks'''
    def run(self):
        install_scripts.run(self)
        # Replicate symlinks if they don't exist
        for script in self.distribution.scripts:
            if os.path.islink(script):
                target = os.readlink(script)
                newlink = os.path.join(self.install_dir,
                                       os.path.basename(script))
                if not os.path.exists(newlink):
                    os.symlink(target, newlink)


class build_py_with_git_version(build_py):
    '''Like build_py, but also hardcoding the version in __init__.__version__
       so it's consistent even outside of the source tree'''

    def build_module(self, module, module_file, package):
        build_py.build_module(self, module, module_file, package)
        print module, module_file, package
        if module == '__init__' and '.' not in package:
            version_line = "__version__ = '{0}'\n".format(__version__)
            old_init_name = self.get_module_outfile(self.build_lib, (package,),
                                                    module)
            new_init_name = old_init_name + '.new'
            with open(new_init_name, 'w') as new_init:
                with open(old_init_name) as old_init:
                    for line in old_init:
                        if line.startswith('__version__ ='):
                            new_init.write(version_line)
                        else:
                            new_init.write(line)
                new_init.flush()
            os.rename(new_init_name, old_init_name)


class sdist_with_git_version(sdist):
    '''Like sdist, but also hardcoding the version in __init__.__version__ so
       it's consistent even outside of the source tree'''

    def make_release_tree(self, base_dir, files):
        sdist.make_release_tree(self, base_dir, files)
        version_line = "__version__ = '{0}'\n".format(__version__)
        old_init_name = os.path.join(base_dir, 'euca2ools/__init__.py')
        new_init_name = old_init_name + '.new'
        with open(new_init_name, 'w') as new_init:
            with open(old_init_name) as old_init:
                for line in old_init:
                    if line.startswith('__version__ ='):
                        new_init.write(version_line)
                    else:
                        new_init.write(line)
            new_init.flush()
        os.rename(new_init_name, old_init_name)


setup(name="euca2ools",
      version=__version__,
      description="Eucalyptus Command Line Tools",
      long_description="Eucalyptus Command Line Tools",
      author="Eucalyptus Systems, Inc.",
      author_email="support@eucalyptus.com",
      url="http://www.eucalyptus.com",
      scripts=sum((glob.glob('bin/euare-*'),
                   glob.glob('bin/euca-*'),
                   glob.glob('bin/euform-*'),
                   glob.glob('bin/eulb-*'),
                   glob.glob('bin/euscale-*'),
                   glob.glob('bin/euwatch-*')),
                  []),
      data_files=[('share/man/man1', glob.glob('man/*.1'))],
      packages=find_packages(),
      install_requires=REQUIREMENTS,
      license='BSD (Simplified)',
      platforms='Posix; MacOS X',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'Intended Audience :: System Administrators',
                   'License :: OSI Approved :: Simplified BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Internet'],
      cmdclass={'build_py': build_py_with_git_version,
                'build_scripts': build_scripts_except_symlinks,
                'install_scripts': install_scripts_and_symlinks,
                'sdist': sdist_with_git_version})
