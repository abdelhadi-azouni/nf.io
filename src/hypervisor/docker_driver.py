import requests
from contextlib import contextmanager

import docker

from hypervisor_base import HypervisorBase
from hypervisor_return_codes import *


class Docker(HypervisorBase):

    def __init__(self):
        self.__port = '4444'
        self.__version = '1.15'
        self.__dns_list = ['8.8.8.8']
        self.__image_prefix = 'netfx'

    def _get_client(self, host):
        return docker.Client(
            base_url="http://" +
            host +
            ":" +
            self.__port,
            version=self.__version)

    @contextmanager
    def _error_handling(self, return_data):
        try:
            yield
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as ex:
            return_data['code'] = CONNECTION_ERROR
        except docker.errors.APIError as ex:
            return_data['code'] = DOCKER_ERROR
            return_data['message'] = ex.message

    def get_id(self, host, user, vnf_name):
        return_data = {'code': SUCCESS, 'message': ""}
        dcx = self._get_client(host)
        name = user + "-" + vnf_name
        inspect_data = dcx.inspect_container(container=name)
        return inspect_data['Id'], return_data

    def deploy(self, host, user, image_name, vnf_name):
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
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.restart(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def stop(self, host, vnf_id):
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.stop(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def pause(self, host, vnf_id):
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.pause(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def unpause(self, host, vnf_id):
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.unpause(container=vnf_id)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def destroy(self, host, vnf_id, force=False):
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.remove_container(container=vnf_id, force=force)
            return response, return_data['code'], return_data['message']
        return None, return_data['code'], return_data['message']

    def execute_in_guest(self, host, vnf_id, cmd):
        return_data = {'code': SUCCESS, 'message': ""}
        with self._error_handling(return_data):
            dcx = self._get_client(host)
            response = dcx.execute(
                vnf_id, [
                    "/bin/bash", "-c", cmd], stdout=True, stderr=False)
            return response

    def guest_status(self, host, vnf_id):
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
