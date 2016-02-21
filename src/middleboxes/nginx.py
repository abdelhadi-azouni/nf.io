"""
Check the documentation in __init__.py for more information on the methods in
this module.
"""

from vnfs_operations import VNFSOperations
import os
import logging
import getpass
import errno
import errors
"""
special_files is a list of files specific to this VNF that requires special
handling while reading. For example, if a read system call is issued for
rx_bytes, then the VNF instance needs to be queried for the number of bytes it
has received and that is returned as the read data.

action_files contains a list of files that are used to represent different
action on a VNF. For example, writing 'stop' to 'action' will stop a VNF
instance.
"""

special_files = { 'rx_bytes':'rx_bytes', 
                  'tx_bytes':'tx_bytes', 
                  'pkt_drops':'pkt_drops', 
                  'status':'status', 
                  'vm.ip' : 'vm_ip',
                  'action': 'action'}

logger = logging.getLogger(__name__)

def full_path(root, partial_path):
    if partial_path.startswith("/"):
        partial_path = partial_path[1:]
    return os.path.join(root, partial_path)

def get_nf_config(vnfs_ops, full_nf_path):
    # nf_path for calling vnfs_op function
    tokens = full_nf_path.encode('ascii').split('/')
    last_index_to_keep = tokens.index('nf-types') + 3
    nf_path = "/".join(tokens[0:last_index_to_keep])

    # get info about nf
    nf_instance_name, nf_type, host, nf_image_name = vnfs_ops.vnfs_get_instance_configuration(nf_path)
    return {'nf_image_name':nf_image_name,
            'nf_instance_name':nf_instance_name,
            'host':host,
            'username':getpass.getuser()
            }

def _mkdir(root, path, mode):
    vnfs_ops = VNFSOperations(root)
    result = vnfs_ops.vnfs_create_vnf_instance(path, mode)
    return result

def _getattr(root, path, fh=None):
    vnfs_ops = VNFSOperations(root)
    f_path = full_path(root, path)
    st = os.lstat(f_path)
    file_name = vnfs_ops.vnfs_get_file_name(f_path)
    return_dictionary = dict()
    return_dictionary['st_atime'] = st.st_atime
    return_dictionary['st_ctime'] = st.st_ctime
    return_dictionary['st_gid'] = st.st_gid
    return_dictionary['st_mode'] = st.st_mode
    return_dictionary['st_mtime'] = st.st_mtime
    return_dictionary['st_nlink'] = st.st_nlink
    return_dictionary['st_size'] = st.st_size
    return_dictionary['st_uid'] = st.st_uid
    if file_name in special_files:
       return_dictionary['st_size'] = 1000
    return return_dictionary

def _read(root, path, length, offset, fh):
    f_path = full_path(root, path)
    vnfs_ops = VNFSOperations(root)
    file_name = vnfs_ops.vnfs_get_file_name(f_path)
    nf_path = ''
    ret_str = ''
    if file_name in special_files and special_files[file_name]+'_read' in globals():

        try:
            nf_config = get_nf_config(vnfs_ops, f_path)
            # call the custom read function
            logger.info('Reading ' + file_name  + ' from ' +
                nf_config['nf_instance_name'] + '@' + nf_config['host'])
            ret_str = globals()[special_files[file_name]+'_read'](vnfs_ops._hypervisor,
                nf_config)
            logger.info('Successfully read ' + file_name +
                ' from ' + nf_config['nf_instance_name'] + '@' + nf_config['host'])
        except errors.nfioError, ex:
            logger.error('Failed to read ' + file_name +
                ' from ' + nf_config['nf_instance_name'] + '@' + nf_config['host'] +
                ' : ' + ex.__class__.__name__)
            #raise OSError(ex.errno, os.strerror(ex.errno))
        if offset >= len(ret_str):
            ret_str = ''
    else:
        os.lseek(fh, offset, os.SEEK_SET)
        ret_str = os.read(fh, length)
    return ret_str

def _write(root, path, buf, offset, fh):
    f_path = full_path(root, path)
    vnfs_ops = VNFSOperations(root)
    file_name = vnfs_ops.vnfs_get_file_name(f_path)
    #if file_name == "action":
    if file_name in special_files and special_files[file_name]+'_write' in globals():
        try:
            nf_config = get_nf_config(vnfs_ops, f_path)
            # call the custom write function
            logger.info('Writing to ' + file_name  + ' in ' +
                nf_config['nf_instance_name'] + '@' + nf_config['host'])
            ret_str = globals()[special_files[file_name]+'_write'](vnfs_ops._hypervisor,
                nf_config, buf.rstrip("\n"))
            logger.info('Successfully wrote ' + file_name +
                ' in ' + nf_config['nf_instance_name'] + '@' + nf_config['host'])
        except errors.nfioError, ex:
            logger.error('Failed to write ' + file_name +
                ' in ' + nf_config['nf_instance_name'] + '@' + nf_config['host'] +
                ' : ' + ex.__class__.__name__)
            #raise OSError(ex.errno, os.strerror(ex.errno))
        os.lseek(fh, offset, os.SEEK_SET)
        os.write(fh, buf.rstrip("\n"))
        return len(buf)
    else:
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)


