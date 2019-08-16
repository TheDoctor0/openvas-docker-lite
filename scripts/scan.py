#!/usr/bin/env python3

from lxml import etree
import subprocess
import argparse
import time
import os

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
        print("{} is not valid option for alive tests! Using default: {}.".format(args.tests, alive_tests))

if args.format is not None:
    if args.format in report_formats:
        report_format = args.format
    else:
        print("{} is not a valid option for report format! Using default: {}.".format(args.format, report_format))

if args.output is not None:
    report_file = args.output

if args.update is True:
    print("Starting and updating OpenVAS...")
    with open(os.devnull, 'w') as devnull:
        subprocess.check_call(["/update"], shell=True, stdout=devnull)
else:
    print("Starting OpenVAS...")
    with open(os.devnull, 'w') as devnull:
        subprocess.check_call(["/start"], shell=True, stdout=devnull)

print("Starting scan with settings:\n* Target: {}\n* Excluded hosts: {}\n* Scan profile: {}"
      + "\n* Alive tests: {}\n* Report format: {}\n* Output file: {}"
      .format(args.target, args.exclude, scan_profile, alive_test, report_format, report_file))

omp_logon = "-u admin -w admin -h 127.0.0.1 -p 9390"

print("Performing initial cleanup...")

existing_task = "omp {} -G | cut -d ' ' -f 1".format(omp_logon)
existing_task_response = subprocess.check_output(existing_task, stderr=subprocess.STDOUT, shell=True)
if args.debug:
    print("Response: {}".format(existing_task_response))

if existing_task_response != "":
    cleanup_task = "omp {} -D {}".format(omp_logon, existing_task_response.strip())
    cleanup_task_response = subprocess.check_output(cleanup_task, stderr=subprocess.STDOUT, shell=True).strip()
    print("Deleted existing task.")
    if args.debug:
        print("Response: {}".format(cleanup_task_response))

existing_target = "omp {} -T | grep ""{}"" | cut -d ' ' -f 1".format(omp_logon, args.target)
existing_target_response = subprocess.check_output(existing_target, stderr=subprocess.STDOUT, shell=True)
if args.debug:
    print("Response: {}".format(existing_target_response))

if existing_target_response != "":
    cleanup_target = "omp {} -X '<delete_target target_id=\"{}\"/>'".format(omp_logon, existing_target_response.strip())
    cleanup_target_response = subprocess.check_output(cleanup_target, stderr=subprocess.STDOUT, shell=True).strip()
    print("Deleted existing target.")
    if args.debug:
        print("Response: {}".format(cleanup_target_response))

create_target = "omp {0} --xml '<create_target><name>{1}</name><hosts>{1}</hosts>" \
                + "<alive_tests>{2}</alive_tests><exclude_hosts>{3}</exclude_hosts></create_target>'"\
    .format(omp_logon, args.target, alive_test.replace("&", "&amp;"), args.exclude)
create_target_response = subprocess.check_output(create_target, stderr=subprocess.STDOUT, shell=True)
target_id = etree.XML(create_target_response).xpath("//create_target_response")[0].get("id")
print("Created target with id: {}.".format(target_id))
if args.debug:
    print("Response: {}".format(create_target_response))

create_task = "omp {} -C --target={} --config={} --name=scan".format(omp_logon, target_id, scan_profiles[scan_profile])
task_id = subprocess.check_output(create_task, stderr=subprocess.STDOUT, shell=True).strip()
print("Created task with id: {}.".format(task_id))
if args.debug:
    print("Response: {}".format(task_id))

start_task = "omp {} -S {}".format(omp_logon, task_id)
start_task_response = subprocess.check_output(start_task, stderr=subprocess.STDOUT, shell=True)
print("Started task.")
if args.debug:
    print("Response: {}".format(start_task_response))

status = ""
get_status = "omp {} --xml '<get_tasks task_id=\"{}\"/>'".format(omp_logon, task_id)
print("Waiting for task to finish...")

get_status_response = None

while status != "Done":
    try:
        time.sleep(10)

        get_status_response = subprocess.check_output(get_status, stderr=subprocess.STDOUT, shell=True)
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
get_report = "omp {} -R {} -f {} --details".format(omp_logon, report_id, report_formats[report_format])
get_report_response = subprocess.check_output(get_report, stderr=subprocess.STDOUT, shell=True)
print("Generated report.")
if args.debug:
    print("Response: {}".format(get_report_response))

export_path = "/reports/" + report_file
f = open(export_path, 'w')
f.write(get_report_response)
f.close()
print("Saved report to {}.".format(export_path))

print("Performing cleanup...")

delete_task = "omp {} -D {}".format(omp_logon, task_id)
delete_task_reponse = subprocess.check_output(delete_task, stderr=subprocess.STDOUT, shell=True).strip()
print("Deleted task.")
if args.debug:
    print("Response: {}".format(delete_task_reponse))

delete_target = "omp {} -X '<delete_target target_id=\"{}\"/>'".format(omp_logon, target_id)
delete_target_response = subprocess.check_output(delete_target, stderr=subprocess.STDOUT, shell=True).strip()
print("Deleted target.")
if args.debug:
    print("Response: {}".format(delete_target_response))

print("Done!")
