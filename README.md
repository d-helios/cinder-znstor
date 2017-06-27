# Cinder driver for znstord daemon

## Example cinder configuration
```angular2html
[znstor]
znstor_domain = default
znstor_pool = tank
znstor_project = openstack
quota = 5120
thin_volumes = True
compression = lz4
oversubs_ratio = 100
management_addr = 172.30.50.82:10987
portal_addr = 172.30.50.82:3260
portal_iqn = iqn.2017-06.znstor.io:01:981dbd97c5c7
target_group = tank-tg2
znstor_user = znstor
znstor_password = znstor
volume_driver=cinder.volume.drivers.znstor.znstiscsi.ZNSTORISCSIDriver
```
* __znstor_domain__ - domain name which represents as first filesystem within zpool (ex: tank/__mydomain__). Different domains my bellong to different organizations;
* __znstor_pool__ - zfs pool in which domain and project is located;
* __znstor_project__ - project in which cinder volumes is located;
* __qouta__ - project quota in gigabytes;
* __thin_volumes__ - create thin or thick volumes;
* __compression__ - enable / disable compression;
* __oversubs_ratio__ - oversubscription ratio;
* __management_addr__ - znstor managment address;
* __portal_addr__ - iscsi target portal address, including port;
* __portal_iqn__ - iscsi target iqn;
* __target_group__ - iscsi target group;
* __znstor_user__ - znstor user;
* __znstor_password__ - znstor password;
* __volume_driver__ - volume driver.

## TODO
* volume migration
* image to volume / volume to image
* backup
