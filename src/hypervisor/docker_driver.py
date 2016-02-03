import requests

import logging
from contextlib import contextmanager

import docker

from hypervisor_base import HypervisorBase
import errors

logger = logging.getLogger(__name__)

class DockerDriver(HypervisorBase):
    """
    @class DockerDriver
    @brief docker driver for nfio. 

    This class provides methods for managing docker containers.
    """
      
    def __init__(self):
        """
        @brief Instantiates a DockerDriver object.
      
        @note This method initializes a set of values for configuring 
            the docker-py remote API client. 
            __port is the port number used for remote API invocation.
            __version is the version number for the report API.
            __dns_list is the list of DNS server(s) used by each container.
        """
        self.__port = '4444'
        self.__version = '1.15'
        self.__dns_list = ['8.8.8.8']

    @contextmanager
    def _error_handling(self, nfioError):
        """
        @beief convert docker-py exceptions to nfio exceptions
        
        This code block is used to catch docker-py docker-py exceptions 
        (from error.py), log them, and then raise nfio related 
        exceptions. 

        @param nfioError A Exception type from nfio's errors module 
        """
        try:
            yield
        except Exception, ex:
            logger.error(ex.message, exc_info=False)
            raise nfioError

    def _get_client(self, host):
        """Returns a Docker client.
        
        @param host IP address or hostname of the host (physical/virtual) 
            where docker containers will be deployed
        
        @return A docker client object that can be used to communicate 
            with the docker daemon on the host
        """
        with self._error_handling(errors.HypervisorConnectionError):
          return docker.Client(
            base_url="http://" +
            host +
            ":" +
            self.__port,
            version=self.__version)

    def get_id(self, host, user, vnf_name):
        """Returns a container's ID.
        
          @param host IP address or hostname of the machine where
            the docker container is deployed
          @param user name of the user who owns the VNF
          @param vnf_type type of the deployed VNF
          @param vnf_name name of the VNF instance whose ID is being queried
          
          @return docker container ID.
        """
        dcx = self._get_client(host)
        vnf_fullname = user + "-" + vnf_name
        with self._error_handling(errors.VNFNotFoundError):
            inspect_data = dcx.inspect_container(container=vnf_fullname)
            return inspect_data['Id']

    def get_ip(self, host, vnf_id):
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFNotFoundError):
            inspect_data = dcx.inspect_container(vnf_id)
            logger.debug('ip address read from container ' + 
                   inspect_data['NetworkSettings']['IPAddress'])
            return inspect_data['NetworkSettings']['IPAddress'].encode('ascii')

    def deploy(self, host, user, image_name, vnf_name, is_privileged=True):
        """Deploys a docker container.

        Args:
            host: IP address or hostname of the machine where
                the docker container is to be deployed
            user: name of the user who owns the VNF
            image_name: docker image name for the VNF
            vnf_name: name of the VNF instance
            is_privileged: if True then the container is deployed in 
                privileged mode

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                container_id: docker container id
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                None as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        dcx = self._get_client(host)
        vnf_fullname = user + "-" + vnf_name
        host_config = dict()
        if is_privileged:
            host_config['Privileged'] = True
        with self._error_handling(errors.VNFDeployError):
            container = dcx.create_container(
                image=image_name,
                hostname=host,
                name=vnf_fullname,
                host_config=host_config)
            return container['Id']

    def start(self, host, vnf_id, is_privileged=True):
        """Starts a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF
          is_privileged: if True then the container is started in 
            privileged mode

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                response: response from the docker-py client
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                None as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFStartError):
            dcx.start(container=vnf_id,
                dns=self.__dns_list,
                privileged=is_privileged)

    def restart(self, host, vnf_id):
        """Restarts a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                response: response from the docker-py client
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                None as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFRestartError):
            dcx.restart(container=vnf_id)

    def stop(self, host, vnf_id):
        """Stops a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                response: response from the docker-py client
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                None as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFStopError):
            dcx.stop(container=vnf_id)

    def pause(self, host, vnf_id):
        """Pauses a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                response: response from the docker-py client
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                None as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFPauseError):
            dcx.pause(container=vnf_id)

    def unpause(self, host, vnf_id):
        """Unpauses a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                response: response from the docker-py client
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                None as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFUnpauseError):
            dcx.unpause(container=vnf_id)

    def destroy(self, host, vnf_id, force=True):
        """Destroys a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                response: response from the docker-py client
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                None as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFDestroyError):
            dcx.remove_container(container=vnf_id, force=force)

    def execute_in_guest(self, host, vnf_id, cmd):
        """Executed commands inside a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF
          cmd: the command to execute inside the container

        Returns:
          The output of the command passes as cmd
        """
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFCommandExecutionError):
            response = dcx.execute(vnf_id, 
                ["/bin/bash", "-c", cmd], 
                stdout=True, stderr=False)
            return response

    def guest_status(self, host, vnf_id):
        """Returns the status of a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF

        Returns:
            If the operation is successful then returns a tuple 
            consisting of the following values:
                state: current state of the docker container
                return_code: SUCCESS
                return_message: EMPTY in this case
            otherwise returns the error as the following tuple:
                Undefined as the first value
                return_code: one of the error codes defined in hypervisor_return_codes
                return_message: detailed message for the return code
        """
        states = {'Running', 'Paused', 'exited', 'Restarting'}
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFNotFoundError):
            response = dcx.inspect_container(vnf_id)
            return response['State']['Status'].encode('ascii')
