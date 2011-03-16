Generating MySQL Cluster Backups
================================

MySQL Cluster backups are a complex beast.  A ``START BACKUP`` directive is
sent to a management node which instructs each of the data nodes to dump backup
files to their respective BackupDataDir.  To restore you will need to collect
those backup files in order to reapply them to the data nodes.

The Delphini backup plugin attemps to make this process much easier with
holland.  A backup directive is issued to a management node and once that
succeeds delphini will ssh into each of the data nodes and retrieve the backup
files to a centralized location.

.. _holland-config:

Holland Backupset Configuration
===============================

Holland uses standard ini-like config files in .conf files - one for each
backup configuration.  A sample config file for delphini might look like this:

::
  [holland:backup]
  plugin = delphini # this can also be 'mysql-cluster'

  [mysql-cluster]
  connect-string 	= 127.0.0.1
  default-ssh-user 	= mysql
  default-ssh-keyfile	= /etc/holland/holland.key

  [compression]
  method		= gzip
  level			= 6

``[holland:backup]`` is a standard section that defines config values common in
all backup config files.  The only required piece of information here is what
plugin you want to use - for delphini this will be called ``delphini`` but is
also aliased to ``mysql-cluster``.  Additional parameters may be specified here
to adjust how holland purges old and failed backups when running backups with
this configuration.  For more information see:
`hollandbackup.org <http://hollandbackup.org>`_

``[mysql-cluster]`` is the main section for delphini with the parameters needed
to connect to the cluster and its data nodes.  Currently only three parameters
are supported:

  * ``connect-string`` to be able to connect to a management node and issue a
    backup directive.  This defaults to localhost so if backups are run on the
    management server no further configuration is necessary.
  * ``default-ssh-user`` to specify what user to use when connecting to the
    data node servers. This defaults to 'root', but another user is strongly
    recommended.
  * ``default-ssh-keyfile`` to specify an ssh key to use for authentication to
    the data node servers.  This must be specified in order to successfully
    authenticate with a remote server.  See :ref:`generating-ssh-keys`

``[compression]`` is a standard configuration section for using holland's
configurable compression support.  Holland 1.0 currently supports several
compression methods:

  * gzip and pigz (parallel gzip)
  * bzip2 and pbzip2 (parallel bzip2)
  * lzop
  * lzma/xz

Further the compression level can be set to 0 or the compression method set to
``none`` to completely disable compression.


.. _generating-ssh-keys:

Generating SSH Keys
===================

Generally you will use the ssh-keygen command to generate an SSH key on linux.

This will generate both a public and private key.  The public key (e.g.
id_rsa.pub) should be copied to each data node and put in the 
``default-ssh-user``'s ``~/.ssh/authorized_keys`` file.  The private key (e.g.
id_rsa) should be copied to some location readable by the holland process.

::

  $ ssh-keygen -t rsa
  $ scp ~/.ssh/id_rsa.pub each.data_node1.server:.ssh/authorized_keys2
  $ sudo cp -a ~/.ssh/id_rsa /etc/holland/holland.key

Required Permissions
====================

To copy files on each data node the ``default-ssh-user`` will need read access
to the node's ``BackupDataDir``.  This will usually be the same as ``DataDir``
unless this has been changed.  I like to use /var/lib/mysql-cluster/ as mysql
cluster's ``DataDir`` and backups will be saved under
/var/lib/mysql-cluster/BACKUPS/.

If you want Delphini to also purge backups once they have been copied off the
server the ``default-ssh-user`` will also need access to delete files under the
``BackupDataDir``.  If ndbd is started as the system root user then this will
mean that ``default-ssh-user`` will also need to be root.

Reporting Bugs
==============

Report bugs against Delphini to the Holland projects at `launchpad
<http://launchpad.net/holland-backup>_`.

Getting the Code
================

If you want to look at the code for Delphini you can checkout or fork the code
at `GitHub <http://github.com/abg/holland-delphini>`_

