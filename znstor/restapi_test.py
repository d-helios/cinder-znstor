import uuid
import restapi

storage = restapi.Znstor(
    managment_address='172.30.50.82:10987',
    pool='tank',
    domain='default',
    user='znstor',
    passwd='znstor'
)


def test_project_create():
    for i in xrange(3):
        project_name = str(uuid.uuid4())
        alias = str(uuid.uuid4())
        result = storage.project_create(
            project_name, quota=500 * 1024 ** 2, alias=alias)
        assert result["project"] == project_name


def test_project_list():
    projects = storage.project_list()
    assert len(projects) > 0


def test_project_get():
    projects = storage.project_list()
    for project in projects:
        current_project = storage.project_get(project["project"])
        assert current_project["project"] == project["project"]


def test_project_set():
    projects = storage.project_list()
    for project in projects:
        modified_project = storage.project_set(
            project=project['project'], quota=2 * 1024 ** 2)
        print modified_project
        assert modified_project['options']['quota'] == 2 * 1024 ** 2


def test_project_exists():
    projects = storage.project_list()
    for project in projects:
        assert storage.project_exists(project["project"])


def test_create_volume():
    project_name = str(uuid.uuid4())
    project_alias = str(uuid.uuid4())
    result = storage.project_create(
        project_name, quota=500 * 1024 ** 2, alias=project_alias)
    assert result["project"] == project_name

    volume = storage.volume_create(project_name, alias="MyVolume", volsize=200 * 1024 ** 2,
                                   options={"thin": True, "reservation": 50 * 1024 ** 2})
    # check that volume create successfully
    assert volume["alias"] == "MyVolume"


def test_resize_volume():
    project_name = str(uuid.uuid4())
    project_alias = str(uuid.uuid4())
    result = storage.project_create(
        project_name, quota=500 * 1024 ** 2, alias=project_alias)
    assert result["project"] == project_name

    volume = storage.volume_create(project_name, alias="MyVolume", volsize=200 * 1024 ** 2,
                                   options={"thin": True, "reservation": 50 * 1024 ** 2})

    assert volume["alias"] == "MyVolume"

    volume = storage.volume_resize(
        project=project_name, volume=volume['id'], volume_size=300 * 1024 ** 2)
    assert volume["vol"]["options"]["volsize"] == 300 * 1024 ** 2 == volume["lu"]["Size"]
    storage.volume_destroy(project_name, volume['id'])
    storage.project_destroy(project_name)


def test_compression():
    project_name = str(uuid.uuid4())
    project_alias = str(uuid.uuid4())
    result = storage.project_create(
        project_name, quota=500 * 1024 ** 2, alias=project_alias)
    assert result["project"] == project_name

    volume = storage.volume_create(project_name, alias="MyVolume", volsize=200 * 1024 ** 2,
                                   options={"thin": True, "reservation": 50 * 1024 ** 2})

    assert volume["alias"] == "MyVolume"

    volume = storage.volume_compression(
        project=project_name, volume=volume['id'], compression='gzip')
    assert volume["vol"]["options"]["compression"] == 'gzip'
    storage.volume_destroy(project_name, volume['id'])
    storage.project_destroy(project_name)


def test_snapshot_and_clones():
    project_name = str(uuid.uuid4())
    project_alias = str(uuid.uuid4())
    snapshot_name = str(uuid.uuid4())
    result = storage.project_create(
        project_name, quota=500 * 1024 ** 2, alias=project_alias)
    assert result["project"] == project_name

    volume = storage.volume_create(project_name, alias="MyVolume", volsize=200 * 1024 ** 2,
                                   options={"thin": True, "reservation": 50 * 1024 ** 2})
    assert volume["alias"] == "MyVolume"

    # create volume snapshot
    snapshot = storage.volume_create_snapshot(
        project_name, volume['id'], snapshot_name)
    assert snapshot["dataset"].split("@")[-1] == snapshot_name

    # create clone
    clone = storage.volume_create_from_snapshot(project_name, volume['id'],
                                                snapshot_name, 'Clone1')
    assert clone['alias'] == 'Clone1'
    assert clone['vol']['options']['origin'].split('/')[-1].split('@')[0] == volume['vol']['dataset'].split('/')[-1]

    # rollback original volume
    volume = storage.volume_rollback_snapshot(
        project_name, volume['id'], snapshot_name)
    assert volume["alias"] == "MyVolume"

    # destroy volume
    storage.volume_destroy(project_name, clone['id'])

    # destroy snapshot
    storage.volume_destroy_snapshot(
        project_name, volume['id'], snapshot_name)

    # destroy volume
    storage.volume_destroy(project_name, volume['id'])

    # destroy project
    storage.project_destroy(project_name)


