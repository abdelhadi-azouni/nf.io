from hypervisor_base import HypervisorBase

class Libvirt(HypervisorBase):
  def deploy(self):
    print 'in libvirt.deploy'

  def pause(self):
    print 'in libvirt.pause'

  def destroy(self):
    print 'in libvirt.destroy'
