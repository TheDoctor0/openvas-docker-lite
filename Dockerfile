FROM debian:buster

ENV GVM_LIBS_VERSION='11.0.0' \
    GVMD_VERSION='9.0.0' \
    OPENVAS_VERSION='7.0.0' \
    OPENVAS_SMB_VERSION='1.0.5' \
    SRC_PATH='/src' \
    DEBIAN_FRONTEND=noninteractive \
    TERM=dumb

# Install dependencies
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
        gnutls-bin \
    -yq && \
    apt-get install texlive-latex-extra --no-install-recommends -yq && \
    apt-get install texlive-fonts-recommended -yq && \
    rm -rf /var/lib/apt/lists/*

# Install python libraries
RUN pip3 install lxml && \
    pip3 install gvm-tools && \
    pip3 install paramiko && \
    pip3 install defusedxml && \
    pip3 install ospd && \
    pip3 install ospd-openvas

# Download and extract sources
RUN mkdir ${SRC_PATH} -p && \
    cd ${SRC_PATH} && \
    curl -o gvm-libs.tar.gz -sL https://github.com/greenbone/gvm-libs/archive/v${GVM_LIBS_VERSION}.tar.gz && \
    curl -o openvas.tar.gz -sL https://github.com/greenbone/openvas/archive/v${OPENVAS_VERSION}.tar.gz && \
    curl -o gvmd.tar.gz -sL https://github.com/greenbone/gvmd/archive/v${GVMD_VERSION}.tar.gz && \
    curl -o openvas-smb.tar.gz -sL https://github.com/greenbone/openvas-smb/archive/v${OPENVAS_SMB_VERSION}.tar.gz && \
    find . -name \*.gz -exec tar zxvfp {} \;

# Build Greenbone Vulnerability Manager Libs
RUN cd ${SRC_PATH}/gvm-libs-* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/gvm-libs-*

# Build OpenVAS SMB module
RUN cd ${SRC_PATH}/openvas-smb-* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/openvas-smb-*

# Build OpenVAS Scanner
RUN cd ${SRC_PATH}/openvas-* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/openvas-*

# Override redis configuration and greenbone sync script
COPY configs/redis.conf /etc/redis/redis.conf
COPY scripts/greenbone-nvt-sync /usr/local/bin/greenbone-nvt-sync

# Add dummy user
RUN adduser service --gecos "service,service,service,service" --disabled-password && \
    echo "service:service" | sudo chpasswd

# Get data from community feed
RUN redis-server /etc/redis/redis.conf && \
    chmod +x /usr/local/bin/greenbone-nvt-sync && \
    greenbone-nvt-sync

# Build Greenbone Vulnerability Manager
RUN cd ${SRC_PATH}/gvmd-* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    rm -rf ${SRC_PATH}/gvmd-*

# Update kernel modules and sync scap/cert data
RUN export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:'/usr/local/lib' && \
    ldconfig && \
    greenbone-scapdata-sync && \
    greenbone-certdata-sync

# Install Impacket
RUN git clone https://github.com/SecureAuthCorp/impacket.git && \
    cd impacket/ && \
    pip install . && \
    cd ../ && \
    rm -rf impacket

# Copy scripts and configuration
COPY scripts/start /start
COPY scripts/update /update
COPY scripts/create /create
COPY scripts/scan.py scan.py
COPY configs/openvas.conf /usr/local/etc/openvas/openvas.conf

# Create directories, set permissions and change configuration
RUN mkdir reports && \
    chmod 777 reports && \
    chmod +x /start && \
    chmod +x /update && \
    chmod +x /create && \
    chmod +x scan.py && \
    echo "net.core.somaxconn = 1024"  >> /etc/sysctl.conf && \
    echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf

# Create Postgres database and user
RUN /etc/init.d/postgresql start && \
    sudo -u postgres createuser -DRS root && \
    sudo -u postgres createdb -O root gvmd && \
    sudo -u postgres psql gvmd -c 'create role dba with superuser noinherit;' && \
    sudo -u postgres psql gvmd -c 'grant dba to root;' && \
    sudo -u postgres psql gvmd -c 'create extension "uuid-ossp";'

# Create user, scanner and sync database
RUN bash /create && rm -f /create
