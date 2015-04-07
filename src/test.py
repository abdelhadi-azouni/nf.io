from hyp import vnfs_docker

hyp = vnfs_docker.Docker()

#cont_id = '456174f712a7'
cont_id, return_code, return_msg = hyp.deploy("cn107-cn", "mfbari", "nginx", "nginx")
print cont_id, return_code, return_msg

#response, code, msg = hyp.start("10.10.0.106", cont_id)
#print response, code, msg

#response, code, msg = hyp.pause("10.10.0.106", cont_id)
#print response, code, msg

