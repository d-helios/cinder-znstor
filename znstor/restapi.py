# -*- coding: utf-8 -*-
"""Module restapi - implement simple interface to communicate with znstor daemon.
"""
from restclient import RestClientURL
# TODO: replace pointer to array in GO


class ZnstorObjectNotFound(Exception):
    def __init__(self, object=None, debug=None, payload=None):
        self.object = object
        self.debug = debug
        self.payload = payload

    def __str__(self):
        return "Object not found. Object %s, Debug: %s, Payload: %s" % (
            self.object,
            self.debug,
            self.payload
        )


class ZnstorBadRequest(Exception):
    def __init__(self, object=None, debug=None, payload=None):
        self.object = object
        self.debug = debug
        self.payload = payload

    def __str__(self):
        return "Bad request. Object %s, Debug: %s, Payload: %s" % (
            self.object,
            self.debug,
            self.payload
        )


class Znstor(object):
    def __init__(self, **kwargs):
        """
        :key management_address: Storage management interface (ip or dns)
        :key api_version: Storage RestApi version (only v1 supported)
        :key pool: zpoolID
        :key domain: znstor domainID, actually is first level dataset in pool.
        :key timeout: request timeout. Default is 180 seconds.
        :key user: znstor user
        :key passwd: znstor password
        """
        self.rest = RestClientURL(**kwargs)

    def project_create(self, project, **kwargs):
        """
        :param project: Project name to create
        :return: Created project structure
        """
        result = self.rest.post(
            "{base_path}/{project_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name=project
            ), kwargs
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(object="{base_path}/{project_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project
                ),
                debug=result.text
            )

    def project_destroy(self, project):
        """
        :param project: Project name to destroy
        :return: None in case of operation completed successfully and raise exception in case of failed 
        """
        result = self.rest.delete(
            "{base_path}/{project_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name=project
            ),
        )

        if result.status_code != 200:
            raise ZnstorBadRequest(object="{base_path}/{project_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project
                ),
                debug=result.text
            )

    def project_list(self):
        """
        :return: project list in case of completed successfully and raise exception in case of failed 
        """
        result = self.rest.get(self.rest.projects_base_path())

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(object=self.rest.projects_base_path(), debug=result.text)

    def project_get(self, project):
        """
        :param: project_name: project name
        :return: project list in case of completed successfully and raise exception in case of failed 
        """
        result = self.rest.get(
            "{base_path}/{project_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name=project
            )
        )

        if result.status_code != 200:
            raise ZnstorBadRequest("{base_path}/{project_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project
                ),
                debug=result.text
            )
        return result.json()

    def project_set(self, project, **kwargs):
        """
        :param: project_name: project name to change
        :key: alias: project alias
        :key: quota: project quota in bytes
        :key: refquota: referenced quota in bytes
        :key: reservation: reservation in bytes
        :key: refreservation: referenced reservation in bytes
        :key: compression: compression [off|lz4|lzjb|gzip]
        :key: dedup: deduplication. Strongly recommended do not enable this property until you are sure what are
        you doing. [on|off]
        :key: atime: enable/disable access time. [on|off]
        :return: project structure
        """
        result = self.rest.put(
            "{base_path}/{project_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name = project
            ),
            kwargs
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name = project
                ),
                debug=result.text,
                payload=kwargs
            )

    def project_exists(self, project):
        """Check if project exists
        :param: project_name: project name to check
        :return: boolean
        """
        result = self.rest.get(
            "{base_path}/{project_name}/exists".format(
                base_path=self.rest.projects_base_path(),
                project_name=project
            )
        )

        if result.status_code == 200:
            return True
        else:
            return False

    def volume_create(self, project, **kwargs):
        """
        :param: *project_name: project
        :key: *alias: volume alias
        :key: serial: volume serial (wwid)
        :key: *volsize: volume size
        :key: guid: luID of the volume. Needed when resizing volume.
        :key: volblocksize: can be applied only while volume creation.
        :key: reservation: volume reservation size.
        :key: dedup: enable volume deduplication
        :key: thin: create thin volume
        :return: volume object
        """
        result = self.rest.post(
            "{base_path}/{project_name}/volumes".format(
                base_path=self.rest.projects_base_path(),
                project_name=project
            ), kwargs
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(object= "{base_path}/{project_name}/volumes".format(
                base_path=self.rest.projects_base_path(),
                project_name=project
            ),
                payload=kwargs,
                debug=result.text
            )

    def volume_destroy(self, project, volume):
        """
        :param project: projectID
        :param volume: volumeID
        :return: 
        """
        result = self.rest.delete(
            "{base_path}/{project_name}/volumes/{volume_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume
            )
        )

        if result.status_code == 200:
            return  result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume
                ),
                debug=result.text
            )

    def volume_list(self, project):
        """
        Get Volume List
        :param project: list all volumes within a project 
        :return: volumes array
        """
        result = self.rest.get(
            "{base_path}/{project_name}/volumes".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                ),
                debug=result.text
            )

    def volume_get(self, project, volume):
        """
        Get Volume
        :param project: projectID
        :param volume:  volumeID
        :return: volume object
        """
        #result = self.rest.get(self.rest.projects_base_path() + "/" + project + "/volumes/" + volume)
        result = self.rest.get(
            "{base_name}/{project_name}/volumes/{volume_name}".format(
                base_name=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_name}/{project_name}/volumes/{volume_name}".format(
                    base_name=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume
                ),
                debug=result.text
            )


    def volume_get_by_alias(self, project, alias):
        """
        Get Volume by alias
        :param project: projectID
        :param alias: volume alias
        :return: volume object
        """
        volumes = self.volume_list(project)
        for vol in volumes:
            if vol['alias'] == alias:
                return vol

    def volume_resize(self, project, volume, volume_size):
        """
        Resize volume.
        :param project
        :param volume: volumeID
        :param volume_size: new size in bytes
        :return: volume object
        """
        result = self.rest.put(
            "{base_path}/{project_name}/volumes/{volume_name}/resize".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume,
            ),
            {'volsize': volume_size}
        )
        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/resize".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume,
                ),
                payload={'volsize': volume_size},
                debug=result.text
            )

    def volume_compression(self, project, volume, compression):
        """
        Enable/Disable volume compression
        :param project: projectID
        :param volume: volumeID
        :param key compression: [lz4|lzjb|gzip|off]
        :return:
        """
        result = self.rest.put(
            "{base_path}/{project_name}/volumes/{volume_name}/compression/{compression_type}".format(
                base_path=self.rest.projects_base_path(),
                volume_name=volume,
                compression_type=compression
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/compression/{compression_type}".format(
                    base_path=self.rest.projects_base_path(),
                    volume_name=volume,
                    compression_type=compression
                ),
                debug=result.text
            )

    def volume_create_snapshot(self, project, volume, snapshot):
        """
        Create snapshot
        :param project: Project ID
        :param volume:  Volume ID
        :param snapshot: Snapshot name
        :return:
        """
        result = self.rest.post(
            "{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume,
                snapshot_name=snapshot
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume,
                    snapshot_name=snapshot
                ),
                debug=result.text
            )

    def volume_create_from_snapshot(self, project, volume, snapshot, clone_alias):
        """
        Create snapshot
        :param project: Project ID
        :param volume:  Volume ID
        :param snapshot: Snapshot name
        :param clone_alias: Snapshot name
        :return:
        """
        result = self.rest.post(
            "{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}/clone".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume,
                snapshot_name=snapshot,
            ),
            {'alias': clone_alias}
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}/clone".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume,
                    snapshot_name=snapshot,
                ),
                debug=result.text,
                payload={'alias': clone_alias}
            )

    def volume_destroy_snapshot(self, project, volume, snapshot):
        """
        Destroy snapshot
        :param project: Project ID
        :param volume:  Volume ID
        :param snapshot: Snapshot name
        :return:
        """
        #result = self.rest.delete(
        #    self.rest.projects_base_path() + "/" + project + "/volumes/" + volume + "/snapshots/" + snapshot)
        result = self.rest.delete(
            "{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume,
                snapshot_name=snapshot,
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume,
                    snapshot_name=snapshot,
                ),
                debug=result.text
            )

    def volume_list_snapshot(self, project, volume):
        """
        List Volume snapshot
        :param project: project ID
        :param volume:  volume ID
        :return: array of snapshot objects
        """
        result = self.rest.get(
            "{base_path}/{project_name}/volumes/{volume_name}/snapshots".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume,
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/snapshots".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume,
                ),
                debug=result.text
            )

    def volume_get_snapshot(self, project, volume, snapshot):
        """
        Get Volume snapshot
        :param project: project ID
        :param volume:  volume ID
        :param snapshot: snapshot ID
        :return: snapshot object
        """
        result = self.rest.get(
            "{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume,
                snapshot_name=snapshot
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume,
                    snapshot_name=snapshot
                ),
                debug=result.text
            )

    def volume_rollback_snapshot(self, project, volume, snapshot):
        """
        Rollback volume to snapshot
        :param project: project ID
        :param volume: volume ID
        :param snapshot: snapshot ID
        :return:
        """
        #result = self.rest.put(
        #    self.rest.projects_base_path() + "/" + project + "/volumes/" + volume +
        #    "/snapshots/" + snapshot + "/rollback"
        #)
        result = self.rest.put(
            "{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}/rollback".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume,
                snapshot_name=snapshot
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/snapshots/{snapshot_name}/rollback".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume,
                    snapshot_name=snapshot
                ),
                debug=result.text
            )

    def volume_export(self, project, volume, hostgroup, targetgroup, lun=-1):
        """
        Export volume aka add view
        :param project: ProjectID
        :param volume: Volume guid
        :param hostgroup: Hostgroup name
        :param targetgroup: Targetgroup name
        :param lun: logical unit number
        :return: volume object
        """
        #result = self.rest.put(
        #    self.rest.projects_base_path() + "/" + project + "/volumes/" + volume
        #    + "/export", {'hostgroup': hostgroup, 'targetgroup': targetgroup, 'lun': lun}
        #)
        result = self.rest.put(
            "{base_path}/{project_name}/volumes/{volume_name}/export".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume
            ),
            {'hostgroup': hostgroup, 'targetgroup': targetgroup, 'lun': lun}
        )

        if result.status_code == 200:
            return self.volume_get(project, volume)
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/export".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume
                ),
                payload={'hostgroup': hostgroup, 'targetgroup': targetgroup, 'lun': lun},
                debug=result.text
            )

    def volume_unexport(self, project, volume, hostgroup, targetgroup, lun=-1):
        """
        Export volume aka add view
        :param project: ProjectID
        :param volume: Volume guid
        :param hostgroup: Hostgroup name
        :param targetgroup: Targetgroup name
        :param lun: logical unit number
        :return: volume object
        """
        result = self.rest.put(
            "{base_path}/{project_name}/volumes/{volume_name}/export".format(
                base_path=self.rest.projects_base_path(),
                project_name=project,
                volume_name=volume
            ),
            {'hostgroup': hostgroup, 'targetgroup': targetgroup, 'lun': lun}
        )

        if result.status_code == 200:
            return self.volume_get(project, volume)
        else:
            raise ZnstorBadRequest(
                object="{base_path}/{project_name}/volumes/{volume_name}/export".format(
                    base_path=self.rest.projects_base_path(),
                    project_name=project,
                    volume_name=volume
                ),
                payload={'hostgroup': hostgroup, 'targetgroup': targetgroup, 'lun': lun},
                debug=result.text
            )

    def hostgroup_create(self, hostgroup):
        """
        Create HostGroup
        :param hostgroup: hostgroup id
        :return: hostgroup object
        """
        result = self.rest.post(
            "{host_base_path}/{hostgroup_name}".format(
                host_base_path=self.rest.hosts_base_path(),
                hostgroup_name=hostgroup
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{host_base_path}/{hostgroup_name}".format(
                    host_base_path=self.rest.hosts_base_path(),
                    hostgroup_name=hostgroup
                ),
                debug=result.text
            )

    def hostgroup_list(self):
        """
        Get all available hostgroups
        :return: return hostgroup objects
        """
        result = self.rest.get(self.rest.hosts_base_path())

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object=self.rest.hosts_base_path(),
                debug=result.text
            )

    def hostgroup_get(self, hostgroup):
        """
        Get specified hostgroup
        :param hostgroup:  HostgroupID
        :return: hostgroup object
        """
        result = self.rest.get(
            "{host_base_path}/{hostgroup_name}".format(
                host_base_path=self.rest.hosts_base_path(),
                hostgroup_name=hostgroup
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{host_base_path}/{hostgroup_name}".format(
                    host_base_path=self.rest.hosts_base_path(),
                    hostgroup_name=hostgroup
                ),
                debug=result.text
            )

    def hostgroup_add_member(self, hostgroup, member):
        """
        Add member (IQN) to hostgroup.
        :param hostgroup: hostgroupID
        :param member: member IQN (wwn in case of FC)
        :return: hostgroup object
        """
        result = self.rest.put(
            "{host_base_path}/{hostgroup_name}/add/{member_iqn}".format(
                host_base_path=self.rest.hosts_base_path(),
                hostgroup_name=hostgroup,
                member_iqn=member
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{host_base_path}/{hostgroup_name}/add/{member_iqn}".format(
                    host_base_path=self.rest.hosts_base_path(),
                    hostgroup_name=hostgroup,
                    member_iqn=member
                ),
                debug=result.text
            )

    def hostgroup_remove_member(self, hostgroup, member):
        """
        Add member (IQN) to hostgroup.
        :param hostgroup: hostgroupID
        :param member: member IQN (wwn in case of FC)
        :return: hostgroup object
        """
        result = self.rest.put(
            "{host_base_path}/{hostgroup}/remove/{member_iqn}".format(
                host_base_path=self.rest.hosts_base_path(),
                hostgroup_name=hostgroup,
                member_iqn=member
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{host_base_path}/{hostgroup}/remove/{member_iqn}".format(
                    host_base_path=self.rest.hosts_base_path(),
                    hostgroup_name=hostgroup,
                    member_iqn=member
                ),
                debug=result.text
            )

    def hostgroup_delete(self, hostgroup):
        """
        Delete hostgroup
        :return: return null
        """
        result = self.rest.delete(
            "{host_base_path}/{hostgroup_name}".format(
                host_base_path=self.rest.hosts_base_path(),
                hostgroup_name=hostgroup
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{host_base_path}/{hostgroup_name}".format(
                    host_base_path=self.rest.hosts_base_path(),
                    hostgroup_name=hostgroup
                ),
                debug=result.text
            )

    def hostgroup_add_multihost_member(self, hostgroup, member):
        """
        Add member to multiple group
        :param hostgroup: hostgroupID
        :param member: member
        :return: hostgroup object
        """
        result = self.rest.put(
            "{host_base_path}/{hostgroup_name}/add/{member_iqn}/force".format(
                host_base_path=self.rest.hosts_base_path(),
                hostgroup_name=hostgroup,
                member_iqn=member
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{host_base_path}/{hostgroup_name}/add/{member_iqn}/force".format(
                    host_base_path=self.rest.hosts_base_path(),
                    hostgroup_name=hostgroup,
                    member_iqn=member
                ),
                debug=result.text
            )

    # targetgroup
    def targetgroup_create(self, targetgroup):
        """
        Create targetgroup
        :param targetgroup: targetgroup id
        :return: targetgroup object
        """
        result = self.rest.post(
            "{target_base_path}/tg/{targetgroup_name}".format(
                target_base_path=self.rest.targets_base_path(),
                targetgroup_name=targetgroup
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tg/{targetgroup_name}".format(
                    target_base_path=self.rest.targets_base_path(),
                    targetgroup_name=targetgroup
                ),
                debug=result.text
            )

    def targetgroup_list(self):
        """
        Get all available targetgroups
        :return: return targetgroup objects
        """
        result = self.rest.get(
            "{target_base_path}/tg".format(
                target_base_path=self.rest.targets_base_path()
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tg".format(
                    target_base_path=self.rest.targets_base_path()
                ),
                debug=result.text
            )

    def targetgroup_get(self, targetgroup):
        """
        Get specified hostgroup
        :param targetgroup:  TargetGroupID
        :return: targetgroup object
        """
        result = self.rest.get(
            "{target_base_path}/tg/{targetgroup_name}".format(
                target_base_path=self.rest.targets_base_path(),
                targetgroup_name=targetgroup
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tg/{targetgroup_name}".format(
                    target_base_path=self.rest.targets_base_path(),
                    targetgroup_name=targetgroup
                ),
                debug=result.text
            )

    def targetgroup_add_member(self, targetgroup, member):
        """
        Add member to targetgroup.
        :param targetgroup: targetgroupID
        :param member: target
        :return: hostgroup object
        """
        result = self.rest.put(
            "{target_base_path}/tg/{targetgroup_name}/add/{member_iqn}".format(
                target_base_path=self.rest.targets_base_path(),
                targetgroup_name=targetgroup,
                member_iqn=member
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tg/{targetgroup_name}/add/{member_iqn}".format(
                    target_base_path=self.rest.targets_base_path(),
                    targetgroup_name=targetgroup,
                    member_iqn=member
                ),
                debug=result.text
            )

    def targetgroup_remove_member(self, targetgroup, member):
        """
        Remove member from targetgroup.
        :param targetgroup: targetgroupID
        :param member: member
        :return: targetgroup object
        """
        result = self.rest.put(
            "{target_base_path}/tg/{targetgroup_name}/remove/{member_iqn}".format(
                target_base_path=self.rest.targets_base_path(),
                targetgroup_name=targetgroup,
                member_iqn=member
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tg/{targetgroup_name}/remove/{member_iqn}".format(
                    target_base_path=self.rest.targets_base_path(),
                    targetgroup_name=targetgroup,
                    member_iqn=member
                ),
                debug=result.text
            )

    def targetgroup_delete(self, targetgroup):
        """
        Delete targetgroup
        :return: return null
        """
        result = self.rest.delete(
            "{target_base_path}/tg/{targetgroup_name}".format(
                target_base_path=self.rest.targets_base_path(),
                targetgroup_name=targetgroup
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tg/{targetgroup_name}".format(
                    target_base_path=self.rest.targets_base_path(),
                    targetgroup_name=targetgroup,
                ),
                debug=result.text
            )

    def targetportgroup_create(self, tpg, ipaddrs):
        """
        Create target port group
        :param tpg: target port group name
        :param ipaddrs: list of ip addresses
        :return: target port group object
        """
        result = self.rest.post(
            "{target_base_path}/tpg/{targetportgroup_name}".format(
                target_base_path=self.rest.targets_base_path(),
                targetportgroup_name=tpg
            ),
            ipaddrs
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tpg/{targetportgroup_name}".format(
                    target_base_path=self.rest.targets_base_path(),
                    targetportgroup_name=tpg
                ),
                payload=ipaddrs,
                debug=result.text
            )

    def targetportgroup_delete(self, tpg):
        """
        Delete target port group
        :return: null
        """
        result = self.rest.delete(
            "{target_base_path}/tpg/{targetportgroup_name}".format(
                target_base_path=self.rest.targets_base_path(),
                targetportgroup_name=tpg
            )
        )

        if result.status_code == 200:
            return result.json()
        else:
            raise ZnstorBadRequest(
                object="{target_base_path}/tpg/{targetportgroup_name}".format(
                    target_base_path=self.rest.targets_base_path(),
                    targetportgroup_name=tpg
                ),
                debug=result.text
            )
