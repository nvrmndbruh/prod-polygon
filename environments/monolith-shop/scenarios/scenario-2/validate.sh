#!/bin/sh
CONFIG=$(docker exec environment-nginx-1 \
  cat /etc/nginx/conf.d/default.conf 2>/dev/null)

if echo "$CONFIG" | grep -q "proxy_pass http://backend:5000"; then
  echo "OK: Nginx configuration is correct"
  exit 0
else
  echo "FAIL: Nginx is not proxying to correct port"
  echo "Current config: $CONFIG"
  exit 1
fi