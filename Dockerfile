FROM thedoctor0/openvas-docker-lite

FROM ubuntu:18.04

# Copy existing feeds data for faster synchronization.
COPY --from=0 /var/lib/openvas /var/lib/openvas

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install software-properties-common --no-install-recommends -yq && \
    add-apt-repository ppa:mrazavi/openvas -y && \
    apt-get clean && \
    apt-get update && \
    apt-get install alien \
        bsdtar \
        bzip2 \
        curl \
        dirb \
        dnsutils \
        git \
        libopenvas9-dev \
        libsasl2-modules \
        net-tools \
        nikto \
        nmap \
        nsis \
        openssh-client \
        openvas9-scanner \
        openvas9-cli \
        openvas9-manager \
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

# Fix for error: 'Directory renamed before its status could be extracted'.
RUN export tar='bsdtar'

RUN wget -q https://github.com/Arachni/arachni/releases/download/v1.5.1/arachni-1.5.1-0.5.12-linux-x86_64.tar.gz && \
    tar -zxf arachni-1.5.1-0.5.12-linux-x86_64.tar.gz && \
    mv arachni-1.5.1-0.5.12 /opt/arachni && \
    ln -s /opt/arachni/bin/* /usr/local/bin/ && \
    rm -rf arachni*

COPY scripts/start /start
COPY scripts/update /update
COPY scripts/scan.py scan.py
COPY configs/redis.conf /etc/redis/redis.conf
COPY configs/openvassd.conf /etc/openvas/openvassd.conf

RUN mkdir -p /var/run/redis && \
    chmod +x /start && \
    chmod +x /update && \
    chmod +x scan.py && \
    sed -i 's/DAEMON_ARGS=""/DAEMON_ARGS="-a 0.0.0.0"/' /etc/init.d/openvas-manager && \
    bash /update && \
    service openvas-scanner stop && \
    service openvas-manager stop && \
    service redis-server stop