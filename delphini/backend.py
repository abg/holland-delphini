
"""Utility methods for mysql cluster backups"""

import os
import logging
from delphini.util import ssh, log_stop_gcp, query_ndb, run_cluster_backup, \
                          list2cmdline
from delphini.error import ClusterError, ClusterCommandError

LOG = logging.getLogger(__name__)

def archive_data_nodes(dsn,
                       backup_id,
                       ssh_user,
                       keyfile,
                       open_file=open):
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

        ssh(host,
            'tar -cf - -C %s .' % list2cmdline([remote_path]),
            keyfile=keyfile,
            stdout=open_file("backup_%s_%d.tar" % (node, backup_id), 'w')
        )
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

def backup(dsn, ssh_user, ssh_keyfile, open_file):
    """Backup a MySQL cluster"""
    backup_id, stop_gcp = run_cluster_backup(dsn=dsn)
    archive_data_nodes(dsn=dsn,
                       backup_id=backup_id,
                       ssh_user=ssh_user,
                       keyfile=ssh_keyfile,
                       open_file=open_file)
    log_stop_gcp(open_file('replication.info', 'w', level=0), stop_gcp)
    purge_backup(dsn, backup_id, ssh_user, ssh_keyfile)
    return backup_id, stop_gcp
