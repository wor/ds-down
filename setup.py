# -*- coding: utf-8 -*- vim:fenc=utf-8:ft=python:et:sw=4:ts=4:sts=4
from setuptools import setup, find_packages
import sys
import os

here = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(here, 'README.rst')).read() if os.path.exists("README.rst") else ""
NEWS = open(os.path.join(here, 'NEWS.rst')).read() if os.path.exists("NEWS.rst") else ""

version      = '0.1'
author       ='Esa Määttä'
author_email ='esa.maatta@iki.fi'

filt_args = []
exec_name="ds_down"
for i, arg in enumerate(sys.argv):
    if arg.startswith("--exec_name="):
        exec_name=arg[len("--exec_name="):]
        sys.argv.pop(i)
        break

console_scripts = [
        '{}=wor.ds_down:main'.format(exec_name),
        ]

# Remove console scripts if "--no-console_scripts" option given
if "--no-console-scripts" in sys.argv[1:]:
    console_scripts = []
    sys.argv.remove("--no-console-scripts")


install_requires = []

setup(name='ds-down',
    version=version,
    description="Synology Download Station url adder.",
    long_description=README + '\n\n' + NEWS,
    classifiers=[c.strip() for c in """
         Development Status :: 4 - Beta
         License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)
         Environment :: Console
         Programming Language :: Python :: 3
         Operating System :: POSIX :: Linux
         Topic :: Utilities
         """.split('\n') if c.strip()],
    keywords='Synology DownloadStation console cli',
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    url='http://github.com/wor/ds-down',
    license='GPL3',
    package_data = {
            '': ['*.rst', 'ds-down.conf', 'ds-down.desktop'],
            },
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    data_files=[
            ('share/ds-down/doc', ['ds-down.conf', 'ds-down.desktop', 'README.rst']),
            ],
    include_package_data=True,
    zip_safe=False,
    # Requirements
    install_requires=install_requires,
    tests_require=['nose'],
    entry_points={
        'console_scripts': console_scripts
    },
    test_suite='nose.collector',
)
