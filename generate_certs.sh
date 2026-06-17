#!/bin/bash
mkdir -p ~/lxd-certs && cd ~/lxd-certs
openssl req -x509 -nodes \
  -newkey ec -pkeyopt ec_paramgen_curve:P-384 \
  -keyout client.key \
  -out client.crt \
  -days 3650 \
  -subj "/CN=prod-polygon-backend"

lxc config trust add client.crt --name prod-polygon-backend
cp client.key client.crt ~/prod-polygon/backend/lxd-certs/

sudo cp /var/snap/lxd/common/lxd/server.crt ~/lxd-certs/lxd-server.crt
sudo chown $USER:$USER ~/lxd-certs/lxd-server.crt
cp ~/lxd-certs/lxd-server.crt ~/prod-polygon/backend/lxd-certs/