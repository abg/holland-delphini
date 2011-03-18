# coding: utf-8
"""
    delphini.plugin
    ~~~~~~~~~~~~~~~

    Implements a backup plugin for holland 1.0 which is exposed as
    holland.backup entrypoint in the delphini package.

    :copyright: 2010-2011 by Andrew Garner
    :license: BSD, see LICENSE.rst for details
"""

import os
import glob
import logging
try:
    from holland.core.exceptions import BackupError
except ImportError:
    # be nice to sphinx
    BackupError = Exception
from delphini.spec import CONFIGSPEC
from delphini.backend import backup
from delphini.util import run_command
from delphini.error import ClusterError

LOG = logging.getLogger(__name__)

class DelphiniPlugin(object):
    """MySQL Cluster Backup Plugin implementation for Holland"""

    def __init__(self, name, config, target_directory, dry_run=False):
        config.validate_config(self.configspec())
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run

    def estimate_backup_size(self):
        """Estimate the backup size"""
        # XXX: implement I_S querying or ssh du -sh perhaps
        return 0

    def backup(self):
        """Run a MySQL cluster backup"""
        config = self.config['mysql-cluster']
        dsn = config['connect-string']
        ssh_user = config['default-ssh-user']
        ssh_keyfile = config['default-ssh-keyfile']
        target_path = os.path.join(self.target_directory, 'data')
        try:
            os.mkdir(target_path)
        except OSError, exc:
            raise BackupError("Failed to create %s: %s", (target_path, exc))

        try:
            backup_id, stop_gcp = backup(dsn,
                                         ssh_user,
                                         ssh_keyfile,
                                         target_path)
        except ClusterError, exc:
            raise BackupError(exc)

        cluster_info = os.path.join(self.target_directory,
                                    'cluster_backup.info')
        try:
            fileobj = open(cluster_info, 'w')
        except IOError, exc:
            raise BackupError("Failed to create %s: %s", (cluster_info, exc))

        try:
            try:
                fileobj.write("stopgcp = %s\n" % stop_gcp)
                fileobj.write("backupid = %s\n" % backup_id)
            except IOError, exc:
                raise BackupError("Failed to write %s: %s",
                                  (cluster_info, exc))
        finally:
            fileobj.close()

        compression = self.config['compression']['method']

        if compression != 'none':
            path = os.path.join(self.target_directory,
                                'BACKUP-%d' % backup_id,
                                '*')
            args = [
                compression,
                '-v',
                '-%d' % self.config['compression']['level'],
            ]
            if compression == 'lzop':
                # ensure lzop removes the old files once they're compressed
                args.insert(1, '--delete')
            for path in glob.glob(path):
                run_command(args + [path])

    @classmethod
    def configspec(cls):
        """Provide the config specification for the delphini plugin"""
        return CONFIGSPEC

    @staticmethod
    def info():
        """Provide additional info about this backup"""
        return ""
