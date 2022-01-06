#/usr/bin/python
import progressbar
import argparse
import datetime
import time
import pytz
import re
from kubernetes import client, config
barprogress = 0
bar = progressbar.ProgressBar(maxval=20, \
    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])

def create_deployment_object(DEPLOYMENT_NAME,version:str="1.15.4",replicas:int=3):
    # Configureate Pod template container
    container = client.V1Container(
        name="nginx",
        image="nginx:"+version,
        ports=[client.V1ContainerPort(container_port=80)],
        resources=client.V1ResourceRequirements(
            requests={"cpu": "100m", "memory": "200Mi"},
            limits={"cpu": "500m", "memory": "500Mi"},
        ),
    )

    # Create and configure a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "nginx"}),
        spec=client.V1PodSpec(containers=[container]),
    )
    progress(barprogress)
    # Create the specification of deployment
    spec = client.V1DeploymentSpec(
        replicas=replicas, template=template, selector={
            "matchLabels":
            {"app": "nginx"}})

    # Instantiate the deployment object
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=DEPLOYMENT_NAME),
        spec=spec,
    )
    progress(barprogress)
    return deployment

def get_deployment(core, name, replicas:int=0):
    res=False
    ret = core.list_pod_for_all_namespaces(watch=False)
    rep=0
    progress(barprogress)
    for i in ret.items:
        pod_name=""
        if re.search("^(\S+)-\w+-\w+$", i.metadata.name):
            pod_name=re.search("^(\S+)-\w+-\w+$", i.metadata.name).group(1)
        else:
            pass
        if(pod_name == name):
            if (i.status.phase == "Running"):
                rep=rep+1

    if rep == replicas:
        progress(barprogress)
        print("[INFO] Replications count matched")
        res=True
    else:
        progress(barprogress)
        print("[ERROR] Replications not matched")
        res=False

    return res    
    
def create_deployment(api, core, deployment, DEPLOYMENT_NAME:str="nginx-deployment", namespace:str="default", replicas:int=3):
    try:
        # Create deployement
        resp = api.create_namespaced_deployment(
            body=deployment, namespace=namespace
        )
        progress(barprogress)
        time.sleep(2*replicas)
        get_pod=get_deployment(core, name=DEPLOYMENT_NAME, replicas=replicas)
        if get_pod:
            progress(barprogress)
            print("\n[INFO] deployment `" + DEPLOYMENT_NAME + "` created.\n")
            print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
            print(
                "%s\t\t%s\t%s\t\t%s\n"
                % (
                    resp.metadata.namespace,
                    resp.metadata.name,
                    resp.metadata.generation,
                    resp.spec.template.spec.containers[0].image,
                )
            )
        else:
            progress(barprogress)
            print("\n[ERROR] deployment `" + DEPLOYMENT_NAME + "` not created successfully.\n")
            print("\n{}".format(resp.status))
    except Exception as e:
        progress(barprogress)
        print("\n[ERROR] Exception on creating deployment.\n")
        print("{}".format(e))

def update_deployment(api, core, deployment, DEPLOYMENT_NAME:str="nginx-deployment", namespace:str="default", version:str="1.16.0", replicas:int=3):
    try:
        # patch the deployment
        resp = api.patch_namespaced_deployment(
            name=DEPLOYMENT_NAME, namespace=namespace, body=deployment
        )
        progress(barprogress)
        time.sleep(2*replicas)
        get_pod=get_deployment(core, name=DEPLOYMENT_NAME, replicas=replicas)
        if get_pod:
            progress(barprogress)
            print("\n[INFO] deployment's container image updated.\n")
            print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
            print(
                "%s\t\t%s\t%s\t\t%s\n"
                % (
                    resp.metadata.namespace,
                    resp.metadata.name,
                    resp.metadata.generation,
                    resp.spec.template.spec.containers[0].image,
                )
            )
        else:
            progress(barprogress)
            print("\n[ERROR] Deployment verification failed.\n")
            print("{}".format(e))
    except Exception as e:
        progress(barprogress)
        print("\n[ERROR]: Exception on deleting the deployment.")
        print("\n{}".format(e))

def restart_deployment(api, core, deployment, replicas:int=3, DEPLOYMENT_NAME:str="nginx-deployment", namespace:str="default"):
    try:
        deployment.spec.template.metadata.annotations = {
            "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow()
            .replace(tzinfo=pytz.UTC)
            .isoformat()
        }
        progress(barprogress)
        # patch the deployment
        resp = api.patch_namespaced_deployment(
            name=DEPLOYMENT_NAME, namespace=namespace, body=deployment
        )
        time.sleep(10)
        get_pod=get_deployment(core, name=DEPLOYMENT_NAME, replicas=replicas)
        if get_pod:
            progress(barprogress)
            print("\n[INFO] deployment `" + DEPLOYMENT_NAME + "` Restarted.")
        else:
            progress(barprogress)
            print("\n[ERROR] Restarting `" + DEPLOYMENT_NAME + "` failed")

    except Exception as e:
        progress(barprogress)
        print("\n[ERROR]: Exception on restarting the deployment.")
        print("\n{}".format(e))



