#!/bin/bash

# установка ----------------------------------
sudo apt install snapd
sudo snap install lxd
sudo lxd init --auto

# настройка ----------------------------------
lxc config set core.https_address "[::]:8443"
lxc profile create docker-enabled

lxc profile edit docker-enabled << 'EOF'
config:
  security.nesting: "true"
  security.syscalls.intercept.mknod: "true"
  security.syscalls.intercept.setxattr: "true"
description: Profile for Docker-enabled containers
devices: {}
name: docker-enabled
EOF

# создаем базовый образ
lxc launch ubuntu:24.04 base-builder \
  --profile default \
  --profile docker-enabled

lxc exec base-builder -- cloud-init status --wait

lxc exec base-builder -- bash -c "
  apt-get update -q &&
  curl -fsSL https://get.docker.com | sh &&
  apt-get install -y docker-compose-plugin &&
  apt-get clean &&
  rm -rf /var/lib/apt/lists/* &&
  mkdir -p /etc/docker &&
  cat > /etc/docker/daemon.json << 'EOF'
{
  \"storage-driver\": \"vfs\"
}
EOF
  systemctl restart docker
"

# устанавливаем нужные образы
lxc exec base-builder -- bash -c "
  docker pull postgres:16-alpine &&
  docker pull redis:7-alpine &&
  docker pull nginx:alpine
"
docker build \
  -f ~/prod-polygon/environments/monolith-shop/backend.Dockerfile \
  -t environment-backend:latest \
  ~/prod-polygon/environments/monolith-shop/

docker save environment-backend:latest | lxc exec base-builder -- docker load

sudo tee /etc/systemd/system/lxd-docker-network-fix.service > /dev/null <<'EOF'
[Unit]
Description=Allow LXD bridge traffic through Docker's DOCKER-USER chain
After=docker.service
Requires=docker.service
PartOf=docker.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/iptables -I DOCKER-USER -s 10.75.164.0/24 -j ACCEPT
ExecStart=/usr/sbin/iptables -I DOCKER-USER -d 10.75.164.0/24 -j ACCEPT
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now lxd-docker-network-fix.service
lxc exec base-builder -- systemctl stop docker.socket docker.service containerd.service
sleep 3

lxc stop base-builder
sleep 2

# публикуем образ
lxc image delete prod-polygon-base
lxc publish base-builder --alias prod-polygon-base
lxc delete base-builder