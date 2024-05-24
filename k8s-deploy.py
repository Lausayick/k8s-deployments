#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File        : k8s-deploy.py
@Time        : 2024/5/13 13:55
@Author      : Lausayick
@Email       : lausayick@foxmail.com
@Software    : PyCharm
@Function    :
@CoreLibrary :
"""
import json
import os
import socket

CONFIG_PATH = r'config/config.json'
FLOW_PATH = r"config/flow.json"


def deploy_k8s_master(config_json: dict, node_type: str = "Nodes"):
    """
    Function:
      Run kubernetes deploy with config.

    Return:
      {
        status: "Success",  # "Error"
        command: "",
        response: ""
      } for each step.
    """
    if node_type not in {'Master', 'Nodes'}:
        return {"status": "Error", "command": "Input", "message": "Error Input Value."}
    # Read basic server config information.
    if node_type == 'Master':
        ip = config_json['master']['ip']
        hostname = config_json['master']['hostname']
        is_gpu = config_json['master']['is_gpu']
    else:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
            status = False
        for node_info in config_json['nodes']:
            if node_info['ip'] == ip:
                hostname = node_info['hostname']
                is_gpu = node_info['is_gpu']
                status = True
                break
        if not status:
            return {"status": "Error", "command": "Get Server Config", "message": "No Such Node In Config."}
    # Run as command
    # # Basic Environment Dependency Configuration
    if config_json['os'] == 'CentOS':
        settings_commands = [
            f"hostnamectl set-hostname {hostname}",
            f"systemctl stop firewalld",
            f"systemctl disable firewalld",
            f"sed -i 's/enforcing/disabled/' /etc/selinux/config",
            f"sed -ri 's/.*swap.*/#&/' /etc/fstab",
            f"swapoff -a",
            f"""cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF""",
            f"sysctl --system"
        ]
    elif config_json['os'] == "Ubuntu":
        settings_commands = [
            f"hostnamectl set-hostname {hostname}",
            f"ufw stop",
            f"ufw disable",
            f"sed -i 's/enforcing/disabled/' /etc/selinux/config",
            f"sed -ri 's/.*swap.*/#&/' /etc/fstab",
            f"swapoff -a",
            f"""cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF""",
            f"sysctl --system"
        ]
    for command in settings_commands:
        # os.system(command=command)
        print(command)

    # # Docker Install
    docker_commands = [
        f'''
cat > /etc/yum.repos.d/kubernetes.repo << EOF
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=0
repo_gpgcheck=0
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
        ''',
        f"curl -s https://get.docker.com/ | sh",
        '''
cat > /etc/docker/daemon.json << EOF
{
    "exec-opts": ["native.cgroupdriver=systemd"  ],
    "registry-mirrors": ["http://docker-registry-mirror.kodekloud.com"]
}
EOF
        ''',
        f"systemctl enable docker",
        f"systemctl start docker"
    ]
    for command in docker_commands:
        # os.system(command=command)
        print(command)

    # # Kubernetes Install
    kubernetes_version = config_json['version']['kubernetes']
    pause_version = config_json['version']['pause']
    Kubernetes_commands = [
        f'''
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-controller-manager:v{kubernetes_version}
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy:v{kubernetes_version}
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-apiserver:v{kubernetes_version}
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-scheduler:v{kubernetes_version}
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/coredns:1.9.3
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/etcd:3.5.6-0
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/pause:{pause_version}
        ''',
        "wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.2/cri-dockerd-0.3.2-3.el7.x86_64.rpm",
        "rpm -ivh cri-dockerd-0.3.2-3.el7.x86_64.rpm"
    ]

def read_config():
    """
    Function:
      Read config information as json type.

    Return:
      config_json: config json.
    """
    try:
        config_json = json.loads(open(CONFIG_PATH, "r").read())
        return config_json
    except FileNotFoundError as except_error:
        return {"status": "Success", "info": "No Such Config File!"}


def rewrite_config(config_json: dict):
    """
    Function:
      Rewrite config information as json type.

    Return:
      config_json: Status.
    """
    try:
        open(CONFIG_PATH, 'w').write(json.dumps(config_json, indent=2))
        return True
    except Exception as except_error:
        return False
    

if __name__ == '__main__':
    config_json = read_config()
    # config_json['version']["kubelet"] = "1.26.6"
    # rewrite_config(config_json=config_json)
    print(deploy_k8s_master(node_type='Master', config_json=config_json))
