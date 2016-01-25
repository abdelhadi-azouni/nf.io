from vnfs_operations import VNFSOperations
import os

special_files = ['rx_bytes', 'tx_bytes', 'pkt_drops', 'status']
action_files = ['action']

def full_path(root, partial_path):
    if partial_path.startswith("/"):
        partial_path = partial_path[1:]
    return os.path.join(root, partial_path)


def _mkdir(root, path, mode):
    vnfs_ops = VNFSOperations(root)
    result = vnfs_ops.vnfs_create_vnf_instance(path, mode)
    return result


def _getattr(root, path, fh=None):
    vnfs_ops = VNFSOperations(root)
    f_path = full_path(root, path)
    st = os.lstat(f_path)
    file_name = vnfs_ops.vnfs_get_file_name(f_path)
    return_dictionary = dict()
    return_dictionary['st_atime'] = st.st_atime
    return_dictionary['st_ctime'] = st.st_ctime
    return_dictionary['st_gid'] = st.st_gid
    return_dictionary['st_mode'] = st.st_mode
    return_dictionary['st_mtime'] = st.st_mtime
    return_dictionary['st_nlink'] = st.st_nlink
    return_dictionary['st_size'] = st.st_size
    return_dictionary['st_uid'] = st.st_uid
    if file_name in special_files:
        return_dictionary['st_size'] = 1000
    return return_dictionary


def _read(root, path, length, offset, fh):
    f_path = full_path(root, path)
    vnfs_ops = VNFSOperations(root)
    file_name = vnfs_ops.vnfs_get_file_name(f_path)
    nf_path = ''
    if file_name in special_files:
        tokens = f_path.encode('ascii').split('/')
        last_index_to_keep = tokens.index('nf-types') + 3
        nf_path = "/".join(tokens[0:last_index_to_keep])
    if file_name == "rx_bytes":
        ret_str = vnfs_ops.vnfs_get_rx_bytes(nf_path)
        if offset >= len(ret_str):
            ret_str = ''
    elif file_name == 'tx_bytes':
        ret_str = vnfs_ops.vnfs_get_tx_bytes(nf_path)
        if offset >= len(ret_str):
            ret_str = ''
    elif file_name == 'pkt_drops':
        ret_str = vnfs_ops.vnfs_get_pkt_drops(nf_path)
        if offset >= len(ret_str):
            ret_str = ''
    elif file_name == 'status':
        ret_str = vnfs_ops.vnfs_get_status(nf_path)
        if offset >= len(ret_str):
            ret_str = ''
    else:
        os.lseek(fh, offset, os.SEEK_SET)
        ret_str = os.read(fh, length)
    return ret_str


def _write(root, path, buf, offset, fh):
    f_path = full_path(root, path)
    vnfs_ops = VNFSOperations(root)
    file_name = vnfs_ops.vnfs_get_file_name(f_path)
    if file_name == "action":
        path_tokens = f_path.split("/")
        nf_path = "/".join(path_tokens[0:path_tokens.index("nf-types") + 3])
        if buf.rstrip("\n") == "activate":
            vnfs_ops.vnfs_deploy_nf(nf_path)
        elif buf.rstrip("\n") == "stop":
            vnfs_ops.vnfs_stop_vnf(nf_path)
        os.lseek(fh, offset, os.SEEK_SET)
        os.write(fh, buf.rstrip("\n"))
        return len(buf)
    else:
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)
