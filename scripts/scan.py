#!/usr/bin/env python3

from lxml import etree
import subprocess
import argparse
import time
import os


def get_output(command):
    command = "su - service -c \"gvm-cli --gmp-username service --gmp-password " + \
              "service socket --xml \'{}\'\"".format(command)

    return subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True).decode().strip()


scan_profiles = {
    "Discovery":                    "8715c877-47a0-438d-98a3-27c7a6ab2196",
    "Empty":                        "085569ce-73ed-11df-83c3-002264764cea",
    "Full and fast":                "daba56c8-73ec-11df-a475-002264764cea",
    "Full and fast ultimate":       "698f691e-7489-11df-9d8c-002264764cea",
    "Full and very deep":           "708f25c4-7489-11df-8094-002264764cea",
    "Full and very deep ultimate":  "74db13d6-7489-11df-91b9-002264764cea",
    "Host Discovery":               "2d3f051c-55ba-11e3-bf43-406186ea4fc5",
    "System Discovery":             "bbca7412-a950-11e3-9109-406186ea4fc5"
}

report_formats = {
    "Anonymous XML":    "5057e5cc-b825-11e4-9d0e-28d24461215b",
    "ARF":              "910200ca-dc05-11e1-954f-406186ea4fc5",
    "CPE":              "5ceff8ba-1f62-11e1-ab9f-406186ea4fc5",
    "CSV Hosts":        "9087b18c-626c-11e3-8892-406186ea4fc5",
    "CSV Results":      "c1645568-627a-11e3-a660-406186ea4fc5",
    "HTML":             "6c248850-1f62-11e1-b082-406186ea4fc5",
    "ITG":              "77bd6c4a-1f62-11e1-abf0-406186ea4fc5",
    "LaTeX":            "a684c02c-b531-11e1-bdc2-406186ea4fc5",
    "NBE":              "9ca6fe72-1f62-11e1-9e7c-406186ea4fc5",
    "PDF":              "c402cc3e-b531-11e1-9163-406186ea4fc5",
    "Topology SVG":     "9e5e5deb-879e-4ecc-8be6-a71cd0875cdd",
    "TXT":              "a3810a62-1f62-11e1-9219-406186ea4fc5",
    "Verinice ISM":     "c15ad349-bd8d-457a-880a-c7056532ee15",
    "Verinice ITG":     "50c9950a-f326-11e4-800c-28d24461215b",
    "XML":              "a994b278-1f62-11e1-96ac-406186ea4fc5"
}

