#!/bin/sh
# nginx 官方镜像会按文件名顺序执行 /docker-entrypoint.d。令牌只允许十六进制，避免写进配置时被解释。
set -eu
TOKEN=$(printf '%s' "${LOCAL_DEV_TOKEN:-}" | tr -cd 'A-Za-z0-9')
if [ -n "$TOKEN" ]; then
  sed -i "/proxy_set_header X-Forwarded-For/a\\        proxy_set_header X-Studio-Local-Token ${TOKEN};" /etc/nginx/conf.d/default.conf
fi
