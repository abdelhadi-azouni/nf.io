#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno

import logging

from fuse import FUSE, FuseOSError, Operations
from hypervisor import hypervisor_factory as hyp_factory
from vnfs_operations import VNFSOperations

import getpass
import re
import importlib
import argparse

logger = logging.getLogger(__name__)

class Nfio(Operations):

    def __init__(
            self,
            root,
            mountpoint,
            hypervisor='Docker',
            module_root='middleboxes'):
        """Instantiates a Nfio object.

        Args:
            root: The root directory of nfio file system. The root directory
                stores persistent state about the system.
            mountpoint: The mountpoint of nfio file system. The mountpoint is
                required to intercept the file system calls via fuse. All the
                file system calls for fuse mounted files/directories are
                intercepted by libfuse and our provided implementation is
                executed.
            hypervisor: The type of hypervisor to use for deploying VNFs. The
                default is to use Docker containers. However, we also plan to
                add support for Libvirt.
            module_root: Root directory of the middlebox modules. Each middlebox
                provides it's own implementation of certain system calls in a
                separate module. module_root points to the root of that module.
                If nothing is provided a default of 'middleboxes' will be
                assumed.
        Returns:
            Nothing. Mounts nf.io file system at the specified mountpoint and
            creates a loop to act upon different file system calls.
        """
        self.root = root
        self.mountpoint = mountpoint
        self.hypervisor = hypervisor
        self.vnfs_ops = VNFSOperations(root)
        self.module_root = module_root

    # Helpers
    # =======

    def _full_path(self, partial):
        """Returns the absolute path of a partially specified path.

        Args:
            partial: The partially specified path. e.g., nf-types/firewall
                This partially specified path should be a relative path under
                the mounted directory of nfio"
        Returns:
            The absolute path for the partially specified path. The absolute
            path is in respect to nfio root directory. e.g., if partial is
            nf-types/firewall and nfio root is /vnfsroot, then the return value
            will be /vnfsroot/nf-types/firewall
        """
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        """
        Returns the file attributes of the file specified by path
        Args:
            path: Path of the file
            fh: Open file handle to the file
        Returns:
            A dictionary containing file attributes. The dictionary contains the
            following keys:
                st_atime:   Last access time
                st_ctime:   File creation time
                st_gid:     Group id of the owner group
                st_mode:    File access mode
                st_mtime:   Last modification time
                st_nlink:   Number of symbolic links to the file
                st_size:    Size of the file in bytes
                st_uid:     User id of the file owner
        Note:
            For special placeholder files for VNFs, st_size is set to a
            constant 1000. This is to make sure read utilities such as cat work
            for these special placeholder files.
        """
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        if opcode == VNFSOperations.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(path)
            if len(nf_type) > 0:
                try:
                    mbox_module = importlib.import_module(
                        self.module_root +
                        "." +
                        nf_type)
                except ImportError:
                    logger.error('VNF module file missing. Add "' + nf_type 
                        + '.py" under the directory ' + self.module_root)
                    ## TODO: raise an custom exception and handle it in a OS 
                    ## specific way
                    raise OSError(errno.ENOSYS)
                return mbox_module._getattr(self.root, path, fh)
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        file_name = self.vnfs_ops.vnfs_get_file_name(full_path)
        return dict(
            (key,
             getattr(
                 st,
                 key)) for key in (
                'st_atime',
                'st_ctime',
                'st_gid',
                'st_mode',
                'st_mtime',
                'st_nlink',
                'st_size',
                'st_uid'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for entry in dirents:
            yield entry

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith(self.root):
            pathname = self.mountpoint + pathname[len(self.root):]
        return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        """
        The semantics have been redefined to create a new VNF instance when a
        directory is created under a specific type of VNF directory.

        Args:
            path: path of the directory to create. The path also represents the
                name of the new VNF instance to be created.
            mode: File access mode for the new directory.
        Returns:
            If path does not correspond to a directory under a specific VNF type
            directory then errno.EPERM is returned. Otherwise the return code is
            same as os.mkdir()'s return code.
        """
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        if opcode == VNFSOperations.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(path)
            # Check if this directory is an instance directory or a type
            # directory
            path_tokens = path.split("/")
            if path_tokens.index("nf-types") == len(path_tokens) - 2:
                return os.mkdir(self._full_path(path), mode)
            mbox_module = importlib.import_module(
                self.module_root +
                "." +
                nf_type)
            result = mbox_module._mkdir(self.root, path, mode)
        elif opcode == VNFSOperations.OP_UNDEFINED:
            result = errno.EPERM
        return result

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict(
            (key,
             getattr(
                 stv,
                 key)) for key in (
                'f_bavail',
                'f_bfree',
                'f_blocks',
                'f_bsize',
                'f_favail',
                'f_ffree',
                'f_files',
                'f_flag',
                'f_frsize',
                'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(self._full_path(target), name)

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        """
        Reads an open file. This nfio specific implementation parses path to see
        if the read is from any VNF or not. In case the read is from a VNF, the
        corresponding VNF module is loaded and the module's _read function is
        invoked to complete the read system call.

        Args:
            path: path represents the path of the file to read from
            length: number of bytes to read from the file
            offset: byte offset indicating the starting byte to read from
            fh: file descriptor of the open file represented by path

        Returns:
            length bytes from offset byte of the file represented by fh and path

        Notes:
            VNFs can have special files which are placeholders for statistics
            such as number of received/sent bytes etc. VNFs provide their own
            implementation of read and handle reading of these special
            placeholder files.
        """
        full_path = self._full_path(path)
        opcode = self.vnfs_ops.vnfs_get_opcode(full_path)
        file_name = self.vnfs_ops.vnfs_get_file_name(full_path)
        if opcode == self.vnfs_ops.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(path)
            mbox_module = importlib.import_module(
                self.module_root +
                "." +
                nf_type)
            return mbox_module._read(self.root, path, length, offset, fh)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        """
        Write to an open file. In this nfio specific implementation the path is
        parsed to see if the write is for any specific VNF or not. If the write
        is for any file under a VNF directory then the corresponding VNF module
        is loaded and the module's _write function is invoked.

        Args:
            path: path to the file to write
            buf: the data to write
            offset: the byte offset at which the write should begin
            fh: file descriptor of the open file represented by path

        Returns:
            Returns the number of bytes written to the file starting at offset

        Note:
            VNFs can have special files where writing specific strings trigger
            a specific function. For example, writing 'activate' to the 'action'
            file of a VNF will start the VNF. VNF specific modules handle such
            special cases of writing.
        """
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        full_path = self._full_path(path)
        file_name = self.vnfs_ops.vnfs_get_file_name(path)
        if opcode == VNFSOperations.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(full_path)
            mbox_module = importlib.import_module(
                self.module_root +
                "." +
                nf_type)
            return mbox_module._write(self.root, path, buf, offset, fh)

        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def nfio_main():
    arg_parser = argparse.ArgumentParser(
        description="nf.io File System for NFV Orchestration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument(
        '--nfio_root',
        help='Absolute path of nf.io root',
        required=True)
    arg_parser.add_argument(
        '--nfio_mount',
        help='Absolute path of nf.io mount point',
        required=True)
    arg_parser.add_argument(
        '--hypervisor',
        help='Hypervisor to use for VNF deployment (Docker/Libvirt)',
        default="Docker")
    arg_parser.add_argument(
        '--middlebox_module_root',
        help='Module directory inside the source tree containing middlebox specific implementation of system calls',
        default='middleboxes')
    arg_parser.add_argument(
        '--log_level',
        help='[debug|info|warning|error]',
        default='info')

    args = arg_parser.parse_args()
    root = args.nfio_root
    mountpoint = args.nfio_mount
    hypervisor = args.hypervisor
    hypervisor_factory = hyp_factory.HypervisorFactory(hypervisor)
    module_root = args.middlebox_module_root

    # set the logging level
    LOG_LEVELS = {'debug':logging.DEBUG,
                  'info':logging.INFO,
                  'warning':logging.WARNING,
                  'error':logging.ERROR,
                  'critical':logging.CRITICAL,
                 }
    log_level = LOG_LEVELS.get(args.log_level, logging.INFO)
    logging.basicConfig(level=log_level)
    # suppress INFO log messages from the requests module
    logging.getLogger("requests").setLevel(logging.WARNING)

    FUSE(
        Nfio(
            root,
            mountpoint,
            hypervisor,
            module_root),
        mountpoint,
        foreground=True)

if __name__ == '__main__':
    nfio_main()
