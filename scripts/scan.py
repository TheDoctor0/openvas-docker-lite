#!/usr/bin/env python3

from typing import Optional
from typing import Union
from typing import List
from typing import Dict
from typing import Set
from lxml import etree
import subprocess
import argparse
import time
import os

debug: bool = False

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
    "HTML": "6c248850-1f62-11e1-b082-406186ea4fc5",
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


def save_report(path: str, report: str) -> None:
    """Save raw OpenVAS report to specified file."""
    file = open(path, 'w')
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
    global debug

    command: str = "su - service -c \"gvm-cli --gmp-username service --gmp-password " + \
                   "service socket --xml \'{}\'\"".format(command)

    response: str = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True).decode().strip()

    if debug:
        print("Response: {}".format(response))

    return etree.XML(response).xpath(xpath) if xpath else response


def make_scan(target: str, exclude: str, tests: str, profile: str, report_format: str, report_file: str) -> None:
    """Make automated OpenVAS scan and save generated report."""
    perform_cleanup()
    print("\nPerformed initial cleanup.")

    command: str = r"<create_target><name>scan</name><hosts>{}</hosts>".format(target) + \
                   r"<exclude_hosts>{}</exclude_hosts>".format(exclude) + \
                   r"<alive_tests>{}</alive_tests></create_target>".format(tests)
    target_id: str = execute_command(command, "//create_target_response")[0].get("id")
    print("Created target with id: {}.".format(target_id))

    command = r"<create_task><name>scan</name>" + \
              r"<target id=\"{}\"></target>".format(target_id) + \
              r"<config id=\"{}\"></config></create_task>".format(profile)
    task_id: str = execute_command(command, "//create_task_response")[0].get("id")
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
            status = etree.XML(task).xpath("//status")[0].text
            progress: int = int(etree.XML(task).xpath("//progress")[0].text)

            if progress > 0:
                print("Task status: {} {}%".format(status, progress))
            else:
                print("Task status: Complete")
        except subprocess.CalledProcessError as exc:
            print("ERROR: ", exc.output)

    report_id: str = etree.XML(task).xpath("//report")[0].get("id")
    report: str = execute_command(r"<get_reports report_id=\"{}\" format_id=\"{}\"/>".format(report_id, report_format))
    print("Generated report.")

    save_report(report_file, report)
    print("Saved report to {}.".format(report_file))

    perform_cleanup()
    print("Done!")


def override_settings(args: argparse.Namespace) -> None:
    """Override default settings and start scan."""
    global debug

    scan_profile: str = "Full and fast"
    report_format: str = "ARF"
    alive_test: str = "ICMP, TCP-ACK Service & ARP Ping"
    report_file: str = "openvas.report"
    max_hosts: int = 1
    max_checks: int = 10

    if args.profile is not None:
        if args.profile in scan_profiles:
            scan_profile = args.profile
        else:
            print("{} is not a valid option for profile! Using default: {}.".format(args.profile, scan_profile))

    if args.tests is not None:
        if args.tests in alive_tests:
            alive_test = args.tests
        else:
            print("{} is not valid option for alive tests! Using default: {}.".format(args.tests, alive_test))

    if args.format is not None:
        if args.format in report_formats:
            report_format = args.format
        else:
            print("{} is not a valid option for report format! Using default: {}.".format(args.format, report_format))

    if args.output is not None:
        report_file = args.output

    if args.max is not None:
        max_hosts = args.max

    if args.checks is not None:
        max_checks = args.checks

    if args.debug:
        debug = True

    with open(os.devnull, 'w') as devnull:
        subprocess.check_call(
            ["sed -i 's/max_hosts.*/max_hosts = " + str(max_hosts) + "/' /usr/local/etc/openvas/openvas.conf"],
            shell=True,
            stdout=devnull
        )
        subprocess.check_call(
            ["sed -i 's/max_checks.*/max_checks = " + str(max_checks) + "/' /usr/local/etc/openvas/openvas.conf"],
            shell=True,
            stdout=devnull
        )

    if args.update is True:
        print("Starting and updating OpenVAS...")
        with open(os.devnull, 'w') as devnull:
            subprocess.check_call(["/update"], shell=True, stdout=devnull)
    else:
        print("Starting OpenVAS...")
        with open(os.devnull, 'w') as devnull:
            subprocess.check_call(["/start"], shell=True, stdout=devnull)

    print("Starting scan with settings:")
    print("* Target: {}".format(args.target))
    print("* Excluded hosts: {}".format(args.exclude))
    print("* Scan profile: {}".format(scan_profile))
    print("* Alive tests: {}".format(alive_test))
    print("* Max hosts: {}".format(max_hosts))
    print("* Max checks: {}".format(max_checks))
    print("* Report format: {}".format(report_format))
    print("* Output file: {}".format(report_file))

    make_scan(args.target, args.exclude, alive_test.replace("&", "&amp;"), scan_profiles[scan_profile],
              report_formats[report_format], "/reports/" + report_file)


def parse_arguments():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='Run OpenVAS scan with specified target and save report.')
    parser.add_argument('target', help='scan target')
    parser.add_argument('-o', '--output', help='output file (default: openvas.report)', required=False)
    parser.add_argument('-f', '--format', help='format for report (default: ARF)', required=False)
    parser.add_argument('-p', '--profile', help='scan profile (default: Full and fast)', required=False)
    parser.add_argument('-t', '--tests', help='alive tests (default: ICMP, TCP-ACK Service & ARP Ping)', required=False)
    parser.add_argument('-e', '--exclude', help='hosts excluded from scan target', required=False)
    parser.add_argument('-m', '--max', help='maximum number of simultaneous hosts tested', type=int, required=False)
    parser.add_argument('-c', '--checks', help='maximum number of simultaneous checks against each tested host',
                        type=int, required=False)
    parser.add_argument('--update', help='synchronize feeds before scan is started', nargs='?', const=True,
                        default=False, required=False)
    parser.add_argument('--debug', help='enable command responses printing', nargs='?', const=True, default=False,
                        required=False)

    return parser.parse_args()


if __name__ == '__main__':
    arguments: argparse.Namespace = parse_arguments()

    override_settings(arguments)
