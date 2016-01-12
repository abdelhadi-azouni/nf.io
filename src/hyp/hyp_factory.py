from vnfs_docker import Docker
from vnfs_libvirt import Libvirt

class HypervisorFactory(object):
    __hyp_instance = None
    __hyp_instance_type = None
    def __init__(self, hyp_type = "Docker"):
        if not HypervisorFactory.__hyp_instance:
            if hyp_type == "Docker":
                HypervisorFactory.__hyp_instance_type = hyp_type
                HypervisorFactory.__hyp_instance = Docker()
            elif hyp_type == "Libvirt":
                HypervisorFactory.__hyp_instance_type = hyp_type
                HypervisorFactory.__hyp_instance = Libvirt()
            else:
                raise TypeError("Invalid hypervisor type. Valid types are: Docker, Libvirt")
        elif HypervisorFactory.__hyp_instance_type <> hyp_type:
            raise ValueError("An instantiation of Docker type already exists.")
    
    @staticmethod
    def get_hypervisor_instance():
        if HypervisorFactory.__hyp_instance is not None:
            return HypervisorFactory.__hyp_instance
        else:
            raise RuntimeError("Hypervisor not initialized.")