alive_tests = {
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

scan_profile = "Full and fast"
report_format = "ARF"
alive_test = "ICMP, TCP-ACK Service & ARP Ping"
report_file = "openvas.report"
max_hosts = 1
max_checks = 10

parser = argparse.ArgumentParser(description='Run OpenVAS scan with specified target and save report.')
parser.add_argument('target', help='scan target')
parser.add_argument('-o', '--output', help='output file (default: openvas.report)',
                    required=False)
parser.add_argument('-f', '--format', help='format for report (default: PDF)',
                    required=False)
parser.add_argument('-p', '--profile', help='scan profile (default: Full and fast)',
                    required=False)
parser.add_argument('-t', '--tests', help='alive tests (default: ICMP, TCP-ACK Service & ARP Ping)',
                    required=False)
parser.add_argument('-e', '--exclude', help='hosts excluded from scan target',
                    required=False)
parser.add_argument('-m', '--max', help='maximum number of simultaneous hosts tested',
                    type=int, required=False)
parser.add_argument('-c', '--checks', help='maximum number of simultaneous checks against each host tested',
                    type=int, required=False)
parser.add_argument('--update', help='synchronize feeds before scan is started',
                    nargs='?', const=True, default=False, required=False)
parser.add_argument('--debug', help='enable printing OMP command responses and OpenVAS logs',
                    nargs='?', const=True, default=False, required=False)

args = parser.parse_args()

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

with open(os.devnull, 'w') as devnull:
    subprocess.check_call(
        ["sed -i 's/max_hosts.*/max_hosts = " + str(max_hosts) + "/' /etc/openvas/openvassd.conf"],
        shell=True,
        stdout=devnull
    )
    subprocess.check_call(
        ["sed -i 's/max_checks.*/max_checks = " + str(max_checks) + "/' /etc/openvas/openvassd.conf"],
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
        subprocess.check_call(["openvas -u"], shell=True, stdout=devnull)

print("Starting scan with settings:")
print("* Target: {}".format(args.target))
print("* Excluded hosts: {}".format(args.exclude))
print("* Scan profile: {}".format(scan_profile))
print("* Alive tests: {}".format(alive_test))
print("* Max hosts: {}".format(max_hosts))
print("* Max checks: {}".format(max_checks))
print("* Report format: {}".format(report_format))
print("* Output file: {}".format(report_file))

print("\nPerforming initial cleanup...")

existing_tasks = "<get_tasks/>".format()
existing_tasks_response = get_output(existing_tasks)
existing_tasks = etree.XML(existing_tasks_response).xpath("//get_tasks_response/task")
if args.debug:
    print("Response: {}".format(existing_tasks_response))

for existing_task in existing_tasks:
    cleanup_task = r"<delete_task task_id=\"{}\" ultimate=\"true\"/>".format(existing_task.get("id"))
    cleanup_task_response = get_output(cleanup_task)
    print("Deleted existing task.")
    if args.debug:
        print("Response: {}".format(cleanup_task_response))

existing_targets = "<get_targets/>".format()
existing_targets_response = get_output(existing_targets)
existing_targets = etree.XML(existing_targets_response).xpath("//get_targets_response/target")
if args.debug:
    print("Response: {}".format(existing_targets_response))

for existing_target in existing_targets:
    cleanup_target = r"<delete_target target_id=\"{}\" ultimate=\"true\"/>".format(existing_target.get("id"))
    cleanup_target_response = get_output(cleanup_target)
    print("Deleted existing target.")
    if args.debug:
        print("Response: {}".format(cleanup_target_response))

create_target = r"<create_target><name>scan</name><hosts>{}</hosts>".format(args.target) + \
                "<alive_tests>{}</alive_tests>".format(alive_test.replace("&", "&amp;")) + \
                "<exclude_hosts>{}</exclude_hosts></create_target>".format(args.exclude)
create_target_response = get_output(create_target)
target_id = etree.XML(create_target_response).xpath("//create_target_response")[0].get("id")
print("Created target.".format(target_id))
if args.debug:
    print("Response: {}".format(create_target_response))

create_task = r"<create_task><name>scan</name>" + \
              r"<target id=\"{}\"></target>".format(target_id) + \
              r"<config id=\"{}\"></config></create_task>".format(scan_profiles[scan_profile])
create_task_response = get_output(create_task)
task_id = etree.XML(create_task_response).xpath("//create_task_response")[0].get("id")
print("Created task.".format(task_id))
if args.debug:
    print("Response: {}".format(task_id))

start_task = r"<start_task task_id=\"{}\"/>".format(task_id)
start_task_response = get_output(start_task)
print("Started task.")
if args.debug:
    print("Response: {}".format(start_task_response))

status = ""
get_status_response = None
get_status = r"<get_tasks task_id=\"{}\"/>".format(task_id)
print("Waiting for task to finish...")

while status != "Done":
    try:
        time.sleep(10)

        get_status_response = get_output(get_status)
        status = etree.XML(get_status_response).xpath("//status")[0].text
        progress = etree.XML(get_status_response).xpath("//progress")[0].text

        if args.debug is False:
            os.system("clear")

        if int(progress) > 0:
            print("Task status: {} {}%".format(status, progress))
        else:
            print("Task status: Complete")

        if args.debug:
            print("Response: {}".format(get_status_response))
    except subprocess.CalledProcessError as exc:
        print("Error: ", exc.output)

if args.debug:
    openvaslog = open("/var/log/openvas/openvassd.messages", "r").read()
    print("OpenVAS Log: {}".format(openvaslog))

report_id = etree.XML(get_status_response).xpath("//report")[0].get("id")
get_report = r"<get_reports report_id=\"{}\" format_id=\"{}\"/>".format(report_id, report_formats[report_format])
get_report_response = get_output(get_report)
print("Generated report.")
if args.debug:
    print("Response: {}".format(get_report_response))

export_path = "/reports/" + report_file
f = open(export_path, 'w')
f.write(get_report_response)
f.close()
print("Saved report to {}.".format(export_path))

print("Performing cleanup...")

delete_task = r"<delete_task task_id=\"{}\" ultimate=\"true\"/>".format(task_id)
delete_task_reponse = get_output(delete_task)
print("Deleted task.")
if args.debug:
    print("Response: {}".format(delete_task_reponse))

delete_target = r"<delete_target target_id=\"{}\" ultimate=\"true\"/>".format(target_id)
delete_target_response = get_output(delete_target)
print("Deleted target.")
if args.debug:
    print("Response: {}".format(delete_target_response))

print("Done!")