def delete_deployment(api, core, DEPLOYMENT_NAME:str="nginx-deployment", namespace="default"):
    try:
        # Delete deployment
        resp = api.delete_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy="Foreground", grace_period_seconds=5
            ),
        )
        progress(barprogress)
        print("\n[INFO] Sleeping for 10 seconds before deployment cleanup...")
        time.sleep(10)
        n=4
        while n:
            get_pod=get_deployment(core, name=DEPLOYMENT_NAME)
            if get_pod:
                break
            print("\n[INFO] Sleeping 5 more seconds for deployment cleanup...")
            time.sleep(5)
            n=n-1
        progress(barprogress)
        if get_pod:
            print("\n[INFO] deployment `" + DEPLOYMENT_NAME + "` deleted.")
        else:
            print("\n[ERROR] Deleting `" + DEPLOYMENT_NAME + "` failed")
    except Exception as e:
        progress(barprogress)
        print("\n[ERROR]: Exception on deleting the deployment.")
        print("\n{}".format(e))

def get_namespace(core_v1, namespace):
    try:
        namespaces = core_v1.list_namespace()
        progress(barprogress)
        for ns in namespaces.items:
            if ns.metadata.name == namespace:
                return True

        return False
    except Exception as e:
        progress(barprogress)
        print("\n[Error] Exception on getting namespace")
        print("\n{}".format(e))

def create_namespace(core_v1, namespace):
    try:
        if get_namespace(core_v1, namespace):
            progress(barprogress)
            print("\n[INFO] Namespace {} already exists, proceeding deployment".format(namespace))
            return True
        else:    
            body = client.V1Namespace()
            body.metadata = client.V1ObjectMeta(name=namespace)
            resp=core_v1.create_namespace(body)
            progress(barprogress)
            time.sleep(2)
            if get_namespace(core_v1, namespace):
                progress(barprogress)
                print("\n[INFO] Namespace created successfully")
                return True
            else:
                progress(barprogress)
                print("\n[ERROR] Namespace not created successfully")
    except Exception as e:
        print("\n[ERROR]: Exception on creating the namespace.")
        print("\n{}".format(e))

def progress(barprogress):
    barprogress=barprogress+1
    bar.update(barprogress)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="nginx-deployment", help="Define the deployment name, default='nginx-deployment'", type=str)
    parser.add_argument("--action", default="deploy", choices=["deploy", "update", "restart","delete"], help="Options deploy(default), update, restart or delete", type=str)
    parser.add_argument("--version", default="1.15.4", help="Define the version, default='1.15.4'", type=str)
    parser.add_argument("--namespace", default="default", help="Define the namespace, default='default'", type=str)
    parser.add_argument("--replica", default=3, help="Define the replica count, default=3", type=int)
    parser.add_argument("--kubeconfig", default="/home/ubuntu/.kube/config", help="Define path of kube config, default='~/.kube/config'", type=str)
    args = parser.parse_args()
    progress(barprogress)
    config.load_kube_config(config_file=args.kubeconfig)
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    progress(barprogress)

    deployment = create_deployment_object(DEPLOYMENT_NAME=args.name, version=args.version , replicas=args.replica)
    progress(barprogress)
    if args.action=="deploy":
        if create_namespace(core_v1, args.namespace):
            create_deployment(apps_v1, core_v1, deployment, DEPLOYMENT_NAME=args.name, replicas=args.replica, namespace=args.namespace)
            progress(barprogress)
        else:
            print("\n[ERROR] Deployment failed since the namepsace not created")
    elif args.action=="update":
        update_deployment(apps_v1, core_v1, deployment, DEPLOYMENT_NAME=args.name, version=args.version, replicas=args.replica, namespace=args.namespace)
        progress(barprogress)
    elif args.action=="restart":
        restart_deployment(apps_v1, core_v1, deployment, DEPLOYMENT_NAME=args.name, namespace=args.namespace, replicas=args.replica)
        progress(barprogress)
    elif args.action=="delete":
        delete_deployment(apps_v1, core_v1, DEPLOYMENT_NAME=args.name, namespace=args.namespace)
        progress(barprogress)

print("Kubernetes Nginx Deployer")
if __name__ == "__main__":
    bar.start()
    progress(barprogress)
    main()
    progress(barprogress)
    bar.finish()
