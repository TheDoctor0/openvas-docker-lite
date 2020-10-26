# OpenVAS Docker Lite [![License](https://img.shields.io/github/license/TheDoctor0/openvas-docker-lite)](https://github.com/TheDoctor0/openvas-docker-lite/blob/master/LICENSE) [![Build Status](https://travis-ci.org/TheDoctor0/openvas-docker-lite.png)](https://travis-ci.org/TheDoctor0/openvas-docker-lite) [![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/TheDoctor0/openvas-docker-lite/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/TheDoctor0/openvas-docker-lite/?branch=master) [![Docker Pulls](https://img.shields.io/docker/pulls/thedoctor0/openvas-docker-lite.svg)](https://hub.docker.com/r/thedoctor0/openvas-docker-lite)

Docker container with automated OpenVAS 20.8.0 (GVMD 20.8.0) based on the Debian 10 image.

It contains custom automation script that allows to scan selected targets and generate a report with one command.

This is a lite version and it does not include Greenbone Security Assistant - web app for managing OpenVAS.

Previous version with OpenVAS 10 is available [here](https://github.com/TheDoctor0/openvas-docker-lite/tree/10).

Oldest container based on Ubuntu with OpenVAS 9 is available [here](https://github.com/TheDoctor0/openvas-docker-lite/tree/9).

## Usage

### 1. Pull image:

```
docker pull thedoctor0/openvas-docker-lite
```

### 2. Scan and save report:

```
docker run --rm -v $(pwd):/reports/:rw thedoctor0/openvas-docker-lite python3 -u scan.py <target> [options]
```

This will start up the container and update the NVTs cache - it can take some time, so be patient.

After that, the scan script will run and the progress will be displayed in the console.


#### Target

Target can be a single IP or CIDR or a comma separated list of IP addresses or CIDRs.

#### Output

It is possible to specify output filename with **-o** or **--output** argument.

By default report is saved as *openvas.report*.

#### Formats

1. Anonymous XML
2. CSV Results
3. ITG
4. PDF
5. TXT
6. XML

You can select what report format will be used with **-f** or **--format** argument with one of the available profiles.

By default *XML* format is used to generate the report.

#### Profiles

1. Discovery
2. Empty
3. Full and fast
4. Full and fast ultimate
5. Full and very deep
6. Full and very deep ultimate
7. Host Discovery
8. System Discovery

You can select scan profile by adding **-p** or **--profile** argument with one of the available profiles.

By default *Full and fast* profile is used.

#### Alive Tests

1. Scan Config Default
2. ICMP, TCP-ACK Service & ARP Ping
3. TCP-ACK Service & ARP Ping
4. ICMP & ARP Ping
5. ICMP & TCP-ACK Service Ping
6. ARP Ping
7. TCP-ACK Service Ping
8. TCP-SYN Service Ping
9. ICMP Ping
10. Consider Alive

You can select scan alive tests by adding **-t** or **--tests** argument with one of the available tests.

By default *ICMP, TCP-ACK Service & ARP Ping* alive tests are used.

#### Port Lists

1. All IANA Assigned TCP
2. All IANA Assigned TCP and UDP
3. All TCP and Nmap top 100 UDP

You can select scan alive tests by adding **-P** or **--ports** argument with one of the available tests.

By default *All TCP and Nmap top 100 UDP* port list is used.
Note that using *All TCP and Nmap top 100 UDP* will significantly increase the scan time.

#### Exclude Hosts

You can exclude hosts from specified target by adding **-e** or **--exclude** argument with list of IPs.

By default list of excluded hosts is empty.

#### Max Hosts

It is possible to override *max_hosts* variable in OpenVAS config which specify maximum number of simultaneous hosts tested.
Just add **-m** or **--max** argument with wanted numeric value.

By default **10** is used as *max_hosts* variable value.

#### Max Checks

It is possible to override *max_checks* variable in OpenVAS config which specify maximum number of simultaneous checks against each host tested.
Just add **-c** or **--checks** argument with wanted numeric value.

By default **3** is used as *max_checks* variable value.

#### Debug

You can enable printing command responses by adding **--debug** argument.

#### Update

You can also add **--update** argument to force update.

This will synchronize OpenVAS feeds before making the scan.

Feeds update is quite slow, so it will take significantly more time.

## Credits
- Mike Splain for creating the original OpenVAS docker image
- ICTU team for creating the base automation script for OpenVAS
- Eugene Merlinsky for adjusting the project to work with Greenbone 20.8.0
