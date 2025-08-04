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
  chmod 750 /home/meetingplatform/meeting-platform/deploy/production/gunicorn.conf.py
  chmod 750 /home/meetingplatform/meeting-platform/

  cp /home/meetingplatform/meeting-platform/deploy/production/gunicorn.conf.py /home/meetingplatform/meeting-platform/deploy/production/gunicorn.conf.py.bak

  # 替换HTTPS绑定IP
  sed -i "s/{{ip}}/${CURRENT_IP}/" /home/meetingplatform/meeting-platform/deploy/production/gunicorn.conf.py.bak

  mv /home/meetingplatform/meeting-platform/deploy/production/gunicorn.conf.py.bak /home/meetingplatform/meeting-platform/gunicorn.conf.py

  chmod 550 /home/meetingplatform/meeting-platform/deploy/production/gunicorn.conf.py
  chmod 550 /home/meetingplatform/meeting-platform/
  chmod 550 /home/meetingplatform/meeting-platform/gunicorn.conf.py
  echo "modify new ip in gunicorn success"
}

modify_ip

exec $@