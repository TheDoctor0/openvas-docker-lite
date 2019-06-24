FROM thedoctor0/openvas-docker-lite

FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM dumb

# Install general packages
RUN apt-get update && \
    apt-get install software-properties-common --no-install-recommends -yq && \
    apt-get clean && \
    apt-get update && \
    apt-get install alien \
        bsdtar \
        bzip2 \
        curl \
        dirb \
        dnsutils \
        git \
        libsasl2-modules \
        net-tools \
        nikto \
        nmap \
        nsis \
        openssh-client \
        python-pip \
        rpm \
        rsync \
        redis \
        redis-server \
        smbclient \
        socat \
        sqlite3 \
        sshpass \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-latex-recommended \
        wapiti \
        wget \
        xsltproc \
    -yq && \
    pip install lxml && \
    apt-get purge software-properties-common -yq && \
    apt autoremove -yq && \
    rm -rf /var/lib/apt/lists/*
    
# Install OpenVAS components
RUN apt-get update && \
    add-apt-repository ppa:mrazavi/openvas -y && \
    apt-get clean && \
    apt-get update && \
    apt-get install libopenvas9-dev \
        openssh-client \
        openvas9-scanner \
        openvas9-cli \
        openvas9-manager \
    -yq && \
    apt autoremove -yq && \
    rm -rf /var/lib/apt/lists/*

# Fix for error: 'Directory renamed before its status could be extracted'.
RUN export tar='bsdtar'

# Install Arachni
RUN wget -q https://github.com/Arachni/arachni/releases/download/v1.5.1/arachni-1.5.1-0.5.12-linux-x86_64.tar.gz && \
    tar -zxf arachni-1.5.1-0.5.12-linux-x86_64.tar.gz && \
    mv arachni-1.5.1-0.5.12 /opt/arachni && \
    ln -s /opt/arachni/bin/* /usr/local/bin/ && \
    rm -rf arachni*

# Copy scrips and configuration
COPY scripts/start /start
COPY scripts/update /update
COPY scripts/scan.py scan.py
COPY configs/redis.conf /etc/redis/redis.conf
COPY configs/openvassd.conf /etc/openvas/openvassd.conf

# Create directories and set files permissions
RUN mkdir -p /var/run/redis && \
    mkdir reports && \
    chmod 777 reports && \
    chmod +x /start && \
    chmod +x /update && \
    chmod +x scan.py && \
    sed -i 's/DAEMON_ARGS=""/DAEMON_ARGS="-a 0.0.0.0"/' /etc/init.d/openvas-manager

# Copy existing feeds data for faster update.
COPY --from=0 /var/lib/openvas /var/lib/openvas

# Update OpenVAS
RUN bash /update && \
    service openvas-scanner stop && \
    service openvas-manager stop && \
    service redis-server stop
