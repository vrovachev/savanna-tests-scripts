import urllib
import hashlib
import os.path
import logging
import getpass
import settings

from glanceclient.v1 import Client as glanceclient
from keystoneclient.v2_0 import Client as keystoneclient
from novaclient.v1_1 import Client as novaclient

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
LOGGER.addHandler(ch)


class Common():
    def __init__(self, controller_ip):
        self.controller_ip = controller_ip

    def _get_auth_url(self):
        LOGGER.debug('Slave-01 is {0}'.format(self.controller_ip))
        return 'http://{0}:5000/v2.0/'.format(self.controller_ip)

    def goodbye_security(self):
        auth_url = self._get_auth_url()
        nova = novaclient(username=settings.SERVTEST_USERNAME,
                          api_key=settings.SERVTEST_PASSWORD,
                          project_id=settings.SERVTEST_TENANT,
                          auth_url=auth_url)
        LOGGER.debug('Permit all TCP and ICMP in security group default')
        secgroup = nova.security_groups.find(name='default')
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='tcp',
                                         from_port=1,
                                         to_port=65535)
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='icmp',
                                         from_port=-1,
                                         to_port=-1)
        key_name = getpass.getuser()
        if not nova.keypairs.findall(name=key_name):
            LOGGER.debug("Adding keys")
            with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
                nova.keypairs.create(name=key_name, public_key=fpubkey.read())
        try:
            flavor = nova.flavors.find(name='savanna')
        except:
            LOGGER.debug("Adding savanna flavor")
            nova.flavors.create('savanna', 2048, 1, 40)

    def check_image(self, url, image, md5,
                    path=settings.SERVTEST_LOCAL_PATH):
        download_url = "{0}/{1}".format(url, image)
        local_path = os.path.expanduser("{0}/{1}".format(path, image))
        LOGGER.debug('Check md5 {0} of image {1}/{2}'.format(md5, path, image))
        if not os.path.isfile(local_path):
            urllib.urlretrieve(download_url, local_path)
        with open(local_path, mode='rb') as fimage:
            digits = hashlib.md5()
            while True:
                buf = fimage.read(4096)
                if not buf:
                    break
                digits.update(buf)
            md5_local = digits.hexdigest()
        if md5_local != md5:
            LOGGER.debug('MD5 is not correct, download {0} to {1}'.format(
                         download_url, local_path))
            urllib.urlretrieve(download_url, local_path)
        return True

    def image_import(self, properties, local_path, image, image_name):
        LOGGER.debug('Import image {0}/{1} to glance'.
                     format(local_path, image))
        auth_url = self._get_auth_url()
        LOGGER.debug('Auth URL is {0}'.format(auth_url))
        keystone = keystoneclient(username=settings.SERVTEST_USERNAME,
                                  password=settings.SERVTEST_PASSWORD,
                                  tenant_name=settings.SERVTEST_TENANT,
                                  auth_url=auth_url)
        token = keystone.auth_token
        LOGGER.debug('Token is {0}'.format(token))
        glance_endpoint = keystone.service_catalog.url_for(
            service_type='image', endpoint_type='publicURL')
        LOGGER.debug('Glance endpoind is {0}'.format(glance_endpoint))
        glance = glanceclient(endpoint=glance_endpoint, token=token)
        LOGGER.debug('Importing {0}'.format(image))
        with open(os.path.expanduser('{0}/{1}'.format(local_path,
                                                      image))) as fimage:
            glance.images.create(name=image_name, is_public=True,
                                 disk_format='qcow2',
                                 container_format='bare', data=fimage,
                                 properties=properties)


if __name__ == "__main__":
    import sys
    controller = (sys.argv[1])
    common_func = Common(controller)
    for image_info in settings.images:
        common_func.check_image(
            image_info['url'],
            image_info['image'],
            image_info['md5sum'])
        common_func.image_import(
            image_info['meta'],
            settings.SERVTEST_LOCAL_PATH,
            image_info['image'],
            image_info['name'])
    common_func.goodbye_security()

LOGGER.debug('All done !')

print("HDP cluster:\n"
      "Creating:\n"
      "Worker - ['TASKTRACKER', 'DATANODE', 'HDFS_CLIENT', "
      "'MAPREDUCE_CLIENT']\n"
      "Master - ['JOBTRACKER', 'NAMENODE', 'SECONDARY_NAMENODE',"
      " 'GANGLIA_SERVER', 'NAGIOS_SERVER' 'AMBARI_SERVER']\n")
print("Testing:\n"
      "sudo su hdfs\n"
      "cd /usr/lib/hadoop\n"
      "hadoop jar hadoop-examples.jar pi 10 10\n")

print("Vanilla cluste r:\n"
      "Testing:\n"
      "sudo su - hadoop\n"
      "cd /usr/share/hadoop/\n"
      "hadoop jar hadoop-examples-1.2.1.jar pi 10 10\n")
