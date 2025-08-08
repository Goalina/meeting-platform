FROM openeuler/openeuler:22.03

ARG user=meetingplatform
ARG group=meetingplatform
ARG uid=1000
ARG gid=1000


# 1.install
RUN yum install -y shadow wget git openssl openssl-devel tzdata python3-devel mariadb-devel python3-pip  \
    libXext libjpeg xorg-x11-fonts-75dpi xorg-x11-fonts-Type1 gcc ffmpeg
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -d /home/meetingplatform/ -s /sbin/nologin -m ${user}

# 2.copy
COPY --chown=${user}:${group} . /home/meetingplatform/meeting-platform/
RUN mv /home/meetingplatform/meeting-platform/deploy/fonts/simsun.ttc /usr/share/fonts/simsun.ttc
RUN rm -rf /home/meetingplatform/meeting-platform/Dockerfile

# 3.install
RUN pip3 install -r /home/meetingplatform/meeting-platform/requirements.txt && rm -rf /home/meetingplatform/meeting-platform/requirements.txt
RUN wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.centos8.x86_64.rpm && \
    rpm -i wkhtmltox-0.12.6-1.centos8.x86_64.rpm && \
    rm -f wkhtmltox-0.12.6-1.centos8.x86_64.rpm

# 4.clean
RUN chmod -R 550 /home/meetingplatform/meeting-platform/
RUN chmod 550 /home/meetingplatform/meeting-platform/manage.py
RUN chmod 550 /home/meetingplatform/meeting-platform/docker-entrypoint.sh
RUN chmod 550 /usr/share/fonts/simsun.ttc
RUN chmod -R 750 /home/meetingplatform/meeting-platform/deploy
RUN rm -rf /home/meetingplatform/meeting-platform/.git
RUN rm -rf /home/meetingplatform/meeting-platform/.gitignore
RUN rm -rf /home/meetingplatform/meeting-platform/deploy/config

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN yum remove -y gcc python3-pip procps-ng gdb-gdbserver findutils passwd mirror cpp
RUN sed -i "s|PASS_MAX_DAYS[ \t]*99999|PASS_MAX_DAYS 30|" /etc/login.defs && rm -rf /tmp/*
RUN rm -rf /usr/share/gdb  \
    && rm -rf /usr/bin/nc  \
    && rm -rf /usr/bin/ncat \
    && rm -rf /usr/share/locale/ar \
    && rm -rf /usr/share/locale/cpp \
    && rm -rf /usr/lib64/python3.9/bdb.py \
    && rm -rf /usr/lib64/python3.9/pdb.py \
    && rm -rf /usr/lib64/python3.9/timeit.py \
    && rm -rf /usr/lib64/python3.9/trace.py \
    && rm -rf /usr/lib64/python3.9/tracemalloc.py \
    && rm -rf /usr/bin/kill \
    && echo "umask 0027" >> /etc/bashrc \
    && echo "set +o history" >> /etc/bashrc \
    && sed -i "s|HISTSIZE=1000|HISTSIZE=0|" /etc/profile \
    && yum clean all \
    && usermod -s /sbin/nologin sync \
    && usermod -s /sbin/nologin shutdown \
    && usermod -s /sbin/nologin halt \
    && echo "export TMOUT=1800 readonly TMOUT" >> /etc/profile \
    && rm -rf /usr/bin/gdb* \
    && rm -rf /usr/share/gdb \
    && rm -rf /usr/share/gcc* \
    && rm -rf /usr/share/licenses/glib2/COPYING \
    && rm -rf /usr/share/man/man1/ex.1.gz \
    && rm -rf /usr/share/man/man1/rview.1.gz \
    && rm -rf /usr/share/man/man1/view.1.gz

RUN echo "umask 027" >> /home/meetingplatform/.bashrc
RUN echo 'set +o history' >> /home/meetingplatform/.bashrc
RUN chmod 640 /home/meetingplatform/.bashrc && chmod 640 /home/meetingplatform/.bash_logout && chmod 640 /home/meetingplatform/.bash_profile
RUN chown ${user}:${group} /home/meetingplatform/meeting-platform/deploy/production/gunicorn.conf.py

# 5.Run server
WORKDIR /home/meetingplatform/meeting-platform
ENV LANG=en_US.UTF-8
USER ${uid}:${gid}

ENTRYPOINT ["/home/meetingplatform/meeting-platform/docker-entrypoint.sh"]
CMD ["gunicorn", "meeting_platform.wsgi:application"]
EXPOSE 8080