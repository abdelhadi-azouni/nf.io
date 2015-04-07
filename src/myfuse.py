#!/usr/bin/env python

from __future__ import with_statement

# myfuse imports
import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations
from vnfs_operations import VNFSOperations

# OpenNfo imports
import getpass
import re

class Passthrough(Operations):
    def __init__(self, root, mountpoint):
        self.root = root
        self.mountpoint = mountpoint
        self.vnfs_ops = VNFSOperations(root)

    # Helpers
    # =======

    def _full_path(self, partial):
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
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        special_files = ['rx_bytes', 'tx_bytes', 'pkt_drops', 'status']
        file_name = self.vnfs_ops.vnfs_get_file_name(full_path)
        return_dictionary = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        if file_name in special_files:
            return_dictionary['st_size'] = 1000
        return return_dictionary

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith(self.root):
            pathname = self.mountpoint + pathname[len(self.root):]
        print pathname
        return pathname
#        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
#            return os.path.relpath(pathname, self.root)
#        else:
#            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        if opcode == VNFSOperations.OP_NF:
            result = self.vnfs_ops.vnfs_create_vnf_instance(path, mode)
        elif opcode == VNFSOperations.OP_CHAIN:
            result = self.vnfs_ops.vnfs_create_chain(path, mode)
        elif opcode == VNFSOperations.OP_UNDEFINED:
            result = errno.EPERM
        return result


    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        opcode = self.vnfs_ops.vnfs_get_opcode(name)
        result = 0
        if opcode != VNFSOperations.OP_CHAIN:
            return -1
        if not self.vnfs_ops.vnfs_is_nf_instance(target):
            return -1
        target = self._full_path(target)
        name = self._full_path(name)
        nf_instance_name = self.vnfs_ops.vnfs_get_file_name(target)
        chns_file_name = self.vnfs_ops.vnfs_get_file_name(name)
        if chns_file_name == 'start' or chns_file_name == 'next':
            return os.symlink(target, name)
        else:
            result = os.mkdir(name, 0755)
            result = os.symlink(target, name + '/' +
                                nf_instance_name)
        return result

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
        full_path = self._full_path(path)
        print full_path
        opcode = self.vnfs_ops.vnfs_get_opcode(full_path)
        file_name = self.vnfs_ops.vnfs_get_file_name(full_path)
        special_files = ['rx_bytes', 'tx_bytes', 'pkt_drops', 'status']
        nf_path = ''
        if file_name in special_files:
            tokens = full_path.encode('ascii').split("/")
            if opcode == VNFSOperations.OP_CHAIN:
                last_index_to_keep = tokens.index('chns') + 4
                nf_path = "/".join(tokens[0:last_index_to_keep])
                nf_path = os.readlink(nf_path)
            elif opcode == VNFSOperations.OP_NF:
                last_index_to_keep = tokens.index('nf-types') + 3
                nf_path = "/".join(tokens[0:last_index_to_keep])
        print nf_path

        if file_name == "rx_bytes":
            ret_str = self.vnfs_ops.vnfs_get_rx_bytes(nf_path)
            if offset >= len(ret_str):
              ret_str = ''
        elif file_name == "tx_bytes":
            ret_str = self.vnfs_ops.vnfs_get_tx_bytes(nf_path)
            if offset >= len(ret_str):
              ret_str = ''
        elif file_name == 'pkt_drops':
            ret_str = self.vnfs_ops.vnfs_get_pkt_drops(nf_path)
            if offset >= len(ret_str):
              ret_str = ''
        elif file_name == 'status':
            ret_str = self.vnfs_ops.vnfs_get_status(nf_path)
            if offset >= len(ret_str):
                ret_str = ''
        else:
            os.lseek(fh, offset, os.SEEK_SET)
            ret_str = os.read(fh, length)
        return ret_str

    def write(self, path, buf, offset, fh):
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        full_path = self._full_path(path)
        file_name = self.vnfs_ops.vnfs_get_file_name(path)
        if opcode == VNFSOperations.OP_CHAIN:
            if file_name == "action" and buf == "activate":
                # activate a chain of vnfs.
                chain_directory = "/".join(full_path.split("/")[:-1])
                print chain_directory
                self.vnfs_ops.vnfs_deploy_nf_chain(chain_directory)
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

def main(mountpoint, root):
    FUSE(Passthrough(root, mountpoint), mountpoint, foreground=True)

# argv[2] = root
# argv[1] = mountpoint
if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
