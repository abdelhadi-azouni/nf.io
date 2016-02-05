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

    def isEmpty(self, string):
        return string is None or string.strip() == ""

    def validate_host(self, host):
        if self.isEmpty(host):
            raise errors.VNFHostNameIsEmptyError

    def validate_image_name(self, image_name):
        if self.isEmpty(image_name):
            raise errors.VNFImageNameIsEmptyError

    def validate_cont_name(self, cont_name):
        if self.isEmpty(cont_name):
            raise errors.VNFNameIsEmptyError
        ## check to see if there is any container with name cont_name
        #nameExists = False
        #dcx = self._get_client(host)
        #containers = dcx.containers()
        #for container in containers:
        #    for cont_name in container['Names']:
        #        # docker container names includes a leading '/'!
        #        if vnf_fullname == cont_name[1:].encode('ascii'):
        #            nameExists = True
        #if not nameExist:
        #    raise errors.VNFNotFoundError

    def _get_client(self, host):
        """Returns a Docker client.
        
        @param host IP address or hostname of the host (physical/virtual) 
            where docker containers will be deployed
        
        @return A docker client object that can be used to communicate 
            with the docker daemon on the host
        """
        self.validate_host(host)
        with self._error_handling(errors.HypervisorConnectionError):
          return docker.Client(
            base_url="http://" +
            host +
            ":" +
            self.__port,
            version=self.__version)

    def lookupVNF(self, host, user, vnf_name):
        self.validate_host(host)
        vnf_fullname = user + '-' + vnf_name
        self.validate_cont_name(vnf_fullname)
        dcx = self._get_client(host)
        with self._error_handling(errors.VNFNotFoundError):
            inspect_data = dcx.inspect_container(container=vnf_fullname)
            return dcx, vnf_fullname, inspect_data

    def get_id(self, host, user, vnf_name):
        """Returns a container's ID.
        
          @param host IP address or hostname of the machine where
            the docker container is deployed
          @param user name of the user who owns the VNF
          @param vnf_type type of the deployed VNF
          @param vnf_name name of the VNF instance whose ID is being queried
          
          @return docker container ID.
        """
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        return inspect_data['Id'].encode('ascii')

    def get_ip(self, host, user, vnf_name):
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
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
        self.validate_host(host)
        self.validate_image_name(image_name)
        vnf_fullname = user + '-' + vnf_name
        self.validate_cont_name(vnf_fullname)
        dcx = self._get_client(host)
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

    def start(self, host, user, vnf_name, is_privileged=True):
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
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        with self._error_handling(errors.VNFStartError):
            dcx.start(container=vnf_fullname,
                dns=self.__dns_list,
                privileged=is_privileged)

    def restart(self, host, user, vnf_name):
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
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        with self._error_handling(errors.VNFRestartError):
            dcx.restart(container=vnf_fullname)

    def stop(self, host, user, vnf_name):
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
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        with self._error_handling(errors.VNFStopError):
            dcx.stop(container=vnf_fullname)

    def pause(self, host, user, vnf_name):
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
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        with self._error_handling(errors.VNFPauseError):
            dcx.pause(container=vnf_fullname)

    def unpause(self, host, user, vnf_name):
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
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        with self._error_handling(errors.VNFUnpauseError):
            dcx.unpause(container=vnf_fullname)

    def destroy(self, host, user, vnf_name, force=True):
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
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        with self._error_handling(errors.VNFDestroyError):
            dcx.remove_container(container=vnf_fullname, force=force)

    def execute_in_guest(self, host, user, vnf_name, cmd):
        """Executed commands inside a docker container.

        Args:
          host: IP address or hostname of the machine where 
              the docker container is deployed
          vnf_id: Docker container ID for the VNF
          cmd: the command to execute inside the container

        Returns:
          The output of the command passes as cmd
        """
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        if self.guest_status(host, user, vnf_name) != 'running':
            raise errors.VNFNotRunningError
        with self._error_handling(errors.VNFCommandExecutionError):
            response = dcx.execute(vnf_fullname, 
                ["/bin/bash", "-c", cmd], stdout=True, stderr=False)
            return response

    def guest_status(self, host, user, vnf_name):
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
        dcx, vnf_fullname, inspect_data = self.lookupVNF(host, user, vnf_name)
        return inspect_data['State']['Status'].encode('ascii')
