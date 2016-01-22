import os
import random


def full_path(root, partial):
    if partial.startswith("/"):
        partial = partial[1:]
    return os.path.join(root, partial)


def _mkdir(root, path, mode):
    f_path = full_path(root, path)
    result = os.mkdir(f_path)
    file_names = ['alpha', 'beta', 'gamma', 'kappa', 'omega', 'theta']
    [os.open(f_path + "/" + file_name, os.O_WRONLY | os.O_CREAT, mode) for
     file_name in file_names]
    return result


def _getattr(root, path, fh=None):
    st = os.lstat(full_path(root, path))
    return_dictionary = dict()
    return_dictionary['st_atime'] = st.st_atime
    return_dictionary['st_ctime'] = st.st_ctime
    return_dictionary['st_gid'] = st.st_gid
    return_dictionary['st_mode'] = st.st_mode
    return_dictionary['st_mtime'] = st.st_mtime
    return_dictionary['st_nlink'] = st.st_nlink
    return_dictionary['st_size'] = st.st_size
    return_dictionary['st_uid'] = st.st_uid
    return return_dictionary


def _read(root, path, length, offset, fh):
    os.lseek(fh, offset, os.SEEK_SET)
    return os.read(fh, length)


def _write(root, path, buf, offset, fh):
    os.lseek(fh, offset, os.SEEK_SET)
    return os.write(fh, buf)
