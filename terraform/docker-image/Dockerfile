FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV container docker

RUN apt-get update \
  && apt-get install -y --no-install-recommends systemd systemd-sysv openssh-server ca-certificates curl gnupg2 apt-transport-https python3 python3-apt netcat-openbsd \
  && echo 'root:root' | chpasswd \
  && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
  && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
  && rm -rf /var/lib/apt/lists/*

RUN cd /lib/systemd/system/sysinit.target.wants/ && ls | grep -v systemd-tmpfiles-setup.service | xargs rm -f \
  && rm -f /lib/systemd/system/sockets.target.wants/*udev* \
  && rm -f /lib/systemd/system/sockets.target.wants/*initctl* \
  && rm -f /lib/systemd/system/basic.target.wants/* \
  && rm -f /lib/systemd/system/systemd-update-utmp*

RUN systemctl enable ssh

EXPOSE 22

CMD ["/lib/systemd/systemd"]
