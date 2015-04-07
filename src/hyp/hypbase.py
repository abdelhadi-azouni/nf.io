from abc import ABCMeta, abstractmethod

class HypBase(object):
  __metaclass__=ABCMeta

  @abstractmethod
  def get_id(self):
    pass
  @abstractmethod
  def deploy(self):
    pass

  @abstractmethod
  def pause(self):
    pass

  @abstractmethod
  def destroy(self):
    pass

  @abstractmethod
  def execute_in_guest(self):
    pass

  @abstractmethod
  def guest_status(self):
      pass
