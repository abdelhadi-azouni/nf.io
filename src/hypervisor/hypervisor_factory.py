from docker_driver import Docker
from libvirt_driver import Libvirt


class HypervisorFactory(object):
    __hyp_instance = None
    __hyp_instance_type = None

    def __init__(self, hypervisor_type="Docker"):
        if not HypervisorFactory.__hyp_instance:
            if hypervisor_type == "Docker":
                HypervisorFactory.__hyp_instance_type = hypervisor_type
                HypervisorFactory.__hyp_instance = Docker()
            elif hypervisor_type == "Libvirt":
                HypervisorFactory.__hyp_instance_type = hypervisor_type
                HypervisorFactory.__hyp_instance = Libvirt()
            else:
                raise TypeError(
                    "Invalid hypervisor type. Valid types are: Docker, Libvirt")
        elif HypervisorFactory.__hyp_instance_type != hypervisor_type:
            raise ValueError("An instantiation of Docker type already exists.")

    @staticmethod
    def get_hypervisor_instance():
        if HypervisorFactory.__hyp_instance is not None:
            return HypervisorFactory.__hyp_instance
        else:
            raise RuntimeError("Hypervisor not initialized.")
