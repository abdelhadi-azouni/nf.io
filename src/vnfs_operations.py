#!/usr/bin/env python

from __future__ import with_statement

import os
from subprocess import Popen, PIPE
import sys
import errno
import time

import getpass
import re
from hypervisor import hypervisor_factory
from hypervisor import hypervisor_return_codes as hrc


class VNFSOperations:
    OP_UNDEFINED = 0xFF
    OP_NF = 0o01
    OP_CHAIN = 101

    def __init__(self, vnfs_root):
        self.vnfs_root = vnfs_root
        self._hypervisor = hypervisor_factory.HypervisorFactory.get_hypervisor_instance()

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.vnfs_root, partial)
        return path

    def vnfs_create_vnf_instance(self, path, mode):
        full_path = self._full_path(path)
        result = os.mkdir(full_path)
        default_file_mode = 0o644
        os.open(
            full_path +
            "/status",
            os.O_WRONLY | os.O_CREAT,
            default_file_mode)

        os.mkdir(full_path + "/config", mode)
        os.open(full_path + "/config/boot.conf", os.O_WRONLY | os.O_CREAT,
                default_file_mode)
        os.mkdir(full_path + "/machine", mode)
        os.open(full_path + "/machine/ip", os.O_WRONLY | os.O_CREAT,
                default_file_mode)
        os.open(full_path + "/machine/vm.vcpu", os.O_WRONLY | os.O_CREAT,
                default_file_mode)
        os.open(full_path + "/machine/vm.memory", os.O_WRONLY | os.O_CREAT,
                default_file_mode)
        os.open(full_path + "/machine/vm.image", os.O_WRONLY | os.O_CREAT,
                default_file_mode)
        os.open(full_path + "/action", os.O_WRONLY | os.O_CREAT,
                default_file_mode)

        default_file_mode = 0o444
        os.mkdir(full_path + "/stats", mode)
        os.open(full_path + "/stats/rx_bytes", os.O_WRONLY | os.O_CREAT,
                default_file_mode)
        os.open(full_path + "/stats/tx_bytes", os.O_WRONLY | os.O_CREAT,
                default_file_mode)
        os.open(full_path + "/stats/pkt_drops", os.O_WRONLY | os.O_CREAT,
                default_file_mode)

        return result

    def vnfs_get_opcode(self, path):
        tokens = self._full_path(path).encode('ascii').split('/')
        if "nf-types" in tokens:
            return VNFSOperations.OP_NF
        elif "chns" in tokens:
            return VNFSOperations.OP_CHAIN
        return VNFSOperations.OP_UNDEFINED

    def vnfs_create_chain(self, path, mode):
        full_path = self._full_path(path)
        result = 0
        result = os.mkdir(full_path)
        os.open(full_path + "/status", os.O_WRONLY | os.O_CREAT, mode)
        os.open(full_path + "/action", os.O_WRONLY | os.O_CREAT, mode)
        return result

    def vnfs_get_nf_type(self, path):
        tokens = self._full_path(path).encode('ascii').split('/')
        try:
            return tokens[tokens.index("nf-types") + 1]
        except ValueError:
            return ""
        except IndexError:
            return ""

    def vnfs_get_chain_name(self, path):
        tokens = self._full_path(path).encode('ascii').split('/')
        try:
            return tokens[tokens.index("chns") + 1]
        except ValueError:
            return ""
        except IndexError:
            return ""

    def vnfs_get_file_name(self, path):
        return path.split('/')[-1]

    def vnfs_is_nf_instance(self, path):
        tokens = self._full_path(path).encode('ascii').split('/')
        if ('nf-types' in tokens) and len(tokens) > tokens.index('nf-types') + \
                1:
            return True
        return False

    def vnfs_get_chain_elements(self, chain_root):
        return [directory[0] for directory in
                os.walk(chain_root)
                if directory[0] != chain_root]

    def vnfs_deploy_nf_chain(self, chain_root):
        nf_instances = self.vnfs_get_chain_elements(chain_root)
        nf_paths = [os.readlink(nf_path + "/" +
                                self.vnfs_get_file_name(nf_path))
                    for nf_path in nf_instances]
        ret_codes = [
            {nf_path: self.vnfs_deploy_nf(nf_path)} for nf_path in nf_paths]
        return ret_codes

    def vnfs_get_instance_configuration(self, nf_path):
        nf_instance_name = self.vnfs_get_file_name(nf_path)
        nf_type = self.vnfs_get_nf_type(nf_path)
        ip_address = ''
        print nf_path + '/machine/ip'
        with open(nf_path + '/machine/ip') as ip_fd:
            ip_address = ip_fd.readline().rstrip('\n')
        image_name = ''
        with open(nf_path + '/machine/vm.image') as img_fd:
            image_name = img_fd.readline().rstrip('\n')
        return nf_instance_name, nf_type, ip_address, image_name

    def vnfs_deploy_nf(self, nf_path):
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        print "Starting " + nf_instance_name + " of type " + nf_type + " at " + ip_address + " with image " + image_name
        cont_id, deploy_ret_code, deploy_ret_msg = self._hypervisor.deploy(
            ip_address, getpass.getuser(), image_name, nf_instance_name)
        print cont_id, deploy_ret_code, deploy_ret_msg
        if deploy_ret_code == hrc.SUCCESS:
            start_response, start_ret_code, start_ret_msg = self._hypervisor.start(
                ip_address, cont_id)
            return start_ret_code
        else:
            print 'nf deployment failed'
            return deploy_ret_code

    def vnfs_stop_vnf(self, nf_path):
        nf_instance_name, nf_type, ip_address = self.vnfs_get_instance_configuration(
            nf_path)
        print "Stopping " + nf_instance_name
        cont_id, ret_code = self._hypervisor.get_id(
            ip_address, getpass.getuser(), nf_type, nf_instance_name)
        response, ret_code, ret_message = self._hypervisor.stop(
            ip_address, cont_id)
        return response

    def vnfs_get_rx_bytes(self, nf_path):
        nf_instance_name, nf_type, ip_address = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id, ret_code = self._hypervisor.get_id(ip_address,
                                                    getpass.getuser(),
                                                    nf_type, nf_instance_name)
        command = "ifconfig eth0 | grep -Eo 'RX bytes:[0-9]+' | cut -d':' -f 2"
        response = self._hypervisor.execute_in_guest(
            ip_address,
            cont_id,
            command)
        return response

    def vnfs_get_tx_bytes(self, nf_path):
        nf_instance_name, nf_type, ip_address = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id, ret_code = self._hypervisor.get_id(ip_address,
                                                    getpass.getuser(),
                                                    nf_type, nf_instance_name)
        command = "ifconfig eth0 | grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2"
        response = self._hypervisor.execute_in_guest(
            ip_address,
            cont_id,
            command)
        return response

    def vnfs_get_pkt_drops(self, nf_path):
        nf_instance_name, nf_type, ip_address = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id, ret_code = self._hypervisor.get_id(ip_address,
                                                    getpass.getuser(),
                                                    nf_type, nf_instance_name)
        command = "ifconfig eth0 | grep -Eo 'RX .* dropped:[0-9]+' | cut -d':' -f 4"
        response = self._hypervisor.execute_in_guest(
            ip_address,
            cont_id,
            command)
        return response

    def vnfs_get_status(self, nf_path):
        nf_instance_name, nf_type, ip_address = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id, ret_code = self._hypervisor.get_id(ip_address,
                                                    getpass.getuser(),
                                                    nf_type, nf_instance_name)
        response, ret_code, ret_message = self._hypervisor.guest_status(
            ip_address, cont_id)
        return response
