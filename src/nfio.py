#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations
from hyp import hyp_factory
from vnfs_operations import VNFSOperations

import getpass
import re
import importlib
import argparse

class Nfio(Operations):
    def __init__(self, root, mountpoint, hypervisor):
        self.root = root
        self.mountpoint = mountpoint
        self.hypervisor = hypervisor
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
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        return_dictionary = dict()
        if opcode == VNFSOperations.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(path)
            if len(nf_type) > 0:
                mbox_module = importlib.import_module("middleboxes." + nf_type)
                return mbox_module._getattr(self.root, path, fh)
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        file_name = self.vnfs_ops.vnfs_get_file_name(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

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
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        if opcode == VNFSOperations.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(path)
            # Check if this directory is an instance directory or a type
            # directory
            path_tokens = path.split("/")
            if path_tokens.index("nf-types") == len(path_tokens) - 2:
                return os.mkdir(self._full_path(path), mode)
            mbox_module = importlib.import_module("middleboxes." + nf_type)
            result = mbox_module._mkdir(self.root, path, mode)
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
        opcode = self.vnfs_ops.vnfs_get_opcode(full_path)
        file_name = self.vnfs_ops.vnfs_get_file_name(full_path)
        ret_str = ''
        if opcode == self.vnfs_ops.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(path)
            mbox_module = importlib.import_module("middleboxes." + nf_type)
            ret_str = mbox_module._read(self.root, path, length, offset, fh)
        elif opcode == self.vnfs_ops.OP_CHAIN:
            tokens = full_path.encode('ascii').split("/")
            last_index = len(tokens) - 1
            last_index_to_keep = tokens.index('chns') + 4
            nf_path = os.readlink("/".join(tokens[0:last_index_to_keep]))
            f_path = os.path.join(nf_path, "/".join(tokens[last_index_to_keep +
                1:last_index]))
            nf_type = self.vnfs_ops.vnfs_get_nf_type(f_path)
            mbox_module = importlib.import_module("middleboxes." + nf_type)
            ret_str = mbox_module._read(self.root, f_path, length, offset, fh)
        return ret_str

    def write(self, path, buf, offset, fh):
        opcode = self.vnfs_ops.vnfs_get_opcode(path)
        full_path = self._full_path(path)
        file_name = self.vnfs_ops.vnfs_get_file_name(path)
        if opcode == VNFSOperations.OP_NF:
            nf_type = self.vnfs_ops.vnfs_get_nf_type(full_path)
            mbox_module = importlib.import_module("middleboxes." + nf_type)
            return mbox_module._write(self.root, f_path, buf, offset, fh)

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
            description = "nf.io File System for NFV Orchestration",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument(
            '--root',
            help='nf.io root',
            required=True)
    arg_parser.add_argument(
            '--mountpoint',
            help='nf.io mount point',
            required=True)
    arg_parser.add_argument(
            '--hypervisor',
            help='Hypervisor to use for VNF deployment (Docker/Libvirt)',
            default="Docker")
    args = arg_parser.parse_args()
    root = args.root
    mountpoint = args.mountpoint
    hypervisor = args.hypervisor
    hypervisor_factory = hyp_factory.HypervisorFactory(hypervisor)
    FUSE(Nfio(root, mountpoint, hypervisor), mountpoint, foreground=True)

if __name__ == '__main__':
    nfio_main()
