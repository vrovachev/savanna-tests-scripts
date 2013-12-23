
import urllib
import hashlib
import os.path

import settings

from glanceclient.v1 import Client as glanceclient
from keystoneclient.v2_0 import Client as keystoneclient
from novaclient.v1_1 import Client as novaclient



class Common():
    def __init__(self, controller_ip):
        self.controller_ip = controller_ip

    def _get_auth_url(self):
        print('Slave-01 is {0}'.format(self.controller_ip))
        return 'http://{0}:5000/v2.0/'.format(self.controller_ip)

    def goodbye_security(self):
        auth_url = self._get_auth_url()
        nova = novaclient(username=settings.SERVTEST_USERNAME,
                          api_key=settings.SERVTEST_PASSWORD,
                          project_id=settings.SERVTEST_TENANT,
                          auth_url=auth_url)
        print('Permit all TCP and ICMP in security group default')
        secgroup = nova.security_groups.find(name='default')
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='tcp',
                                         from_port=1,
                                         to_port=65535)
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='icmp',
                                         from_port=-1,
                                         to_port=-1)
        key_name = 'sgalkin'
        if not nova.keypairs.findall(name=key_name):
            print("Adding keys")
            with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
                nova.keypairs.create(name=key_name, public_key=fpubkey.read())
        if not flavor = nova.flavors.find(name='m1.small'):
            nova.flavors.create('savanna',2048,1,40)

    def image_import(self, properties, local_path, image, image_name):
        print('Import image {0}/{1} to glance'.
                     format(local_path, image))
        auth_url = self._get_auth_url()
        print('Auth URL is {0}'.format(auth_url))
        keystone = keystoneclient(username=settings.SERVTEST_USERNAME,
                                  password=settings.SERVTEST_PASSWORD,
                                  tenant_name=settings.SERVTEST_TENANT,
                                  auth_url=auth_url)
        token = keystone.auth_token
        print('Token is {0}'.format(token))
        glance_endpoint = keystone.service_catalog.url_for(
            service_type='image', endpoint_type='publicURL')
        print('Glance endpoind is {0}'.format(glance_endpoint))
        glance = glanceclient(endpoint=glance_endpoint, token=token)
        print('Importing {0}'.format(image))
        with open('{0}/{1}'.format(local_path, image)) as fimage:
            glance.images.create(name=image_name, is_public=True,
                                 disk_format='qcow2',
                                 container_format='bare', data=fimage,
                                 properties=properties)


common_func = Common('172.18.92.84')
common_func.image_import(
    settings.SERVTEST_SAVANNA_IMAGE_META,
    settings.SERVTEST_LOCAL_PATH,
    settings.SERVTEST_SAVANNA_IMAGE,
    settings.SERVTEST_SAVANNA_IMAGE_NAME)
common_func.image_import(
    settings.SERVTEST_SAVANNA_IMAGE_META_2,
    settings.SERVTEST_LOCAL_PATH,
    settings.SERVTEST_SAVANNA_IMAGE_2,
    settings.SERVTEST_SAVANNA_IMAGE_NAME_2)
common_func.goodbye_security()

print('All done !')
print ("HDP cluster:"
       "Worker - ['TASKTRACKER', 'DATANODE', 'HDFS_CLIENT', 'MAPREDUCE_CLIENT']"
       "Master - ['JOBTRACKER', 'NAMENODE', 'SECONDARY_NAMENODE', 'GANGLIA_SERVER', 'NAGIOS_SERVER' 'AMBARI_SERVER']")
print ("sudo su hdfs"
       "cd /usr/lib/hadoop"
       "hadoop jar hadoop-examples.jar pi 10 10")

print("Vanilla cluster:"
      "ubuntu@vvvv-v-master-001:~$ sudo su - hadoop"
      "cd /usr/share/hadoop/"
      "hadoop jar hadoop-examples-1.2.1.jar pi 10 10")
