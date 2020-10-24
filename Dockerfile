FROM thedoctor0/openvas-docker-lite
FROM debian:buster

ENV GVM_LIBS_VERSION='v20.8.0' \
    GVMD_VERSION='v20.8.0' \
    OPENVAS_VERSION='v20.8.0' \
    OPENVAS_SMB_VERSION='v1.0.5' \
    OSPD_OPENVAS_VERSION='v20.8.0' \
    OSPD_VERSION='v20.8.1' \
    SRC_PATH='/src' \
    DEBIAN_FRONTEND=noninteractive \
    TERM=dumb

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils && \
    apt-get install \
        postgresql \
        postgresql-contrib \
        postgresql-server-dev-all \
        python-setuptools \
        git \
        curl \
        doxygen \
        python3 \
        python3-pip \
        python3-dev \
        rsync \
        nmap \
        snmp \
        sudo \
        redis-server \
        cmake \
        pkg-config \
        libradcli-dev \
        libglib2.0-dev \
        libgpgme-dev \
        libgpgme11-dev \
        libgnutls28-dev \
        libssh-gcrypt-dev \
        libldap2-dev \
        libhiredis-dev \
        libpcap-dev \
        libpq-dev \
        libksba-dev \
        libsnmp-dev \
        libical-dev \
        libgcrypt20-dev \
        libpopt-dev \
        gcc-mingw-w64 \
        gcc \
        glib-2.0 \
        perl-base \
        uuid-dev \
        heimdal-dev \
        bison \
        xsltproc \
        xmlstarlet \
        gnutls-bin \
        xmltoman \
        xml-twig-tools \
        libxml2-dev \
    -yq && \
    apt-get install texlive-latex-extra --no-install-recommends -yq && \
    apt-get install texlive-fonts-recommended -yq && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install \
        lxml \
        gvm-tools \
        paramiko \
        defusedxml \
        redis \
        psutil

RUN mkdir ${SRC_PATH} -p && \
    cd ${SRC_PATH} && \
    curl -o gvm-libs.tar.gz -sL https://github.com/greenbone/gvm-libs/archive/${GVM_LIBS_VERSION}.tar.gz && \
    curl -o openvas.tar.gz -sL https://github.com/greenbone/openvas/archive/${OPENVAS_VERSION}.tar.gz && \
    curl -o gvmd.tar.gz -sL https://github.com/greenbone/gvmd/archive/${GVMD_VERSION}.tar.gz && \
    curl -o openvas-smb.tar.gz -sL https://github.com/greenbone/openvas-smb/archive/${OPENVAS_SMB_VERSION}.tar.gz && \
    curl -o ospd-openvas.tar.gz -sL https://github.com/greenbone/ospd-openvas/archive/${OSPD_OPENVAS_VERSION}.tar.gz && \
    curl -o ospd.tar.gz -sL https://github.com/greenbone/ospd/archive/${OSPD_VERSION}.tar.gz && \
    find . -name \*.gz -exec tar zxvfp {} \;

RUN cd ${SRC_PATH}/ospd-openvas* && \
    pip3 install . && \
    rm -rf ${SRC_PATH}/ospd-openvas*

RUN cd ${SRC_PATH}/ospd* && \
    pip3 install . && \
    rm -rf ${SRC_PATH}/ospd*

RUN cd ${SRC_PATH}/gvm-libs* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/gvm-libs*

RUN cd ${SRC_PATH}/openvas-smb* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/openvas-smb*

RUN cd ${SRC_PATH}/openvas* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/openvas*

COPY --from=0 /usr/local/var/lib/openvas/plugins /usr/local/var/lib/openvas/plugins
COPY configs/redis.conf /etc/redis/redis.conf
COPY scripts/sync-nvts /usr/local/bin/sync-nvts
COPY scripts/greenbone-nvt-sync /usr/local/bin/greenbone-nvt-sync

RUN adduser service --gecos "service,service,service,service" --disabled-password && \
    echo "service:service" | sudo chpasswd

RUN redis-server /etc/redis/redis.conf && \
    chmod +x /usr/local/bin/greenbone-nvt-sync && \
    chmod +x /usr/local/bin/sync-nvts && \
    ldconfig && \
    sleep 10 && \
    sync-nvts

RUN cd ${SRC_PATH}/gvmd-* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/gvmd-*

COPY --from=0 /usr/local/var/lib/gvm/scap-data /usr/local/var/lib/gvm/scap-data
COPY --from=0 /usr/local/var/lib/gvm/cert-data /usr/local/var/lib/gvm/cert-data
COPY scripts/sync-scap /usr/local/bin/sync-scap
COPY scripts/sync-certs /usr/local/bin/sync-certs
COPY scripts/sync-data /usr/local/bin/sync-data
COPY scripts/greenbone-certdata-sync /usr/local/sbin/greenbone-certdata-sync
COPY scripts/greenbone-scapdata-sync /usr/local/sbin/greenbone-scapdata-sync
COPY scripts/greenbone-feed-sync /usr/local/sbin/greenbone-feed-sync

RUN chmod +x /usr/local/sbin/greenbone-certdata-sync && \
    chmod +x /usr/local/sbin/greenbone-scapdata-sync && \
    chmod +x /usr/local/sbin/greenbone-feed-sync && \
    chmod +x /usr/local/bin/sync-scap && \
    chmod +x /usr/local/bin/sync-certs && \
    chmod +x /usr/local/bin/sync-data && \
    ldconfig && \
    sleep 10 && \
    sync-data && \
    sleep 10 && \
    sync-certs && \
    sleep 10 && \
    sync-scap

RUN git clone https://github.com/SecureAuthCorp/impacket.git && \
    cd impacket/ && \
    pip3 install . && \
    cd ../ && \
    rm -rf impacket

COPY scripts/start-services /usr/local/bin/start-services
COPY scripts/start-openvas /usr/local/bin/start-openvas
COPY scripts/start-scanner /usr/local/bin/start-scanner
COPY scripts/update-scanner /usr/local/bin/update-scanner
COPY scripts/configure-scanner /configure-scanner
COPY scripts/scan.py /scan.py
COPY configs/openvas.conf /usr/local/etc/openvas/openvas.conf

RUN mkdir reports && \
    chmod 777 reports && \
    mkdir /var/run/ospd && \
    chmod 777 /var/run/ospd && \
    chmod 777 /usr/local/var/lib/gvm/gvmd/report_formats && \
    chmod +x /usr/local/bin/start-services && \
    chmod +x /usr/local/bin/start-openvas && \
    chmod +x /usr/local/bin/start-scanner && \
    chmod +x /usr/local/bin/update-scanner && \
    chmod +x /configure-scanner && \
    chmod +x /scan.py && \
    echo "net.core.somaxconn = 1024"  >> /etc/sysctl.conf && \
    echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf


RUN bash /configure-scanner && \
    rm -f /configure-scanner && \
    rm -rf /usr/local/var/log/gvm/*.log && \
    rm -rf  /usr/local/var/run/feed-update.lock && \
    /etc/init.d/postgresql stop && \
    /etc/init.d/redis-server stop
