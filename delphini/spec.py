# coding: utf-8
"""
    delphini.spec
    ~~~~~~~~~~~~~

    Defines the configspec for the delphini backup plugin. This is used by
    Holland to generate new config files and to validate configs passed to this
    plugin.

    :copyright: 2010-2011 by Andrew Garner
    :license: BSD, see LICENSE.rst for details
"""

CONFIGSPEC = """
[mysql-cluster]
connect-string      = string(default='localhost')
default-ssh-user    = string(default='root')
default-ssh-keyfile = string(default=None)

[compression]
method              = option(gzip, pigz, bzip2, lzop, lzma, default=gzip)
level               = integer(min=0, max=9)
inline              = boolean(default=yes)
""".splitlines()
