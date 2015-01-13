#!/usr/bin/env python

from distutils import log
from distutils.command.build_ext import build_ext as _build_ext
from distutils.core import setup, Extension
import os


class BuildWebSQL(_build_ext):
    def run(self):
        path = os.path.abspath(os.path.join('extra', 'websqlclient'))
        log.info("building 'websqlclient' library")
        pwd = os.getcwd()
        temp_dir = os.path.join(self.build_temp, 'websqlclient')
        self.mkpath(temp_dir)
        os.chdir(temp_dir)
        try:
            self.spawn(['cmake', path, '-DDISABLE_SHARED=on', '-DWITH_PIC=1'])
            self.spawn(['make'])
        finally:
            os.chdir(pwd)

        self.include_dirs.extend([os.path.join(temp_dir, 'include'), os.path.join(path, 'include')])
        self.libraries.append('websqlclient')
        self.library_dirs.append(os.path.join(temp_dir, 'libmysql'))

        zlib_path = os.path.join(temp_dir, 'zlib')
        if os.path.exists(zlib_path):
            self.library_dirs.append(zlib_path)
            self.libraries.append('zlib')

        ssl_path = os.path.join(temp_dir, 'extra', 'yassl')
        if os.path.exists(ssl_path):
            self.library_dirs.extend((ssl_path, os.path.join(ssl_path, 'taocrypt')))
            self.libraries.extend(('yassl', 'taocrypt'))

        self.extensions[0].depends.append(os.path.join(temp_dir, 'libmysql', 'libwebsqlclient.a'))
        in_file = os.path.join(temp_dir, 'include', 'mysqld_error.h')
        out_file = os.path.join(temp_dir, 'py_mysqld_error.c')
        self.make_er(in_file, out_file)
        self.extensions[0].sources.append(out_file)
        super().run()

    @staticmethod
    def make_er(in_file, out_file):
        with open(in_file, 'rb') as mysqld_errors:
            with open(out_file, 'wb') as py_errors:
                py_errors.write(b"/* Autogenerated file, please don't edit */\n")
                py_errors.write(b"#include <mysqld_error.h>\n")
                py_errors.write(b"#define PY_SSIZE_T_CLEAN 1\n#include <Python.h>\n\n")
                py_errors.write(b"int _mysql_constants_add_err(PyObject* module) {\n")
                for line in mysqld_errors:
                    if not line.startswith(b'#define'):
                        continue
                    name = line.split()[1]
                    py_errors.write(b"    if (PyModule_AddIntMacro(module, " + name + b") < 0) return -1;\n")
                py_errors.write(b"    return 0;\n")
                py_errors.write(b"}\n")


__name__ = "websql"
__version__ = "1.1.0"

extra_link_args = ["-lstdc++"]

module1 = Extension('_' + __name__,
                    sources=["./src/connections.c",
                             "./src/constants.c",
                             "./src/exceptions.c",
                             "./src/fields.c",
                             "./src/format.c",
                             "./src/mysqlmod.c",
                             "./src/results.c"],
                    libraries=['ssl', 'crypto'],
                    extra_compile_args=["-Os", "-g", "-fno-strict-aliasing", "-std=c99"],
                    extra_link_args=["-lstdc++"] + os.getenv('WEBSQL_EXTRA_LINKER_ARGS', '').split(),
                    define_macros=[
                        ("MODULE_NAME", '_' + __name__),
                        ("version_info", "(%d, %d, %d, 'beta', 0)" % tuple(map(int, __version__.split('.')))),
                        ("__version__", __version__)
                    ])

setup(
    name=__name__,
    version=__version__,
    description='Asynchronous Python interface to MySQL',
    cmdclass={'build_ext': BuildWebSQL},
    ext_modules=[module1],
    py_modules=[
        "websql._types",
        "websql.connections",
        "websql.converters",
        "websql.cursors",
        "websql.release",
        "websql.times"
    ],
    author="@bg",
    author_email='gaifullinbf@gmail.com',
    maintainer='@bg',
    maintainer_email='gaifullinbf@gmail.com',
    url='https://github.com/bgaifullin/web-sql',
    license='GPL',
    long_description="""\
=========================
Asynchronous Python interface for MySQL
=========================
\n
MySQLdb is an asynchronous interface to the popular MySQL_ database server for
Python.  The design goals are:
\n
- Compatibility with Python3 asyncio package
\n
- Compatibility with WebScale fork of MySQL
\n
- Compliance with Python database API version 2.0 [PEP-0249]_
\n
- Thread-safety
\n
- Thread-friendliness (threads will not block each other)
\n
MySQL-3.23 through 5.1 and Python-2.3 through 2.5 are currently
supported.
\n
MySQLdb is `Free Software`_.
\n
.. _MySQL: http://www.mysql.com/
.. _`Free Software`: http://www.gnu.org/
.. [PEP-0249] http://www.python.org/peps/pep-0249.html
      """,
    classifiers=[
        "Development Status :: 5 - Beta",
        "Environment :: Other Environment",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "Programming Language :: C",
        "Programming Language :: Python3",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
    ]
)

# to build debug
# CFLAGS='-Wall -O0 -g' python3 setup.py build
