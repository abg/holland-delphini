# coding: utf-8
"""
    delphini.backend
    ~~~~~~~~~~~~~~~~

    Delphini backend API for generating MySQL cluster backups

    :copyright: 2010-2011 by Andrew Garner
    :license: BSD, see LICENSE.rst for details
"""

import os
import logging
from subprocess import list2cmdline
from delphini.util import ssh, rsync, query_ndb, run_cluster_backup
from delphini.error import ClusterError, ClusterCommandError

LOG = logging.getLogger(__name__)

def archive_data_nodes(dsn,
                       backup_id,
                       ssh_user,
                       keyfile,
                       target_path):
    """Archive the backups specified by ``backup_id`` on the data nodes

    :param dsn: connection string to use to query the data nodes involved
    :param backup_id: backup_id of of the backup to archive on each node
    :param ssh_user: ssh user to use when archiving data
    :param keyfile: ssh keyfile to use for authentication

    :raises: ClusterError on failure
    """
    nodes = query_ndb(dsn, query=['nodegroup', 'nodeid', 'backupdatadir'])
    results = []
    for node in nodes:
        query = nodes[node]
        host = '%s@%s' % (ssh_user, node)
        remote_path = os.path.join(query.backupdatadir,
                                   'BACKUP',
                                   'BACKUP-%d' % backup_id)
        try:
            ssh(host,
                'ls -lah ' + list2cmdline([remote_path]),
                keyfile=keyfile)
        except ClusterCommandError, exc:
            if exc.status != 255:
                LOG.error("Error when checking Backup path. "
                          "Skipping backups for node %d", query.nodeid)
                continue
            # status == 255 errors are probably fatal
            raise

        rsync(host, keyfile, list2cmdline([remote_path]), target_path)
        LOG.info("Archived node %s with backup id %d", node, backup_id)
        results.append(query)

    groups = set([query.nodegroup for query in nodes.values()])
    # verify node groups
    for node in results:
        if node.nodegroup in groups:
            groups.remove(node.nodegroup)
    if groups:
        for group in groups:
            LOG.error("Node group %s does not have backup coverage", group)
        raise ClusterError("Failed to backup one or more node groups")

    if len(nodes) != len(results):
        LOG.warning("One or more nodes appears to be down but all node "
                    "groups had a successful backup")

def purge_backup(dsn, backup_id, ssh_user, keyfile):
    """Purge backups for a particular backup-id"""
    nodes = query_ndb(dsn, query=['backupdatadir'])
    for node in nodes:
        query = nodes[node]
        host = '%s@%s' % (ssh_user, node)
        remote_path = os.path.join(query.backupdatadir,
                                   'BACKUP',
                                   'BACKUP-%d' % backup_id)
        ssh(host,
            'rm -fr %s' % list2cmdline([remote_path]),
            keyfile=keyfile)

def backup(dsn, ssh_user, ssh_keyfile, target_path):
    """Backup a MySQL cluster"""
    backup_id, stop_gcp = run_cluster_backup(dsn=dsn)
    archive_data_nodes(dsn=dsn,
                       backup_id=backup_id,
                       ssh_user=ssh_user,
                       keyfile=ssh_keyfile,
                       target_path=target_path)
    purge_backup(dsn, backup_id, ssh_user, ssh_keyfile)
    return backup_id, stop_gcp
