OpenVAS Docker Lite
==============

A Docker container with OpenVAS 9 based on the Ubuntu 18.04 image.
It also contains custom automation script that allow to scan selected targets and generate report with one command.
It is lite version and it does not contain Greenbone Security Assistant - web app for managing OpenVAS.

Requirements
------------
Docker

Usage
-----
Pull:
```
docker pull thedoctor0/openvas-docker-lite
```

Scan:
```
docker run --rm -v $(pwd):/openvas/results/:rw thedoctor0/openvas-docker-lite /openvas/run_scan.py <target> report.html
```

This will startup the container and update the NVTs cache. It can take some time, so be patient.
After that, the scan script will run and the progress is displayed.

Update and scan:
```
docker run --rm -v $(pwd):/openvas/results/:rw thedoctor0/openvas-docker-lite /openvas/run_scan.py <target> report.html --update
```

This works the same as *Scan* command, but will synchronize OpenVAS feeds before making scan.
Feeds update is slow, so it will take significantly more time.

Credits
------
- Mike Splain for creating the original OpenVAS docker image
- ICTU team for creating automation script for OpenVAS