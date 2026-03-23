#!/bin/sh
echo "Breaking nginx configuration..."
docker exec environment-nginx-1 sh -c \
  "cat /etc/nginx/conf.d/default.conf | \
  sed 's/5000/9999/' | \
  tee /etc/nginx/conf.d/default.conf > /dev/null && \
  nginx -s reload"
echo "Done. Nginx now proxies to wrong port."