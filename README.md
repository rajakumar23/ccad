Introduction
============

The intention of this project is to automate the deployment of CC 13.x using Ansible, Jinja2, Yaml and Python. Based on 
the servers selected the IP fabric leaf switch will be provisioned first and then continues with the contrail cloud installation. 
As of now, following topologies can be built within 6 hours of time. This code has been tested for CC 13.5.

1. Topology_1 : 1 Jumphost + 1 Control Host + 1 Kernel Compute
2. Topology_2 : 1 Jumphost + 1 Control Host + 1 DPDK Compute
3. Topology_3 : 1 Jumphost + 1 Control Host + 1 Kernel Compute + 1 DPDK Compute
4. Topology_4 : 1 Jumphost + 3 Control Host + 1 Kernel Compute + 1 DPDK Compute

Note: Consider this as a prototype, as only part of the code has been shared. To make it work, one has to insert the server details to mysql db
and make changes to the python script respectively. Also, place the CC installer script & appformix license in config folder

Resource Details
----------------
Servers:
    1. server_1
    2. server_2
    3. server_3
    4. server_4
    5. server_5
    6. server_6
    7. server_7
    8. server_8


CC Deployment Details
---------------------
1. Spawn a VM 

2. Login into VM and change directory to /root

3. Create a new directory "mkdir cc13.5"

4. Fetch/copy the source from this page 

5. Change directory to  /root/cc13.5 

6. Excute the below command from PWD to pull an pyez-ansible container which is needed to provision the fabric leaf device and kick start contrail cloud deployment
   docker run -d --name cc_pyez_ansible -it --rm -v $PWD:/project -v $PWD/configs/apk.txt:/extras/apk.txt -v $PWD/configs/requirements.txt:/extras/requirements.txt juniper/pyez-ansible

7. Based on the topology to be built, update the "configs/user_input.yml" file, which is self explainatory.

8. Install RH7.7 for all the selected servers.

9. Login into the pyez ansible container as follows,
   docker exec -it cc_pyez_ansible bash

10. Execute the ansible playbook as follows,
    ansible-playbook -i hosts cc_deploy -vvvv

11. Wait for almost 5 to 6 hours for the deployment to get completed

12. Once done with the servers, please execute the below playbook to revert the configs back to original on the fabric leaf
    switch. Make sure the configs are reverted back to original and then unreserve the servers.
    ansible-playbook -i hosts cc_cleanup -vvvv

Author Information
------------------
rajakumar.cloud@gmail.com
