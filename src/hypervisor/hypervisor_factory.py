from docker_driver import Docker
from libvirt_driver import Libvirt


class HypervisorFactory(object):

    """
    A singletone class for creating hypervisor driver objects. For an
    instantiation of nf.io there can be exactly one object of only one type of
    hyperviosr. HyervisorFactory takes care of the creation logic.
    """
    __hyp_instance = None
    __hyp_instance_type = None

    def __init__(self, hypervisor_type="Docker"):
        """
        Instantiates a HypervisorFactory object.

        Args:
            hypervisor_type: The type of hypervisor object to instantiate. Valid
                hypervisor types are 'Docker' and 'Libvirt' for the time being.

        Returns:
            Nothing. Initializaes the factory object.

        Note:
            If this factory class is instantiated multiple times with different
            types of hypervisor_type argument then it raises a ValueError.

            If this factory class is instantiated with a hypervisor type other
            than Docker or Libvirt it raises a TypeError.
        """
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
            raise ValueError(
                "An instantiation of type " +
                HypervisorFactory.__hyp_instance_type +
                " already exists.")

    @staticmethod
    def get_hypervisor_instance():
        """
        Returns the hypervisor driver nstance. If the instance is not initialized then
        a RuntimeError is raised.
        """
        if HypervisorFactory.__hyp_instance is not None:
            return HypervisorFactory.__hyp_instance
        else:
            raise RuntimeError("Hypervisor not initialized.")
