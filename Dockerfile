FROM openeuler/openeuler:22.03

ARG user=meetingplatform
ARG group=meetingplatform
ARG uid=1000
ARG gid=1000


# 1.install
RUN yum install -y shadow wget git openssl openssl-devel tzdata python3-devel mariadb-devel python3-pip  \
    libXext libjpeg xorg-x11-fonts-75dpi xorg-x11-fonts-Type1 gcc ffmpeg hostname
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -d /home/meetingplatform/ -s /sbin/nologin -m ${user}

# 2.copy
COPY . /home/meetingplatform/meeting-platform/
RUN mv /home/meetingplatform/meeting-platform/deploy/fonts/simsun.ttc /usr/share/fonts/simsun.ttc
RUN rm -rf /home/meetingplatform/meeting-platform/Dockerfile
RUN rm -rf /home/meetingplatform/meeting-platform/deploy/config
RUN rm -rf /home/meetingplatform/meeting-platform/deploy/fonts

# 3.install
RUN pip3 install -r /home/meetingplatform/meeting-platform/requirements.txt && rm -rf /home/meetingplatform/meeting-platform/requirements.txt
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.centos8.x86_64.rpm && \
    rpm -i wkhtmltox-0.12.6-1.centos8.x86_64.rpm && \
    rm -f wkhtmltox-0.12.6-1.centos8.x86_64.rpm

# 4.clean
RUN chmod -R 550 /home/meetingplatform/meeting-platform/ && \
    chown -R ${user}:${group} /home/meetingplatform/meeting-platform/
RUN chmod 550 /home/meetingplatform/meeting-platform/manage.py && \
    chown ${user}:${group} /home/meetingplatform/meeting-platform/manage.py
RUN chmod 550 /home/meetingplatform/meeting-platform/docker-entrypoint.sh && \
    chown ${user}:${group} /home/meetingplatform/meeting-platform/docker-entrypoint.sh
RUN chmod 550 /usr/share/fonts/simsun.ttc && chown ${user}:${group} /usr/share/fonts/simsun.ttc
RUN mkdir -p /home/meetingplatform/meeting-platform/deploy/static &&  \
    chmod -R 750 /home/meetingplatform/meeting-platform/deploy &&  \
    chown -R ${user}:${group} /home/meetingplatform/meeting-platform/deploy

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN yum remove -y gcc python3-pip procps-ng
RUN sed -i "s|PASS_MAX_DAYS[ \t]*99999|PASS_MAX_DAYS 30|" /etc/login.defs && sed -i "s|HISTSIZE=1000|HISTSIZE=0|" /etc/profile  && rm -rf /tmp/*
RUN rm -rf /usr/share/gdb && rm -rf /usr/bin/nc && rm -rf /usr/bin/ncat \
    /usr/share/licenses/glibc \
    /usr/share/locale/ar \
    /usr/share/locale/cpp \
    && rm -f /usr/lib64/python3.9/bdb.py \
    /usr/lib64/python3.9/pdb.py \
    /usr/lib64/python3.9/timeit.py \
    /usr/lib64/python3.9/trace.py \
    /usr/lib64/python3.9/tracemalloc.py \
    /usr/bin/kill


RUN echo "umask 027" >> /home/meetingplatform/.bashrc
RUN echo 'set +o history' >> /home/meetingplatform/.bashrc
RUN chmod 640 /home/meetingplatform/.bashrc && chmod 640 /home/meetingplatform/.bash_logout && chmod 640 /home/meetingplatform/.bash_profile

# 5.Run server
WORKDIR /home/meetingplatform/meeting-platform
ENV LANG=en_US.UTF-8
USER meetingplatform

ENTRYPOINT ["/home/meetingplatform/meeting-platform/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/home/meetingplatform/meeting-platform/deploy/production/uwsgi.ini"]
EXPOSE 8080
