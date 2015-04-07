from hypbase import HypBase

class Libvirt(HypBase):
  def deploy(self):
    print 'in libvirt.deploy'

  def pause(self):
    print 'in libvirt.pause'

  def destroy(self):
    print 'in libvirt.destroy'
