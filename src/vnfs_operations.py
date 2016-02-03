#!/usr/bin/env python
from __future__ import with_statement

import os
from subprocess import Popen, PIPE
import sys
import errno
import time

import logging

import getpass
import re

import errors
from hypervisor import hypervisor_factory

logger = logging.getLogger(__name__)

class VNFSOperations:

    """
    Provides a common set of operations for nfio. These operations act as a
    helper.
    """

    OP_UNDEFINED = 0xFF
    OP_NF = 0x01

    def __init__(self, vnfs_root):
        self.vnfs_root = vnfs_root
        self._hypervisor = hypervisor_factory.HypervisorFactory.get_hypervisor_instance()

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.vnfs_root, partial)
        return path

    def vnfs_create_vnf_instance(self, path, mode):
        """
        Create the file system structure for a VNF.

        Args:
            path: path of the new VNF instance.
            mode: file creation mode for the new VNF instance directory.

        Returns:
            returns the return code of os.mkdir
        """
        logger.info('Creating file/directory structure in ' + path)
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
        os.open(full_path + "/machine/vm.ip", os.O_WRONLY | os.O_CREAT,
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
        logger.info('Finished creating file/directory structure in ' + path)
        return result

    def vnfs_get_opcode(self, path):
        """
        Determinse the type of operation based on the path.

        Args:
            path: path to the file/directory on which the operation is being
            performed

        Returns:
            If the file is under nf-types subdirectory in the nfio mount, then
            returns OP_NF. Otherwise, returns OP_UNDEFINED.
        """
        tokens = self._full_path(path).encode('ascii').split('/')
        if "nf-types" in tokens:
            return VNFSOperations.OP_NF
        return VNFSOperations.OP_UNDEFINED

    def vnfs_get_nf_type(self, path):
        """
        Parse the type of VNF from path

        Args:
            path: the path of the file/directory on which some operation is
            being performed.

        Returns:
            Returns the type of VNF parsed from the path, e.g., if the path is
            /mnt/vnfsroot/nf-types/firewall/fw-alpha/action then returns
            firewall.
        """
        tokens = self._full_path(path).encode('ascii').split('/')
        try:
            return tokens[tokens.index("nf-types") + 1]
        except ValueError:
            return ""
        except IndexError:
            return ""

    def vnfs_get_file_name(self, path):
        """
        Return the name of the file represented by a path.

        Args:
            path: the path of the file in concern

        Returns:
            returns the name of the file, i.e., last token after / in the path.
        """

        return path.split('/')[-1]

    def vnfs_is_nf_instance(self, path):
        """
        Determines if a path represents an nf instance directory.

        Args:
            path: path of the file/directory in concern.

        Returns:
            True: if path represents an nf instance directory. For example, if
            path is /mnt/vnfsmnt/nf-types/firewall/fw-alpha then returns True.

            False: if the path does not represent an nf instance directory. For
            example, if path is /mnt/vnfsmnt/nf-types/firewall/fw-alpha/action
            then returns False.
        """
        tokens = self._full_path(path).encode('ascii').split('/')
        if ('nf-types' in tokens) and len(tokens) > tokens.index('nf-types') + \
                1:
            return True
        return False

    def vnfs_get_instance_configuration(self, nf_path):
        """
        Return the configuration parameters related to a VNF instance.

        Args:
            nf_path: path of the VNF instance. e.g.,
            /mnt/vnfsmnt/firewall/fw-alpha

        Returns:
            A tuple representing the configuration of the VNF instance. The
            tuple is organized in the following order:
                nf_instance_name: name of the VNF instance.
                nf_type: type of the VNF.
                ip_address: IP address of the machine where this VNF will be
                    deployed.
                image_name: name of the VM/container image for that VNF.
        """
        nf_instance_name = self.vnfs_get_file_name(nf_path)
        nf_type = self.vnfs_get_nf_type(nf_path)
        ip_address = ''
        logger.debug(nf_path + '/machine/ip')
        with open(nf_path + '/machine/ip') as ip_fd:
            ip_address = ip_fd.readline().rstrip('\n')
        image_name = ''
        with open(nf_path + '/machine/vm.image') as img_fd:
            image_name = img_fd.readline().rstrip('\n')
        logger.info("Instance name: " + nf_instance_name + ", type: " 
            + nf_type + ", host-ip: " + ip_address + " VNF image: " + image_name)
        return nf_instance_name, nf_type, ip_address, image_name

    def vnfs_deploy_nf(self, nf_path):
        """
        Deploys and STARTS a VNF instance.

        Args:
            nf_path: path of the VNF instance.

        @return void
        """
        logger.info('Deploying new VNF at ' + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(nf_path)
        try:
            cont_id  = self._hypervisor.deploy(
                ip_address, getpass.getuser(), image_name, nf_instance_name)
            logger.debug(cont_id)
        except errors.VNFDeployError:
            logger.info('Instance: ' + nf_instance_name  + ' deployment failed')
        else:
            logger.info('Instance: ' + nf_instance_name  
                    + ' successfully deployed')
            try:
                logger.info('Starting the deployed VNF instance: ' 
                    + nf_instance_name)
                self._hypervisor.start(ip_address, cont_id)
            except errors.VNFStartError:
                logger.info('Instance: ' + nf_instance_name  + ' start failed')
                # destroy the deployed VNF
                self._hypervisor.destroy(ip_address, cont_id)
                logger.info('Instance: ' + nf_instance_name  
                    + ' destroyed')
            else:
                logger.info('Instance: ' + nf_instance_name  
                    + ' successfully deployed and started')

    def vnfs_stop_vnf(self, nf_path):
        """
        Stops a VNF instance.

        Args:
            nf_path: path of the VNF instance.

        @return void
        """
        logger.info("Stopping VNF at " + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id = self._hypervisor.get_id(
            ip_address, getpass.getuser(), nf_instance_name)
        self._hypervisor.stop(ip_address, cont_id)
        logger.info('Instance: ' + nf_instance_name + ' successfully stopped')

    def vnfs_start_vnf(self, nf_path):
        """
        Starts a deployed VNF instance.

        Args:
            nf_path: path of the VNF instance.

        Returns:
            return codes are described in hypervisor.hypervisor_return_codes
            module.
        """
        logger.info("Starting VNF at " + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id = self._hypervisor.get_id(
            ip_address, getpass.getuser(), nf_instance_name)
        self._hypervisor.start(ip_address, cont_id)
        logger.info('Instance: ' + nf_instance_name + ' successfully started')

    def vnfs_destroy_vnf(self, nf_path):
        """
        Destroys a deployed VNF instance.

        Args:
            nf_path: path of the VNF instance.

        Returns:
            return codes are described in hypervisor.hypervisor_return_codes
            module.
        """
        logger.info("Destroying VNF at " + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id = self._hypervisor.get_id(
            ip_address, getpass.getuser(), nf_instance_name)
        self._hypervisor.destroy(ip_address, cont_id)
        logger.info('Instance: ' + nf_instance_name + ' successfully destroyed')

    def vnfs_get_rx_bytes(self, nf_path):
        """
        Reads the number of bytes received by a VNF instance.

        Args:
            nf_path: path of the VNF instance.

        Returns:
            returns the number of bytes received by a VNF instance.
        """
        logger.info('Reading rx_bytes at ' + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id = self._hypervisor.get_id(ip_address,
                                                    getpass.getuser(),
                                                    nf_instance_name)
        command = "ifconfig eth0 | grep -Eo 'RX bytes:[0-9]+' | cut -d':' -f 2"
        response = self._hypervisor.execute_in_guest(
            ip_address,
            cont_id,
            command)
        logger.info('Successfully read rx_bytes')
        return response

    def vnfs_get_tx_bytes(self, nf_path):
        """
        Reads the number of bytes sent by a VNF instance.

        Args:
            nf_path: path of the VNF instance.

        Returns:
            returns the number of bytes sent by a VNF instance.
        """
        logger.info('Reading tx_bytes at ' + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id = self._hypervisor.get_id(ip_address,
                                                    getpass.getuser(),
                                                    nf_instance_name)
        command = "ifconfig eth0 | grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2"
        response = self._hypervisor.execute_in_guest(
            ip_address,
            cont_id,
            command)
        logger.info('Successfully read tx_bytes')
        return response

    def vnfs_get_pkt_drops(self, nf_path):
        """
        Reads the number of packets dropped by a VNF instance.

        Args:
            nf_path: path of the VNF instance.

        Returns:
            returns the number of packets dropped by a VNF instance.
        """
        logger.info('Reading pkt_drops at ' + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        cont_id = self._hypervisor.get_id(ip_address,
                                                    getpass.getuser(),
                                                    nf_instance_name)
        command = "ifconfig eth0 | grep -Eo 'RX .* dropped:[0-9]+' | cut -d':' -f 4"
        response = self._hypervisor.execute_in_guest(
            ip_address,
            cont_id,
            command)
        logger.info('Successfully read pkt_drops')
        return response

    def vnfs_get_status(self, nf_path):
        """
        Get the status of a VNF instance, e.g., the VNF is
        running/suspended/stopped etc.

        Args:
            nf_path: path of the VNF instance.

        Returns:
            Hypervisor specific status of the VNF. For example, if Docker is
            being used for VNF deployment then Docker specific container status
            message is returned.
        """
        logger.info('Reading status at ' + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        response = ''
        try:
            nf_id = self._hypervisor.get_id(ip_address,
                getpass.getuser(),
                nf_instance_name)
            response = self._hypervisor.guest_status(ip_address, nf_id)
        except errors.VNFNotFoundError:
            logger.info('Instance: ' + nf_instance_name + ' does not exist')
        logger.info('Successfully read status')
        return response

    def vnfs_get_ip(self, nf_path):
        """
        Get the status of a VNF instance, e.g., the VNF is
        running/suspended/stopped etc.

        Args:
            nf_path: path of the VNF instance.

        Returns:
            Hypervisor specific status of the VNF. For example, if Docker is
            being used for VNF deployment then Docker specific container status
            message is returned.
        """
        logger.info('Reading ip at ' + nf_path)
        nf_instance_name, nf_type, ip_address, image_name = self.vnfs_get_instance_configuration(
            nf_path)
        cont_ip = self._hypervisor.get_ip(ip_address,
                                                    getpass.getuser(),
                                                    nf_instance_name)
        logger.debug('cont_ip ' + cont_ip)
        logger.info('Successfully read ip')
        return cont_ip

