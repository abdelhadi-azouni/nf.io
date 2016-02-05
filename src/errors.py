"""
@brief This module contains all the custom exceptions defined for nf.io
"""

class nfioError(Exception):
    pass

class HypervisorError(nfioError):
    pass

class VNFConfigurationError(nfioError):
    pass

class HypervisorConnectionError(HypervisorError):
    def __init__(self):
        self.errno = 701

class VNFNotFoundError(HypervisorError):
    def __init__(self):
        self.errno = 702

class VNFCommandExecutionError(HypervisorError):
    def __init__(self):
        self.errno = 703

class VNFCreateError(HypervisorError):
    def __init__(self):
        self.errno = 704

class VNFDeployError(HypervisorError):
    def __init__(self):
        self.errno = 705

class VNFDestroyError(HypervisorError):
    def __init__(self):
        self.errno = 706

class VNFStartError(HypervisorError):
    def __init__(self):
        self.errno = 707

class VNFRestartError(HypervisorError):
    def __init__(self):
        self.errno = 708

class VNFStopError(HypervisorError):
    def __init__(self):
        self.errno = 709

class VNFPauseError(HypervisorError):
    def __init__(self):
        self.errno = 710

class VNFUnpauseError(HypervisorError):
    def __init__(self):
        self.errno = 711

class VNFDeployErrorWithInconsistentState(HypervisorError):
    def __init__(self):
        self.errno = 712

class VNFImageNameIsEmptyError(VNFConfigurationError):
    def __init__(self):
        self.errno = 713

class VNFHostNameIsEmptyError(VNFConfigurationError):
    def __init__(self):
        self.errno = 714

class VNFNameIsEmptyError(VNFConfigurationError):
    def __init__(self):
        self.errno = 715

class VNFNotRunningError(HypervisorError):
    def __init__(self):
        self.errno = 716

