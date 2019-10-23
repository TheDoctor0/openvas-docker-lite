#!/usr/bin/env python3
"""Automation script for OpenVAS 10."""

import subprocess
import argparse
import base64
import time
import os
from lxml import etree
from typing import Optional
from typing import Union
from typing import Dict
from typing import List
from typing import Set
from typing import IO

DEBUG: bool = False

scan_profiles: Dict[str, str] = {
    "Discovery": "8715c877-47a0-438d-98a3-27c7a6ab2196",
    "Empty": "085569ce-73ed-11df-83c3-002264764cea",
    "Full and fast": "daba56c8-73ec-11df-a475-002264764cea",
    "Full and fast ultimate": "698f691e-7489-11df-9d8c-002264764cea",
    "Full and very deep": "708f25c4-7489-11df-8094-002264764cea",
    "Full and very deep ultimate": "74db13d6-7489-11df-91b9-002264764cea",
    "Host Discovery": "2d3f051c-55ba-11e3-bf43-406186ea4fc5",
    "System Discovery": "bbca7412-a950-11e3-9109-406186ea4fc5"
}

report_formats: Dict[str, str] = {
    "Anonymous XML": "5057e5cc-b825-11e4-9d0e-28d24461215b",
    "ARF": "910200ca-dc05-11e1-954f-406186ea4fc5",
    "CPE": "5ceff8ba-1f62-11e1-ab9f-406186ea4fc5",
    "CSV Hosts": "9087b18c-626c-11e3-8892-406186ea4fc5",
    "CSV Results": "c1645568-627a-11e3-a660-406186ea4fc5",
    "ITG": "77bd6c4a-1f62-11e1-abf0-406186ea4fc5",
    "LaTeX": "a684c02c-b531-11e1-bdc2-406186ea4fc5",
    "NBE": "9ca6fe72-1f62-11e1-9e7c-406186ea4fc5",
    "PDF": "c402cc3e-b531-11e1-9163-406186ea4fc5",
    "Topology SVG": "9e5e5deb-879e-4ecc-8be6-a71cd0875cdd",
    "TXT": "a3810a62-1f62-11e1-9219-406186ea4fc5",
    "Verinice ISM": "c15ad349-bd8d-457a-880a-c7056532ee15",
    "Verinice ITG": "50c9950a-f326-11e4-800c-28d24461215b",
    "XML": "a994b278-1f62-11e1-96ac-406186ea4fc5"
}

alive_tests: Set[str] = {
    "Scan Config Default",
    "ICMP, TCP-ACK Service & ARP Ping",
    "TCP-ACK Service & ARP Ping",
    "ICMP & ARP Ping",
    "ICMP & TCP-ACK Service Ping",
    "ARP Ping",
    "TCP-ACK Service Ping",
    "TCP-SYN Service Ping",
    "ICMP Ping",
    "Consider Alive",
}


def save_report(path: str, raw_report: str, output_format: str = None) -> None:
    """Save OpenVAS report to specified file. Decode from Base64 if not XML."""
    if output_format == 'a994b278-1f62-11e1-96ac-406186ea4fc5':
        report: str = raw_report
    else:
        report: str = base64.b64decode(raw_report).decode('utf-8')

    file: IO[str] = open(path, 'w')
    file.write(report)
    file.close()


def perform_cleanup() -> None:
    """Remove all existing tasks and targets."""
    existing_tasks: List = execute_command("<get_tasks/>", "//get_tasks_response/task")

    for task in existing_tasks:
        execute_command(r"<delete_task task_id=\"{}\" ultimate=\"true\"/>".format(task.get("id")))

    existing_targets: List = execute_command("<get_targets/>", "//get_targets_response/target")

    for target in existing_targets:
        execute_command(r"<delete_target target_id=\"{}\" ultimate=\"true\"/>".format(target.get("id")))


def execute_command(command: str, xpath: Optional[str] = None) -> Union[str, float, bool, List]:
    """Execute gvmd command and return its output (optionally xpath can be used to get nested XML element)."""
    global DEBUG

    command: str = "su - service -c \"gvm-cli --gmp-username admin --gmp-password admin " \
                   "socket --xml \'{}\'\"".format(command)

    if DEBUG:
        print("[DEBUG] Command: {}".format(command))

    response: str = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True).decode().strip()

    if DEBUG:
        print("[DEBUG] Response: {}".format(response))

    return etree.XML(response).xpath(xpath) if xpath else response


