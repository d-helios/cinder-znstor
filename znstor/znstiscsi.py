from oslo_config import cfg
from oslo_log import log
from oslo_utils import units
from cinder import exception
from cinder import interface
from cinder.volume import driver
from cinder.volume.drivers.znstor import restapi as znstor_restapi

CONF = cfg.CONF
LOG = log.getLogger(__name__)

OPTS = [
    cfg.StrOpt('znstor_domain',
               help='storage domain.'),
    cfg.StrOpt('znstor_pool',
               help='zpool id.'),
    cfg.StrOpt('znstor_project',
               help='project'),
    cfg.IntOpt('quota',
               help='project quota in gb.'),
    cfg.BoolOpt('thin_volumes', default=True,
                help='thin-provisioned volumes: True, False.'),
    cfg.StrOpt('compression', default='lzjb',
               help='volume compression: lz4, lzjb, off'),
    cfg.StrOpt('oversubs_ratio',
               help='oversubscription ratio.'),
    cfg.StrOpt('management_addr',
               help='znstor cluster resource group management address.'),
    cfg.StrOpt('portal_addr', default='',
               help='ISCSI Target Portal'),
    cfg.StrOpt('portal_iqn', default='',
               help='ISCSI Target IQN'),
    cfg.StrOpt('target_group', default='tg-openstack',
               help='TargetGroup'),
    cfg.StrOpt('znstor_user', help='username'),
    cfg.StrOpt('znstor_password', help='password')
]

CONF.register_opts(OPTS)