def test_export_volumes():
    project_name = str(uuid.uuid4())
    project_alias = str(uuid.uuid4())
    result = storage.project_create(
        project_name, quota=500 * 1024 ** 2, alias=project_alias)
    assert result['project'] == project_name

    volume = storage.volume_create(project_name, alias="exportedVolume", volsize=200 * 1024 ** 2,
                                   options={"thin": True})
    assert volume['alias'] == 'exportedVolume'

    target_group1 = storage.targetgroup_create('target_group1')
    host_group1 = storage.hostgroup_create('host_group1')
    host_group2 = storage.hostgroup_create('host_group2')
    host_group1 = storage.hostgroup_add_member(host_group1['HostGroup'], 'iqn.1994-05.com.redhat:f253a269fe1')
    host_group2 = storage.hostgroup_add_member(host_group2['HostGroup'], 'iqn.1994-05.com.redhat:f223a169fe2')
    assert len(host_group1['Members']) == 1
    assert len(host_group2['Members']) == 1

    volume = storage.volume_export(project_name, volume['id'], host_group1['HostGroup'],
                                   target_group1['TargetGroup'], 1)
    assert len(volume['views']) == 1

    volume = storage.volume_export(project_name, volume['id'], host_group2['HostGroup'],
                                   target_group1['TargetGroup'], 1)
    assert len(volume['views']) == 2

    volume = storage.volume_unexport(project_name, volume['id'], host_group2['HostGroup'],
                                     target_group1['TargetGroup'], 1)
    assert len(volume['views']) == 1

    storage.volume_destroy(project_name, volume['id'])
    storage.hostgroup_delete(host_group1['HostGroup'])
    storage.hostgroup_delete(host_group2['HostGroup'])
    storage.targetgroup_delete(target_group1['TargetGroup'])
    storage.project_destroy(project_name)


def test_snapshots():
    project_name = str(uuid.uuid4())
    project_alias = str(uuid.uuid4())
    result = storage.project_create(
        project_name, quota=500 * 1024 ** 2, alias=project_alias)
    assert result["project"] == project_name

    volume = storage.volume_create(project_name, alias="MyVolume", volsize=200 * 1024 ** 2,
                                   options={"thin": True, "reservation": 50 * 1024 ** 2})
    assert volume["alias"] == "MyVolume"

    for snap_index in xrange(4):
        snapshot = storage.volume_create_snapshot(project_name, volume['id'], "snapshot_%d" % snap_index)
        assert snapshot["dataset"].split("@")[-1] == "snapshot_%d" % snap_index

    for snapshot in storage.volume_list_snapshot(project_name, volume['id']):
        snapshot_name = snapshot['dataset'].split('@')[-1]
        storage.volume_destroy_snapshot(
            project_name, volume['id'], snapshot_name)

    storage.volume_destroy(project_name, volume['id'])


def test_destroy_all_volumes():
    projects = storage.project_list()
    if projects is not None:
        for project in projects:
            volumes = storage.volume_list(project["project"])
            if volumes is not None:
                for volume in volumes:
                    volume = storage.volume_get(
                        project["project"], volume['id'])
                    storage.volume_destroy(project['project'], volume['id'])


def test_project_destroy():
    projects = storage.project_list()
    if projects is not None:
        for project in projects:
            storage.project_destroy(project["project"])
            assert not storage.project_exists(project["project"])


def test_hostgroup():
    # create hostgroup test
    for index in xrange(10):
        hostgroup = storage.hostgroup_create("hostgroup_%d" % index)
        assert hostgroup['HostGroup'] == "hostgroup_%d" % index

    hostgroups = storage.hostgroup_list()
    if hostgroups:
        # test add member to hostgroup
        for index in xrange(len(hostgroups)):
            initiator = "iqn.1994-05.com.redhat:e253ac69fe%x" % index
            storage.hostgroup_add_member(
                hostgroups[index]['HostGroup'], initiator)
            hostgroup = storage.hostgroup_get(hostgroups[index]['HostGroup'])
            assert len(hostgroup["Members"]) == 1

        for index in xrange(len(hostgroups)):
            initiator = "iqn.1994-05.com.redhat:e253ac79fe%x" % index
            storage.hostgroup_add_member(
                hostgroups[index]['HostGroup'], initiator)
            hostgroup = storage.hostgroup_get(hostgroups[index]['HostGroup'])
            assert len(hostgroup["Members"]) == 2

        # test remove member from hostgroup
        for index in xrange(len(hostgroups)):
            initiator = "iqn.1994-05.com.redhat:e253ac79fe%x" % index
            storage.hostgroup_remove_member(
                hostgroups[index]['HostGroup'], initiator)
            hostgroup = storage.hostgroup_get(hostgroups[index]['HostGroup'])
            assert len(hostgroup["Members"]) == 1

        # test remove hostgroup
        for hostgroup in hostgroups:
            storage.hostgroup_delete(hostgroup['HostGroup'])
        assert len(storage.hostgroup_list()) == 0
    else:
        assert False

# def test_TargetGroup():
#     # create targetgroup test
#     for index in xrange(10):
#         targetgroup = storage.targetgroup_create("targetgroup_%d" % index)
#         assert targetgroup['TargetGroup'] == "targetgroup_%d" % index
#
#     targetgroups = storage.targetgroup_list()
#     if targetgroups:
#         # test destroy targetgroup
#         for targetgroup in targetgroups:
#             if targetgroup['TargetGroup'][:12] == 'targetgroup':
#                 storage.targetgroup_delete(targetgroup['TargetGroup'])
