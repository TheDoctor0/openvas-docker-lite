FROM debian:buster

ENV GVM_LIBS_VERSION='dbef141' \
    GVMD_VERSION='90dd913' \
    OPENVAS_VERSION='0fd5aa8' \
    OPENVAS_SMB_VERSION='de43dab' \
    OSPD_OPENVAS_VERSION='d019f63' \
    OSPD_VERSION='5170464' \
    SRC_PATH='/src' \
    DEBIAN_FRONTEND=noninteractive \
    TERM=dumb

RUN apt-get update && \
    apt-get install \
        postgresql \
        postgresql-contrib \
        postgresql-server-dev-all \
        python-setuptools \
        git \
        curl \
        python3 \
        python3-pip \
        python-pip \
        python-dev \
        rsync \
        nmap \
        snmp \
        sudo \
        redis-server \
        cmake \
        pkg-config \
        libglib2.0-dev \
        libgpgme11-dev \
        libgnutls28-dev \
        libssh-gcrypt-dev \
        libldap2-dev \
        libhiredis-dev \
        libpcap-dev \
        libksba-dev \
        libsnmp-dev \
        libical-dev \
        libgcrypt20-dev \
        libpopt-dev \
        gcc-mingw-w64 \
        glib-2.0 \
        perl-base \
        uuid-dev \
        heimdal-dev \
        bison \
        xsltproc \
        xmlstarlet \
        gnutls-bin \
        xmltoman \
        doxygen \
        xml-twig-tools \
        libxml2-dev \
    -yq && \
    apt-get install texlive-latex-extra --no-install-recommends -yq && \
    apt-get install texlive-fonts-recommended -yq && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install lxml && \
    pip3 install gvm-tools && \
    pip3 install paramiko && \
    pip3 install defusedxml && \
    pip3 install redis && \
    pip3 install psutil

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

COPY configs/redis.conf /etc/redis/redis.conf
COPY scripts/sync-feeds /usr/local/bin/greenbone-nvt-sync

RUN adduser service --gecos "service,service,service,service" --disabled-password && \
    echo "service:service" | sudo chpasswd

RUN redis-server /etc/redis/redis.conf && \
    ldconfig && \
    sleep 10 && \
    greenbone-nvt-sync

RUN cd ${SRC_PATH}/gvmd-* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/gvmd-*

RUN ldconfig && \
    #Problem with long SCAP sync: https://github.com/greenbone/gvmd/issues/822
    #sleep 10 && \
    #greenbone-scapdata-sync && \
    sleep 10 && \
    greenbone-certdata-sync

RUN git clone https://github.com/SecureAuthCorp/impacket.git && \
    cd impacket/ && \
    pip install . && \
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
    /etc/init.d/postgresql stop && \
    /etc/init.d/redis-server stop
