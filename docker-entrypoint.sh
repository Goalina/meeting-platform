#!/usr/bin/env bash
set -e

# Check if we are in the correct directory before running commands.
if [[ ! $(pwd) == '/home/meetingplatform/meeting-platform' ]]; then
	echo "Running in the wrong directory...switching to..."
	cd /home/meetingplatform/meeting-platform
fi

python3 manage.py migrate

function modify_ip() {
  CURRENT_IP=$(grep -v '^#' /etc/hosts | awk '{print $1}'|grep -E '([0-9]{1,3}\.){3}[0-9]{1,3}'|grep -v '^127\.')

  if [ -z "$CURRENT_IP" ]; then
    echo "not found the local ip"
    exit 1
  fi

  # 备份原始配置文件
  cp /home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini /home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini.bak

  # 替换HTTPS绑定IP
  sed -i "s/https={{ip}}:8080/https=$CURRENT_IP:8080/" /home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini.bak

  mv /home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini.bak /home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini

  echo "set new ip in uwsgi.ini: $CURRENT_IP"
}

modify_ip

exec $@