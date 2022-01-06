##########################################################################
#                   KUBERNETES NGINX DEPLOYER                            #
##########################################################################

#!-- How to install requirements 

chmod 777 install_requirements.sh
sudo sh install_requirements.sh

#!-- How to uninstall requirements

chmod 777 remove_requirements.sh
sudo sh remove_requirements.sh 

#!-- How to build the binary(optional):

pyinstaller --onefile KND.py

#!-- Installation Steps:

sudo cp dist/KND /usr/local/bin/KND

#!-- Steps to run the code:

$ KND --help

Kubernetes Nginx Deployer
usage: KND [-h] [--name NAME] [--action {deploy,update,restart,delete}] [--version VERSION] [--namespace NAMESPACE] [--replica REPLICA] ]   5%
           [--kubeconfig KUBECONFIG]

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           Define the deployment name, default='nginx-deployment'
  --action {deploy,update,restart,delete}
                        Options deploy(default), update, restart or delete
  --version VERSION     Define the version, default='1.15.4'
  --namespace NAMESPACE
                        Define the namespace, default='default'
  --replica REPLICA     Define the replica count, default=3
  --kubeconfig KUBECONFIG
                        Define path of kube config, default='~/.kube/config'


#!-- Sample code:

- Bring up the nginx deployment            : KND --name=nginx-deployment --action=deploy --version=1.16.0
- Update replicate set of nginx deployment : KND --name=nginx-deployment --action=update --replica=5
- Restart the nginx deployemnt             : KND --name=nginx-deployment --action=restart --replica=5
- Delete the nginx deployment              : KND --name=nginx-deployment --action=delete

#!-- UnInstallation Steps:

sudo rm -rf /usr/local/bin/KND

