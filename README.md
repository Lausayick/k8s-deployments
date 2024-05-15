# k8s-deployments

[//]: # (基础配置)
<details>
<summary><font color="red" size="5">Basic Settings</font></summary>

> Choose based on your operating system

<details>
<summary><font color="#808080" size="3">&emsp;CentOS</font></summary>

- set hostname _(for each node)_
```
hostnamectl set-hostname k8s-master
```

- set ip connect hostname _(for master)_
```
cat >> /etc/hosts << EOF
master-ip k8s-master
node1-ip k8s-node1
node2-ip k8s-node2
EOF
```

- set firewall enabled _(for each node)_
```
systemctl stop firewalld
systemctl disable firewalld
```

- disable selinux and swap _(for each node)_
```
# Always close
sed -i 's/enforcing/disabled/' /etc/selinux/config  
sed -ri 's/.*swap.*/#&/' /etc/fstab

# Temp close
setenforce 0
swapoff -a
```

- change ipv4 connect _(for each node)_
```
cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
```

- enable changes _(for each node)_
```
sysctl --system
```
</details>

<details>
<summary><font color="#808080" size="3">&emsp;Ubuntu</font></summary>

- set hostname _(for each node)_
```
hostnamectl set-hostname k8s-master
```

- set ip connect hostname _(for master)_
```
cat >> /etc/hosts << EOF
master-ip k8s-master
node1-ip k8s-node1
node2-ip k8s-node2
EOF
```

- set firewall enabled _(for each node)_
```
ufw stop 
ufw disable
```

- disable selinux and swap _(for each node)_
```
# Always close
sed -i 's/enforcing/disabled/' /etc/selinux/config  
sed -ri 's/.*swap.*/#&/' /etc/fstab

# Temp close
setenforce 0
swapoff -a
```

- change ipv4 connect _(for each node)_
```
cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
```

- enable changes _(for each node)_
```
sysctl --system
```
</details>
</details>


[//]: # (Docker安装)
<details>
<summary><font color="red" size="5">Docker Installing</font></summary>

- set kubernetes.repo for mirror _(for each node)_
```
cat > /etc/yum.repos.d/kubernetes.repo << EOF
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=0
repo_gpgcheck=0
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
```

- install docker _(for each node)_
```
curl -s https://get.docker.com/ | sh
```

- config daemon.json _(for each node)_
```
cat > /etc/docker/daemon.json << EOF
{
    "exec-opts": ["native.cgroupdriver=systemd"  ],
    "registry-mirrors": ["http://docker-registry-mirror.kodekloud.com"  ]
}
EOF
```

- enable and run docker _(for each node)_
```
systemctl enable docker
systemctl start docker
```

- pull docker images _(for each node)_
```
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-controller-manager:v1.26.6
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy:v1.26.6
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-apiserver:v1.26.6
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-scheduler:v1.26.6
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/coredns:1.9.3
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/etcd:3.5.6-0
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.9
```

- do CRI config _(for each node, kubernetes version > 1.23)_
```
wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.2/cri-dockerd-0.3.2-3.el7.x86_64.rpm
rpm -ivh cri-dockerd-0.3.2-3.el7.x86_64.rpm

# 配置 pause 镜像
vim /usr/lib/systemd/system/cri-docker.service
ExecStart=/usr/bin/cri-dockerd --network-plugin=cni --pod-infra-container-image=registry.aliyuncs.com/google_containers/pause:3.9

# 生效配置
systemctl daemon-reload
systemctl enable --now cri-docker
```
</details>


[//]: # (Kubernetes安装)
<details>
<summary><font color="red" size="5">Kubernetes Installing</font></summary>

> Choose based on your operating system

<details>
<summary><font color="#808080" size="3">&emsp;CentOS</font></summary>

- install kubernetes _(for each node)_
```
yum install -y kubelet-1.26.6 kubeadm-1.26.6 kubectl-1.26.6
```

- enable kubelet _(for each node)_
```
systemctl enable kubelet
```

- Initialize kubernetes cluster _(for master)_
```
# Master 服务器
kubeadm init \
 --apiserver-advertise-address= $master-ip \
 --image-repository registry.aliyuncs.com/google_containers \
 --kubernetes-version v1.26.6 \
 --service-cidr=10.1.0.0/12 \
 --pod-network-cidr=10.244.0.0/16 \
 --cri-socket unix:///var/run/cri-dockerd.sock \
 --ignore-preflight-errors=all
```

- Configuration file environment _(for master)_
```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

- Join node into cluster _(for each node except master)_
```
# Use result return by kubeadm init
kubeadm join $master-ip:6443 --token zgl90c.m6dfmlmsr01208x6 --discovery-token-ca-cert-hash sha256:f15f0a822dc9af02d8ca0ba825b2ff4360556b54a8b7f0f8d29eb21b82fb77b1
--cri-socket unix:///var/run/cri-dockerd.sock
```

- Configuration network calico _(for master)_
```
wget https://docs.projectcalico.org/v3.18/manifests/calico.yaml

vim calico.yaml

# Edit CALICO_IPV4POOL_CIDR value same as kubeadm init '--pod-network-cidr'。
- name: CALICO_IPV4POOL_CIDR
  value: "10.244.0.0/16"
  
kubectl apply -f calico.yaml
```
</details>

<details>
<summary><font color="#808080" size="3">&emsp;Ubuntu</font></summary>

- install kubernetes _(for each node)_
```
apt-get install -y kubelet-1.26.6-00 kubeadm-1.26.6-00 kubectl-1.26.6-00
```

- enable kubelet _(for each node)_
```
systemctl enable kubelet
```

- Initialize kubernetes cluster _(for master)_
```
# Master 服务器
kubeadm init \
 --apiserver-advertise-address= $master-ip \
 --image-repository registry.aliyuncs.com/google_containers \
 --kubernetes-version v1.26.6 \
 --service-cidr=10.1.0.0/12 \
 --pod-network-cidr=10.244.0.0/16 \
 --cri-socket unix:///var/run/cri-dockerd.sock \
 --ignore-preflight-errors=all
```

- Configuration file environment _(for master)_
```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

- Join node into cluster _(for each node except master)_
```
# Use result return by kubeadm init
kubeadm join $master-ip:6443 --token zgl90c.m6dfmlmsr01208x6 --discovery-token-ca-cert-hash sha256:f15f0a822dc9af02d8ca0ba825b2ff4360556b54a8b7f0f8d29eb21b82fb77b1
--cri-socket unix:///var/run/cri-dockerd.sock
```

- Configuration network calico _(for master)_
```
wget https://docs.projectcalico.org/v3.18/manifests/calico.yaml

vim calico.yaml

# Edit CALICO_IPV4POOL_CIDR value same as kubeadm init '--pod-network-cidr'。
- name: CALICO_IPV4POOL_CIDR
  value: "10.244.0.0/16"
  
kubectl apply -f calico.yaml
```
</details>
</details>


[//]: # (Kubernetes插件配置)
<details>
<summary><font color="red" size="5">Kubernetes config</font></summary>

- network config _(for each node)_
```
vim mod.sh

# add content
#!/bin/bash
modprobe ip_vs
modprobe ip_vs_rr
modprobe ip_vs_wrr
modprobe ip_vs_sh
modprobe nf_conntrack_ipv4
modprobe br_netfilter

chmod +x mod.sh
bash mod.sh

vim /etc/rc.local

# add content
/root/mod.sh

chmod +x /etc/rc.local

cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
vm.swappiness=0
EOF

sysctl --system
```

- install metric tool _(for master)_
```
vim components-v0.5.0.yaml

apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    k8s-app: metrics-server
    rbac.authorization.k8s.io/aggregate-to-admin: "true"
    rbac.authorization.k8s.io/aggregate-to-edit: "true"
    rbac.authorization.k8s.io/aggregate-to-view: "true"
  name: system:aggregated-metrics-reader
rules:
- apiGroups:
  - metrics.k8s.io
  resources:
  - pods
  - nodes
  verbs:
  - get
  - list
  - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    k8s-app: metrics-server
  name: system:metrics-server
rules:
- apiGroups:
  - ""
  resources:
  - pods
  - nodes
  - nodes/stats
  - namespaces
  - configmaps
  verbs:
  - get
  - list
  - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server-auth-reader
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: extension-apiserver-authentication-reader
subjects:
- kind: ServiceAccount
  name: metrics-server
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server:system:auth-delegator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
- kind: ServiceAccount
  name: metrics-server
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  labels:
    k8s-app: metrics-server
  name: system:metrics-server
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:metrics-server
subjects:
- kind: ServiceAccount
  name: metrics-server
  namespace: kube-system
---
apiVersion: v1
kind: Service
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
spec:
  ports:
  - name: https
    port: 443
    protocol: TCP
    targetPort: https
  selector:
    k8s-app: metrics-server
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: metrics-server
  strategy:
    rollingUpdate:
      maxUnavailable: 0
  template:
    metadata:
      labels:
        k8s-app: metrics-server
    spec:
      containers:
      - args:
        - --cert-dir=/tmp
        - --secure-port=4443
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --metric-resolution=15s
        - --kubelet-insecure-tls
        image: registry.cn-shenzhen.aliyuncs.com/zengfengjin/metrics-server:v0.5.0
        imagePullPolicy: IfNotPresent
        livenessProbe:
          failureThreshold: 3
          httpGet:
            path: /livez
            port: https
            scheme: HTTPS
          periodSeconds: 10
        name: metrics-server
        ports:
        - containerPort: 4443
          name: https
          protocol: TCP
        readinessProbe:
          failureThreshold: 3
          httpGet:
            path: /readyz
            port: https
            scheme: HTTPS
          initialDelaySeconds: 20
          periodSeconds: 10
        resources:
          requests:
            cpu: 100m
            memory: 200Mi
        securityContext:
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
        volumeMounts:
        - mountPath: /tmp
          name: tmp-dir
      nodeSelector:
        kubernetes.io/os: linux
      priorityClassName: system-cluster-critical
      serviceAccountName: metrics-server
      volumes:
      - emptyDir: {}
        name: tmp-dir
---
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  labels:
    k8s-app: metrics-server
  name: v1beta1.metrics.k8s.io
spec:
  group: metrics.k8s.io
  groupPriorityMinimum: 100
  insecureSkipTLSVerify: true
  service:
    name: metrics-server
    namespace: kube-system
  version: v1beta1
  versionPriority: 100
  

# 部署安装
kubectl apply -f ./components-v0.5.0.yaml
```
</details>


[//]: # (GPU部署)
<details>
<summary><font color="red" size="5">Kubernetes GPU config</font></summary>

- references:
1. https://gitcode.com/NVIDIA/k8s-device-plugin/overview?utm_source=csdn_github_accelerator&isLogin=1


- Install nvidia-container-toolkit
```
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/libnvidia-container.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
```

- Install nvidia-device-plugin

```
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.3/nvidia-device-plugin.yml
```
- Change k8s-device-plugin for GPU virtualization
```
vim k8s-device-plugin.yaml

apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-device-plugin-daemonset
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: nvidia-device-plugin-ds
  updateStrategy:
    type: RollingUpdate
  template:
    metadata:
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ""
      labels:
        name: nvidia-device-plugin-ds
    spec:
      tolerations:
      - key: CriticalAddonsOnly
        operator: Exists
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      priorityClassName: "system-node-critical"
      containers:
      - image: 4pdosc/k8s-device-plugin:latest
        # - image: m7-ieg-pico-test01:5000/k8s-device-plugin-test:v0.9.0-ubuntu20.04
        imagePullPolicy: Always
        name: nvidia-device-plugin-ctr
        args: ["--fail-on-init-error=false", "--device-split-count=6", "--device-memory-scaling=2", "--device-cores-scaling=1"]
        # args: ["--fail-on-init-error=false", "--device-split-count=3", "--device-memory-scaling=3", "--device-cores-scaling=1"]
        env:
        - name: PCIBUSFILE
          value: "/usr/local/vgpu/pciinfo.vgpu"
        - name: NVIDIA_MIG_MONITOR_DEVICES
          value: all
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
            add: ["SYS_ADMIN"]
        volumeMounts:
          - name: device-plugin
            mountPath: /var/lib/kubelet/device-plugins
          - name: vgpu-dir
            mountPath: /usr/local/vgpu
          - mountPath: /tmp
            name: hosttmp
      volumes:
        - name: device-plugin
          hostPath:
            path: /var/lib/kubelet/device-plugins
        - name: vgpu-dir
          hostPath:
            path: /usr/local/vgpu
        - hostPath:
            path: /tmp
          name: hosttmp
      nodeSelector: 
        nvidia-vgpu: "on"
```

- restart for enable
```
systemctl restart docker
systemctl restart containerd
```
</details>