@interface.volumedriver
class ZNSTORISCSIDriver(driver.ISCSIDriver):
    """ZNStor cinder driver implementation"""

    vendor_name = 'ZNStor'
    driver_version = '0.0.1'
    protocol = 'iSCSI'

    def __init__(self, *args, **kwargs):
        super(ZNSTORISCSIDriver, self).__init__(*args, **kwargs)

        self.configuration.append_config_values(OPTS)
        self.lcfg = self.configuration

        self.storage = znstor_restapi.Znstor(
            management_address=self.lcfg.management_addr,
            pool=self.lcfg.znstor_pool,
            domain=self.lcfg.znstor_domain,
            user=self.lcfg.znstor_user,
            passwd=self.lcfg.znstor_password,
        )

    def do_setup(self, context):
        """Setup project"""
        if self.lcfg.znstor_project not in [project['project'] for project in self.storage.project_list()]:
            try:
                self.storage.project_create(
                    self.lcfg.znstor_project, quota=int(self.lcfg.quota * units.Gi))
            except znstor_restapi.ZnstorBadRequest as e:
                LOG.error(e)
                raise exception.VolumeBackendAPIException(
                    data="ZNSTOR. backend initialization failed. Err: %s" % str(e)
                )
            except Exception as e:
                LOG.error(e)
                raise exception.VolumeBackendAPIException(
                    data="ZNSTOR. unknown exception. Err: %s" % str(e)
                )

        # get current project property
        project = self.storage.project_get(self.lcfg.znstor_project)

        # check quota properties
        self.storage.project_set(project['project'], quota=int(self.lcfg.quota * units.Gi))
        self.storage.project_set(project['project'], compression=self.lcfg.compression)

    def check_for_setup_error(self):
        """Check if setup ended successfully"""
        project = self.storage.project_get(self.lcfg.znstor_project)
        if project['project'] != self.lcfg.znstor_project:
            LOG.error('ZNSTOR. Project is not initialize. check_for_setup failed.')
            raise exception.VolumeBackendAPIException(
                data="ZNSTOR. Project is not initialize. Project is %s" % str(project)
            )

    # noinspection PyArgumentList,PyArgumentList
    def _update_volume_stats(self):
        """update backend statistics"""
        project = self.storage.project_get(self.lcfg.znstor_project)

        data = {}
        data['vendor_name'] = self.vendor_name
        data['volume_backend_name'] = 'znstor'
        data['driver_version'] = self.driver_version
        data['storage_protocol'] = 'iscsi'
        data['pools'] = []

        single_pool = {}
        # noinspection PyArgumentList
        single_pool.update(
            pool_name=project['project'],
            total_capacity_gb=project['options']['quota'] / units.Gi,
            free_capacity_gb=project['options']['available'] / units.Gi,
            location_info='None',
            QoS_support=False,
            provisioned_capacity_gb=project['options']['used'] / units.Gi,
            max_over_subscription_ratio=int(self.lcfg.oversubs_ratio),
            thin_provisioning_support=True,
            thick_provisioning_support=True,
            total_volumes=0,
            multiattach=True,
        )

        # add volume count information
        try:
            vols_list = self.storage.volume_list(project['project'])
            # noinspection PyArgumentList
            # TODO: must return empty array if no one volume exist
            single_pool.update(total_volumes=len(vols_list))
        except znstor_restapi.ZnstorObjectNotFound as e:
            # TODO: remove this exception
            # There is no project within the project.
            pass

        data['pools'].append(single_pool)
        self._stats = data

    def create_volume(self, volume):
        """create volume"""
        volsize = volume['size'] * units.Gi
        volalias = volume['name']

        try:
            self.storage.volume_create(self.lcfg.znstor_project, alias=volalias, volsize=volsize,
                                       options={
                                           "thin": True,
                                           "compression": 'lz4'
                                       })
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.error(e)
            raise exception.VolumeBackendAPIException(message=
                                                      "ZNSTOR. delete volume failed with error. Err: %s" % str(e))

    def delete_volume(self, volume):
        """delete volume"""
        alias = volume['name']
        try:
            lu_uuid = self.storage.volume_get_by_alias(self.lcfg.znstor_project, alias)['LUName']
            self.storage.volume_destroy(self.lcfg.znstor_project, lu_uuid)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.error(e)
            raise exception.VolumeIsBusy(
                message="Err: %s. Volume: %s" % (str(e), volume['name']))

    def initialize_connection(self, volume, connector):
        alias = volume['name']

        # get volume that should be exported to host
        try:
            vol = self.storage.volume_get_by_alias(
                self.lcfg.znstor_project, alias)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.debug("ZNSTOR. Can't export volume. Err: %s" % str(e))
            raise exception.VolumeBackendAPIException(
                message="Volume export failed: %s" % volume['name'])

        # ensure that initiator host is present on storage
        initiator_iqn = connector['initiator']
        initiator_host = connector['host']

        try:
            hostgroups = self.storage.hostgroup_list()
            if initiator_host not in [hg['HostGroup'] for hg in hostgroups]:
                self.storage.hostgroup_create(initiator_host)
                self.storage.hostgroup_add_member(initiator_host, initiator_iqn)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.debug("ZNSTOR. Can't check/create hostgroup")
            raise exception.VolumeBackendAPIException(message="Volume export failed: %s" % volume['name'])

        iscsi_properties = {}
        # check if volume already exported to client

        views = self.storage.volume_exports(self.lcfg.znstor_project, vol['LUName'])

        if len(views) > 0:
            for view in views:
                if view['HostGroup'] == initiator_host and view['TargetGroup'] == self.lcfg.target_group:
                    iscsi_properties['target_discovered'] = False
                    iscsi_properties['target_portal'] = self.lcfg.portal_addr
                    iscsi_properties['target_iqn'] = self.lcfg.portal_iqn
                    iscsi_properties['target_lun'] = view['LUN']
                    iscsi_properties['volume_id'] = vol['SerialNum']
                    iscsi_properties['discard'] = True
                    return {
                        'driver_volume_type': 'iscsi',
                        'data': iscsi_properties
                    }

        self.storage.volume_export(
            self.lcfg.znstor_project, vol['LUName'], initiator_host, self.lcfg.target_group, -1)

        views = self.storage.volume_exports(self.lcfg.znstor_project, vol['LUName'])
        for view in views:
            if view['HostGroup'] == initiator_host and view['TargetGroup'] == self.lcfg.target_group:
                iscsi_properties['target_discovered'] = False
                iscsi_properties['target_portal'] = self.lcfg.portal_addr
                iscsi_properties['target_iqn'] = self.lcfg.portal_iqn
                iscsi_properties['target_lun'] = view['LUN']
                iscsi_properties['volume_id'] = vol['SerialNum']
                iscsi_properties['discard'] = True
                return {
                    'driver_volume_type': 'iscsi',
                    'data': iscsi_properties
                }

    def terminate_connection(self, volume, connector, **kwargs):
        """Driver entry point to terminate connection for a volume"""
        alias = volume['name']
        try:
            vol = self.storage.volume_get_by_alias(self.lcfg.znstor_project, alias)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.debug("ZNSTOR. Can't export volume. Err: %s" % str(e))
            raise exception.VolumeBackendAPIException(message="Volume export failed: %s" % volume['name'])

        initiator_iqn = connector['initiator']
        initiator_host = connector['host']
        views = self.storage.volume_exports(self.lcfg.znstor_project, vol['LUName'])
        if len(views) > 0:
            for view in views:
                if view['HostGroup'] == initiator_host and view['TargetGroup'] == self.lcfg.target_group:
                    self.storage.volume_unexport(
                        self.lcfg.znstor_project, vol['LUName'], initiator_host, self.lcfg.target_group, -1)

    def clone_image(self, volume, image_location, image_id, image_meta, image_service):
        # TODO: need to implements
        pass

    def create_volume_from_snapshot(self, volume, snapshot):
        new_vol_alias = volume['name']
        parent_vol_alias = snapshot['volume_name']
        snapname = snapshot['name']

        try:
            parent_vol = self.storage.volume_get_by_alias(self.lcfg.znstor_project, parent_vol_alias)
            self.storage.volume_create_from_snapshot(
                self.lcfg.znstor_project, parent_vol['id'], snapname, new_vol_alias)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.error(e)
            raise exception.VolumeBackendAPIException(
                message="ZNSTOR. delete volume failed with error. Err: %s" % str(e))

    def delete_snapshot(self, snapshot):
        alias = snapshot['volume_name']
        snapshot_name = snapshot['name']
        try:
            vol = self.storage.volume_get_by_alias(self.lcfg.znstor_project, alias)
            self.storage.volume_destroy_snapshot(self.lcfg.znstor_project, vol['LUName'], snapshot_name)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.error('Snapshot %s: has clones. Err: %s' % (snapshot['name'], e))
            raise exception.SnapshotIsBusy(snapshot_name=snapshot['name'])

    def create_snapshot(self, snapshot):
        alias = snapshot['volume_name']
        snapname = snapshot['name']

        try:
            vol = self.storage.volume_get_by_alias(self.lcfg.znstor_project, alias)
            self.storage.volume_create_snapshot(self.lcfg.znstor_project, vol['LUName'], snapname)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.error(e)
            raise exception.VolumeBackendAPIException(
                message="ZNSTOR. delete volume failed with error. Err: %s" % str(e))

    def extend_volume(self, volume, new_size):
        try:
            alias = volume['name']
            vol = self.storage.volume_get_by_alias(self.lcfg.znstor_project, alias)
            self.storage.volume_resize(self.lcfg.znstor_project, vol['LUName'], new_size * units.Gi)
        except znstor_restapi.ZnstorBadRequest as e:
            LOG.error(e)
            raise exception.VolumeBackendAPIException(
                message="ZNSTOR. delete volume failed with error. Err: %s" % str(e))

    def create_export(self, context, volume, connector):
        pass

    def remove_export(self, context, volume):
        pass

    def ensure_export(self, context, volume):
        pass

    def create_cloned_volume(self, volume, src_vref):
        pass

    def migrate_volume(self, context, volume, host):
        # TODO: Need implementation
        pass
