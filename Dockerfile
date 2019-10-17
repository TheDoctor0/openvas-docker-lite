FROM debian:buster

ENV GVM_LIBS_VERSION '11.0.0'
ENV GVMD_VERSION '9.0.0'
ENV OPENVAS_VERSION '7.0.0'
ENV OPENVAS_SMB_VERSION '1.0.5'

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM dumb

RUN apt-get update && \
    apt-get install \
        postgresql \
        postgresql-contrib \
        postgresql-server-dev-all \
        python-setuptools \
        curl \
        unzip \
        git \
        python3-pip \
        python3 \
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
    pip3 install lxml && \
    rm -rf /var/lib/apt/lists/*

# Build Greenbone Vulnerability Manager Libs
RUN curl -sL https://github.com/greenbone/gvm-libs/archive/v${GVM_LIBS_VERSION}.zip -o gvm-libs.zip && \
    unzip -o gvm-libs.zip -d /tmp && \
    mkdir -p /tmp/gvm-libs-${GVM_LIBS_VERSION}/build && \
    cd /tmp/gvm-libs-${GVM_LIBS_VERSION}/build && \
    cmake .. && \
    make && \
    make install && \
    rm -f /gvm-libs.zip && \
    rm -rf /tmp/gvm-libs-${GVM_LIBS_VERSION}

RUN export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:'/usr/local/lib' && \
    ldconfig

# Build OpenVAS SMB
RUN curl -sL https://github.com/greenbone/openvas-smb/archive/v${OPENVAS_SMB_VERSION}.zip -o openvas-smb.zip && \
    unzip -o openvas-smb.zip -d /tmp && \
    mkdir mkdir -p /tmp/openvas-smb-${OPENVAS_SMB_VERSION}/build && \
    cd /tmp/openvas-smb-${OPENVAS_SMB_VERSION}/build && \
    cmake .. && \
    make && \
    make install && \
    rm -f /openvas-smb.zip && \
    rm -rf /tmp/openvas-smb-${OPENVAS_SMB_VERSION}

# Build OpenVAS Scanner
RUN curl -sL https://github.com/greenbone/openvas/archive/v${OPENVAS_VERSION}.zip -o openvas.zip && \
    unzip -o openvas.zip -d /tmp && \
    mkdir mkdir -p /tmp/openvas-${OPENVAS_VERSION}/build && \
    cd /tmp/openvas-${OPENVAS_VERSION}/build && \
    cmake .. && \
    make && \
    make install && \
    cp -f /tmp/openvas-${OPENVAS_VERSION}/config/redis-openvas.conf /etc/redis/redis.conf && \
    rm -f /openvas.zip && \
    rm -rf /tmp/openvas-${OPENVAS_VERSION}

# Build Greenbone Vulnerability Manager
RUN curl -sL https://github.com/greenbone/gvmd/archive/v${GVMD_VERSION}.zip -o gvmd.zip && \
    unzip -o gvmd.zip -d /tmp && \
    mkdir mkdir -p /tmp/gvmd-${GVMD_VERSION}/build && \
    cd /tmp/gvmd-${GVMD_VERSION}/build && \
    cmake .. && \
    make && \
    make install && \
    rm -f /gvmd.zip && \
    rm -rf /tmp/gvmd-${GVMD_VERSION}

# Install Impacket
RUN git clone https://github.com/SecureAuthCorp/impacket.git && \
    cd impacket/ && \
    python setup.py install && \
    rm -rf /impacket

# Copy scripts and configuration
COPY scripts/start /start
COPY scripts/update /update
COPY scripts/create /create
COPY scripts/scan.py scan.py
COPY configs/greenbone-nvt-sync /usr/local/bin/greenbone-nvt-sync
COPY configs/openvassd.conf /etc/openvas/openvassd.conf
COPY configs/redis.conf /etc/redis/redis.conf

# Create directories, set permissions and change configuration
RUN mkdir reports && \
    chmod 777 reports && \
    chmod +x /start && \
    chmod +x /update && \
    chmod +x /create && \
    chmod +x scan.py && \
    chmod +x /usr/local/bin/greenbone-nvt-sync && \
    echo "net.core.somaxconn = 1024"  >> /etc/sysctl.conf && \
    echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf

# Create Postgres database and user
RUN /etc/init.d/postgresql start && \
    sudo -u postgres createuser -DRS root && \
    sudo -u postgres createdb -O root gvmd && \
    sudo -u postgres psql gvmd -c 'create role dba with superuser noinherit;' && \
    sudo -u postgres psql gvmd -c 'grant dba to root;' && \
    sudo -u postgres psql gvmd -c 'create extension "uuid-ossp";'

# Create GVMD user
RUN bash /create && rm -f /create

# Update OpenVAS
RUN bash /update
