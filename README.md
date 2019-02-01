# OpenVAS Docker Lite

A Docker container with OpenVAS 9 based on the Ubuntu 18.04 image.

It also contains custom automation script that allow to scan selected targets and generate report with one command.

It is lite version and it does not contain Greenbone Security Assistant - web app for managing OpenVAS.

## Usage

### 1. Pull image:

```
docker pull thedoctor0/openvas-docker-lite
```

### 2. Scan and save report:

```
docker run --rm -v $(pwd):/openvas/results/:rw thedoctor0/openvas-docker-lite python scan.py <target>
```

This will startup the container and update the NVTs cache - it can take some time, so be patient.
After that, the scan script will run and the progress will be displayed in console.

It is possible to specify output file with **-o** or **--output** argument.

By default report is save as *openvas.report*.

### Output

It is possible to specify output filename with **-o** or **--output** argument.

By default report is save as *openvas.report*.

### Formats

1. Anonymous XML
2. ARF
3. CPE
4. CSV Hosts
5. CSV Results
6. HTML
7. ITG
8. LaTeX
9. NBE
10. PDF
11. Topology SVG
12. TXT
13. Verinice ISM
14. Verinice ITG
15. XML

You can select what report format will be used with **-f** or **--format** argument with one of available profiles as value.

By default *PDF* format is used to generate report.

### Profiles

1. Discovery
2. Empty
3. Full and fast
4. Full and fast ultimate
5. Full and very deep
6. Full and very deep ultimate
7. Host Discovery
8. System Discovery

You can select scan profile by adding **-p** or **--profile** argument with one of available profiles as value.

By default *Full and fast* profile is used.

### Update

You can also add **--update** argument to force update.

This will synchronize OpenVAS feeds before making the scan.

Feeds update is slow, so it will take significantly more time.

## Credits
- Mike Splain for creating the original OpenVAS docker image
- ICTU team for creating the base automation script for OpenVAS