def rx_bytes_read(hypervisor_driver, nf_config):
    command = "ifconfig eth0 | grep -Eo 'RX bytes:[0-9]+' | cut -d':' -f 2"
    return hypervisor_driver.execute_in_guest(nf_config['host'],
              nf_config['username'], nf_config['nf_instance_name'], command)

def tx_bytes_read(hypervisor_driver, nf_config):
    command = "ifconfig eth0 | grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2"
    return hypervisor_driver.execute_in_guest(nf_config['host'],
              nf_config['username'], nf_config['nf_instance_name'], command)

def pkt_drops_read(hypervisor_driver, nf_config):
    command = "ifconfig eth0 | grep -Eo 'RX .* dropped:[0-9]+' | cut -d':' -f 4"
    return hypervisor_driver.execute_in_guest(nf_config['host'],
              nf_config['username'], nf_config['nf_instance_name'], command)

def status_read(hypervisor_driver, nf_config):
    return hypervisor_driver.guest_status(nf_config['host'],
              nf_config['username'], nf_config['nf_instance_name'])

def vm_ip_read(hypervisor_driver, nf_config):
    return hypervisor_driver.get_ip(nf_config['host'],
              nf_config['username'], nf_config['nf_instance_name'])


"""
nginx specific
def _start(hypervisor_driver, nf_config):
    command = "/user/bin nginx"
    return hypervisor_driver.execute_in_guest(nf_config['host'],
              nf_config['nf_id'], command)
def _nginx_signal(hypervisor_driver, nf_config, signal):
    if signal not in ["stop", "quit", "reload", 'reopen']:
        logger.info("invalid signal")
    else:
        command = "nginx -s %s" % signal
    return hypervisor_driver.execute_in_guest(nf_config['host'],
              nf_config['nf_id'], command)

def command_write(hypervisor_driver, nf_config, command):
    if command == "start":
        command = "/usr/bin nginx"
    #try:
    return hypervisor_driver.execute_in_guest(nf_config['host'],
        nf_config['nf_id'], "nginx "+command)
    #except ValueError:
    #    logger.info('invalid command')
"""

def action_write(hypervisor_driver, nf_config, data):
    if data == "activate":
        logger.info('Deploying new VNF instance ' + nf_config['nf_instance_name'] +
            ' @ ' + nf_config['host'])
        nf_id = hypervisor_driver.deploy(nf_config['host'], nf_config['username'],
            nf_config['nf_image_name'], nf_config['nf_instance_name'])
        logger.info('VNF deployed, now starting VNF instance ' +
            nf_config['nf_instance_name'] + ' @ ' + nf_config['host'])
        try:
            hypervisor_driver.start(nf_config['host'], nf_config['username'], nf_config['nf_instance_name'])
            logger.info('Successfully started VNF instance ' +
                nf_config['nf_instance_name'] + ' @ ' + nf_config['host'])
        except errors.VNFStartError:
            logger.error('Attempt to start ' + nf_config['nf_instance_name'] +
                '@' + nf_config['host'] + ' failed. Destroying depoyed VNF.')
            try:
                hypervisor_driver.destroy(nf_config['host'], nf_config['username'], nf_config['nf_instance_name'])
                logger.info('Successfully destroyed ' +
                    nf_config['nf_instance_name'] + '@' + nf_config['host'])
                # the VNF was deployed, but failed to start so...
                raise errors.VNFDeploymentError
            except errors.VNFDestroyError:
              logger.error('Failed to destroy partially activated VNF instance ' +
                  nf_config['nf_instance_name'] + '@' + nf_config['host'] +
                  '. VNF is in inconsistent state.')
              raise errors.VNFDeployErrorWithInconsistentState
    elif data == "stop":
        logger.info('Stopping VNF instance ' +  nf_config['nf_instance_name'] +
            '@' + nf_config['host'])
        hypervisor_driver.stop(nf_config['host'], nf_config['username'],
            nf_config['nf_instance_name'])
        logger.info(nf_config['nf_instance_name'] + '@' + nf_config['host'] +
            ' successfully stopped')
    elif data == "start":
        logger.info('Starting VNF instance ' +  nf_config['nf_instance_name'] +
            '@' + nf_config['host'])
        hypervisor_driver.start(nf_config['host'], nf_config['username'],
            nf_config['nf_instance_name'])
        logger.info(nf_config['nf_instance_name'] + '@' + nf_config['host'] +
            ' successfully started')
    elif data == "destroy":
        logger.info('Destroying VNF instance ' +  nf_config['nf_instance_name'] +
            '@' + nf_config['host'])
        hypervisor_driver.destroy(nf_config['host'], nf_config['username'],
            nf_config['nf_instance_name'])
        logger.info(nf_config['nf_instance_name'] + '@' + nf_config['host'] +
            ' successfully destroyed')

    elif data == "ifconfig":
        print hypervisor_driver.execute_in_guest(nf_config['host'],
              nf_config['username'], nf_config['nf_instance_name'], "ifconfig")
    elif data == "run-nginx":
        print hypervisor_driver.execute_in_guest(nf_config['host'],
              nf_config['username'], nf_config['nf_instance_name'], "cd /usr/bin; nginx")



