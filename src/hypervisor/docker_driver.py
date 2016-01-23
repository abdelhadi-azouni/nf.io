import requests
from contextlib import contextmanager

import docker

from hypervisor_base import HypervisorBase
from hypervisor_return_codes import *


class Docker(HypervisorBase):
    """Hypervisor driver for Docker. This class provides methods for 
        managing docker containers.
    """
      
    def __init__(self):
        """Instantiates a Docker object.
      
        Args:
        None.
          
        Returns:
            None.
            
        Note:
            This method initializes a set of values for configuring 
            Docker remote API client. 
            __port is the port number used for report API invocation.
            __version is the version number for the report API.
            __dns_list is the list of DNS server(s) used by each container.
        """
        self.__port = '4444'
        self.__version = '1.15'
        self.__dns_list = ['8.8.8.8']

    def _get_client(self, host):
        """Returns a Docker client.
        
        Args:
            host: IP address or hostname of the machine where
            docker containers will be deployed
        
        Returns:
            A Docker client object that can be used to communicate with 
            the docker daemon on a machine
        """
        return docker.Client(
            base_url="http://" +
            host +
            ":" +
            self.__port,
            version=self.__version)

    @contextmanager
    def _error_handling(self, return_data):
        """This code block is used to handle exceptions
        
        Args:
            return_data: a dict object used to return the return code
            and messages for a block of code
            
        Returns:
            None.
        """
        try:
            yield
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as ex:
            return_data['code'] = CONNECTION_ERROR
        except docker.errors.APIError as ex:
            return_data['code'] = DOCKER_ERROR
            return_data['message'] = ex.message

    def get_id(self, host, user, vnf_name):
        """Returns a container's ID.
        
        Args:
            host: IP address or hostname of the machine where
            the docker container is deployed
            user: name of the user who owns the VNF
            vnf_type: type of the deployed VNF
            vnf_name: name of the VNF instance whose ID is being queried
          
        Returns:
            Docker container ID.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        dcx = self._get_client(host)
        name = user + "-" + vnf_name
        inspect_data = dcx.inspect_container(container=name)
        return inspect_data['Id'], return_data

    def deploy(self, host, user, image_name, vnf_name):
        """Deploys a docker container.

        Args:
            host: IP address or hostname of the machine where
            the docker container is to be deployed
            user: name of the user who owns the VNF
            image_name: docker image name for the VNF
            vnf_name: name of the VNF instance

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
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            name = user + "-" + vnf_name
            container = dcx.create_container(
                image=image_name,
                hostname=name,
                name=name)
            if container['Warnings']:
                return_data['message'] = " ".join(container['Warnings'])
            return container['Id'], return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def start(self, host, vnf_id):
        """Starts a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.start(
                container=vnf_id,
                dns=self.__dns_list,
                privileged=True)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def restart(self, host, vnf_id):
        """Restarts a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.restart(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def stop(self, host, vnf_id):
        """Stops a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.stop(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def pause(self, host, vnf_id):
        """Pauses a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.pause(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def unpause(self, host, vnf_id):
        """Unpauses a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.unpause(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def destroy(self, host, vnf_id, force=False):
        """Destroys a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.remove_container(container=vnf_id, force=force)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def execute_in_guest(self, host, vnf_id, cmd):
        """Executed commands inside a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.execute(
                vnf_id, [
                    "/bin/bash", "-c", cmd], stdout=True, stderr=False)
            return response

    def guest_status(self, host, vnf_id):
        """Returns the status of a docker container.
        """
        return_data = {'code': SUCCESS, 'message': ""}
        states = {'Running', 'Paused', 'Restarting'}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.inspect_container(vnf_id)
            docker_state = response['State']
            for state in states:
                if docker_state[state]:
                    return state, return_data['code'], return_data['message']
        return 'Undefined', return_data['code'], return_data['message']
