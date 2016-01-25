"""
Each module provides VNF specific implementations for select system calls. Each
module should provide implementation for the following methods:
    _mkdir(root, path, mode): Provides implementation of mkdir system call. We
        redefined mkdir's semantics to create the file/directory structure of a
        new VNF. A VNF specific implementaion of _mkdir will create that VNF
        specific file/directory structure.
    _getattr(root, path, fh): Provides implementation of getattr system call. If
        there are any VNF specific special cases for setting attribute of
        certain files that should be handled here.
    _read(root, path, length, offset, fh): Provides implementation of read
        system call. It implements read operation for VNF specific special
        files, e.g., rx_bytes, tx_bytes etc.
    _write(root, path, buf, offset, fh): Provides implementation of write system
        call. It implements write operation for VNF specific special files and
        special commands. e.g., writing 'stop' to 'action' file of a VNF stops
        the VNF instance.
"""
