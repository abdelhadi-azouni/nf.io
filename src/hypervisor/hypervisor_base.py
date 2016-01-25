from abc import ABCMeta, abstractmethod


class HypervisorBase(object):
    """Base class for hypervisors. This class must be extended by
      a hypervisor driver.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_id(self):
      """Returns the hypervisor specific ID of the VM or container.
      
      Args:
        Defined in derived class.
        
      Returns:
        Hypervisor specific ID for a VM or container.
      """
        pass

    @abstractmethod
    def deploy(self):
      """Deploys a VM or continer.
      
      Args:
        Defined in derived class.
        
      Returns:
        Hypervisor specific return code.
      """ 
        pass

    @abstractmethod
    def pause(self):
      """Pauses a VM or continer.
      
      Args:
        Defined in derived class.
        
      Returns:
        Hypervisor specific return code.
      """ 
        pass

    @abstractmethod
    def destroy(self):
      """Destroys a VM or continer.
      
      Args:
        Defined in derived class.
        
      Returns:
        Hypervisor specific return code.
      """ 
        pass

    @abstractmethod
    def execute_in_guest(self):
      """Executes a command in the VM or continer.
      
      Args:
        Defined in derived class.
        
      Returns:
        Hypervisor specific return code.
      """ 
        pass

    @abstractmethod
    def guest_status(self):
      """Returns the current status of a VM or continer.
      
      Args:
        Defined in derived class.
        
      Returns:
        Current status of a VM or container.
      """ 
        pass
