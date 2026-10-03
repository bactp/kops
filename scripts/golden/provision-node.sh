#!/usr/bin/env bash
# Runs INSIDE the builder VM as a sudo-capable user. Turns an Ubuntu 22.04 cloud image into the KOPS node golden image.
# Idempotent: safe to re-run on top of an earlier golden image.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
K8S_MINOR="${K8S_MINOR:-v1.35}"
YQ_VERSION="${YQ_VERSION:-v4.47.1}"
LOCAL_PATH_VERSION="${LOCAL_PATH_VERSION:-v0.0.31}"
IMAGES=(
  "docker.io/library/busybox:1.36.1"
  "registry.k8s.io/e2e-test-images/agnhost:2.53"
  "docker.io/rancher/local-path-provisioner:${LOCAL_PATH_VERSION}"
)

echo "== kernel modules, sysctl, containerd, kubeadm"
sudo swapoff -a || true
printf 'overlay\nbr_netfilter\n' | sudo tee /etc/modules-load.d/k8s.conf >/dev/null
printf 'net.bridge.bridge-nf-call-iptables = 1\nnet.bridge.bridge-nf-call-ip6tables = 1\nnet.ipv4.ip_forward = 1\n' | sudo tee /etc/sysctl.d/99-k8s.conf >/dev/null
sudo modprobe overlay; sudo modprobe br_netfilter; sudo sysctl --system >/dev/null 2>&1 || true
sudo apt-get update -qq
sudo apt-get install -y -qq apt-transport-https ca-certificates curl gpg containerd >/dev/null
sudo mkdir -p /etc/containerd; containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd; sudo systemctl enable containerd >/dev/null 2>&1
sudo mkdir -p /etc/apt/keyrings
curl -fsSL "https://pkgs.k8s.io/core:/stable:/${K8S_MINOR}/deb/Release.key" | sudo gpg --dearmor --yes -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/${K8S_MINOR}/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq kubelet kubeadm kubectl >/dev/null
sudo apt-mark hold kubelet kubeadm kubectl >/dev/null
sudo systemctl enable kubelet >/dev/null 2>&1
sudo kubeadm config images pull --kubernetes-version "$(kubeadm version -o short)" >/dev/null 2>&1

echo "== cluster add-on manifests and images (the sandbox has no internet)"
sudo mkdir -p /opt/cni
curl -fsSL https://api.github.com/repos/projectcalico/calico/releases/latest -o /tmp/rel.json
CV=$(grep -m1 '"tag_name"' /tmp/rel.json | cut -d'"' -f4); rm -f /tmp/rel.json
sudo curl -fsSL -o /opt/cni/calico.yaml "https://raw.githubusercontent.com/projectcalico/calico/${CV}/manifests/calico.yaml"
sudo curl -fsSL -o /opt/cni/local-path.yaml "https://raw.githubusercontent.com/rancher/local-path-provisioner/${LOCAL_PATH_VERSION}/deploy/local-path-storage.yaml"
# kind ships a default StorageClass called "standard"; scenarios were validated against it
sudo sed -i '/^kind: StorageClass/,/^---/ s/^  name: local-path$/  name: standard\n  annotations:\n    storageclass.kubernetes.io\/is-default-class: "true"/' /opt/cni/local-path.yaml
for img in $(grep -E '^\s+image:' /opt/cni/calico.yaml | awk '{print $2}' | sort -u) "${IMAGES[@]}"; do
  sudo ctr -n k8s.io images pull "$img" >/dev/null 2>&1 || echo "pull failed: $img"
done
echo "calico=$CV; images in containerd: $(sudo ctr -n k8s.io images ls -q | wc -l)"

echo "== tools a candidate expects (practice profile; the strict exam profile is a later release)"
sudo apt-get install -y -qq vim jq wget man-db bash-completion openssh-client netcat-openbsd dnsutils iputils-ping less >/dev/null
sudo curl -fsSL -o /usr/local/bin/yq "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64"; sudo chmod 755 /usr/local/bin/yq
sudo tee /etc/profile.d/kops.sh >/dev/null <<'PROFILE'
alias k=kubectl
export EDITOR=vim
if command -v kubectl >/dev/null; then source <(kubectl completion bash); complete -o default -F __start_kubectl k; fi
PROFILE

echo "== networking independent of the NIC's MAC, faster boot"
sudo mkdir -p /etc/cloud/cloud.cfg.d
echo 'network: {config: disabled}' | sudo tee /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg >/dev/null
sudo rm -f /etc/netplan/50-cloud-init.yaml
printf 'network:\n  version: 2\n  ethernets:\n    all-en:\n      match: {name: "e*"}\n      dhcp4: true\n      dhcp-identifier: mac\n' | sudo tee /etc/netplan/01-dhcp.yaml >/dev/null
sudo chmod 600 /etc/netplan/01-dhcp.yaml
sudo systemctl disable --now snapd.service snapd.socket snapd.seeded.service snapd.apparmor.service 2>/dev/null || true
sudo apt-get purge -y -qq snapd lxd-installer >/dev/null 2>&1 || true
sudo systemctl disable apt-daily.timer apt-daily-upgrade.timer motd-news.timer fwupd-refresh.timer ua-timer.timer 2>/dev/null || true
sudo systemctl disable unattended-upgrades.service ModemManager.service multipathd.service multipathd.socket udisks2.service 2>/dev/null || true
sudo systemctl mask systemd-networkd-wait-online.service >/dev/null 2>&1 || true
sudo sed -i -E 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=0/' /etc/default/grub
grep -q GRUB_RECORDFAIL_TIMEOUT /etc/default/grub || echo 'GRUB_RECORDFAIL_TIMEOUT=0' | sudo tee -a /etc/default/grub >/dev/null
sudo update-grub >/dev/null 2>&1 || true

echo "== make every clone look like a first boot"
sudo cloud-init clean --logs --seed
sudo truncate -s0 /etc/machine-id; sudo rm -f /var/lib/dbus/machine-id
sudo rm -f /home/*/.ssh/known_hosts /var/log/*.log 2>/dev/null || true
sudo journalctl --rotate >/dev/null 2>&1 || true
sync
echo "provisioned: kubeadm=$(kubeadm version -o short) containerd=$(containerd --version | awk '{print $3}') used=$(df -h / | awk 'NR==2{print $3}')"