def make_scan(scan: Dict[str, str]) -> None:
    """Make automated OpenVAS scan and save generated report."""
    perform_cleanup()
    print("Performed initial cleanup.")

    command: str = r"<create_target><name>scan</name><hosts>{}</hosts>".format(scan['target']) + \
                   r"<exclude_hosts>{}</exclude_hosts>".format(scan['exclude']) + \
                   r"<alive_tests>{}</alive_tests></create_target>".format(scan['tests'])
    target_id: str = execute_command(command, "string(//create_target_response/@id)")
    print("Created target with id: {}.".format(target_id))

    scanner_id: str = execute_command(
        r"<get_scanners filter=\"Scanner\"/>",
        "string(//get_scanners_response/scanner/@id)"
    )
    print("Found scanner with id: {}.".format(scanner_id))

    command = r"<create_task><name>Scan</name>" + \
              r"<target id=\"{}\"></target>".format(target_id) + \
              r"<scanner id=\"{}\"></scanner>".format(scanner_id) + \
              r"<config id=\"{}\"></config></create_task>".format(scan['profile'])
    task_id: str = execute_command(command, "string(//create_task_response/@id)")
    print("Created task with id: {}.".format(task_id))

    execute_command(r"<start_task task_id=\"{}\"/>".format(task_id))
    print("Started task.")

    print("Waiting for task to finish...")
    status: Optional[str] = None
    task: Optional[str] = None

    while status != "Done":
        try:
            time.sleep(5)

            task = execute_command(r"<get_tasks task_id=\"{}\"/>".format(task_id))
            status = etree.XML(task).xpath("string(//status/text())")
            progress: int = int(etree.XML(task).xpath("string(//progress/text())"))

            os.system("clear")

            if progress > 0:
                print("Task status: {} {}%".format(status, progress))
            else:
                print("Task status: Complete")
        except subprocess.CalledProcessError as exception:
            print("ERROR: ", exception.output)

    report_id: str = etree.XML(task).xpath("string(//report/@id)")
    report: str = execute_command(
        r"<get_reports report_id=\"{}\" format_id=\"{}\" ".format(report_id, scan['format']) +
        r"filter=\"levels=hmlg\" details=\"1\" notes_details=\"1\" result_tags=\"1\" ignore_pagination=\"1\"/>",
        "string(//get_reports_response/report/text())"
    )
    print("Generated report.")

    save_report(scan['output'], report, scan['format'])
    print("Saved report to {}.".format(scan['output']))

    perform_cleanup()
    print("Done!")


def start_scan(args: argparse.Namespace) -> None:
    """Override default settings and start scan."""
    global DEBUG

    if args.debug:
        DEBUG = True

    subprocess.check_call(
        ["sed -i 's/max_hosts.*/max_hosts = " + str(args.hosts) + "/' /usr/local/etc/openvas/openvas.conf"],
        shell=True,
        stdout=subprocess.DEVNULL
    )
    subprocess.check_call(
        ["sed -i 's/max_checks.*/max_checks = " + str(args.checks) + "/' /usr/local/etc/openvas/openvas.conf"],
        shell=True,
        stdout=subprocess.DEVNULL
    )

    if args.update is True:
        print("Starting and updating OpenVAS...")
        subprocess.check_call(["update-scanner"], shell=True, stdout=subprocess.DEVNULL)
    else:
        print("Starting OpenVAS...")
        subprocess.check_call(["start-scanner"], shell=True, stdout=subprocess.DEVNULL)

    print("Starting scan with settings:")
    print("* Target: {}".format(args.target))
    print("* Excluded hosts: {}".format(args.exclude))
    print("* Scan profile: {}".format(args.profile))
    print("* Alive tests: {}".format(args.tests))
    print("* Max hosts: {}".format(args.hosts))
    print("* Max checks: {}".format(args.checks))
    print("* Report format: {}".format(args.format))
    print("* Output file: {}\n".format(args.output))

    make_scan({'target': args.target, 'exclude': args.exclude, 'tests': args.tests.replace("&", "&amp;"),
               'profile': scan_profiles[args.profile], 'format': report_formats[args.format],
               'output': "/reports/" + args.output})


def report_format(arg: Optional[str]) -> str:
    """Check if report format value is valid."""
    if arg not in report_formats:
        raise argparse.ArgumentTypeError("Specified report format is invalid!")

    return arg


def scan_profile(arg: Optional[str]) -> str:
    """Check if scan profile value is valid."""
    if arg not in scan_profiles:
        raise argparse.ArgumentTypeError("Specified scan profile is invalid!")

    return arg


def alive_test(arg: Optional[str]) -> str:
    """Check if alive test value is valid."""
    if arg not in alive_tests:
        raise argparse.ArgumentTypeError("Specified alive tests are invalid!")

    return arg


def max_hosts(arg: Optional[str]) -> int:
    """Check if max hosts value is valid."""
    try:
        value = int(arg)

        if value <= 0:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError("Specified maximum number of simultaneous tested hosts is invalid!")

    return value


def max_checks(arg: Optional[str]) -> int:
    """Check if max checks value is valid."""
    try:
        value = int(arg)

        if value <= 0:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError("Specified maximum number of simultaneous checks against hosts is invalid!")

    return value


def parse_arguments():
    """Add and parse script arguments."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='Run OpenVAS scan with specified target and save report.')
    parser.add_argument('target', help='scan target')
    parser.add_argument('-o', '--output', help='output file (default: openvas.report)',
                        default="openvas.report", required=False)
    parser.add_argument('-f', '--format', help='format for report (default: ARF)',
                        default="ARF", type=report_format, required=False)
    parser.add_argument('-p', '--profile', help='scan profile (default: Full and fast)',
                        default="Full and fast", type=scan_profile, required=False)
    parser.add_argument('-t', '--tests', help='alive tests (default: ICMP, TCP-ACK Service & ARP Ping)',
                        default="ICMP, TCP-ACK Service & ARP Ping", type=alive_test, required=False)
    parser.add_argument('-e', '--exclude', help='hosts excluded from scan target (Default: "")',
                        default="", required=False)
    parser.add_argument('-m', '--hosts', help='maximum number of simultaneous tested hosts (Default: 3)',
                        type=max_hosts, default=3, required=False)
    parser.add_argument('-c', '--checks', help='maximum number of simultaneous checks against each host (Default: 10)',
                        type=max_checks, default=10, required=False)
    parser.add_argument('--update', help='synchronize feeds before scanning',
                        nargs='?', const=True, default=False, required=False)
    parser.add_argument('--debug', help='enable command responses printing',
                        nargs='?', const=True, default=False, required=False)

    return parser.parse_args()


if __name__ == '__main__':
    arguments: argparse.Namespace = parse_arguments()

    start_scan(arguments)
