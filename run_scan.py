#!/usr/bin/python
from __future__ import print_function
from lxml import etree
import os, sys, time
import subprocess
import argparse

configs = [
    "8715c877-47a0-438d-98a3-27c7a6ab2196", # Discovery
    "085569ce-73ed-11df-83c3-002264764cea", # Empty
    "daba56c8-73ec-11df-a475-002264764cea", # Full and fast
    "698f691e-7489-11df-9d8c-002264764cea", # Full and fast ultimate
    "708f25c4-7489-11df-8094-002264764cea", # Full and very deep
    "74db13d6-7489-11df-91b9-002264764cea", # Full and very deep ultimate
    "2d3f051c-55ba-11e3-bf43-406186ea4fc5", # Host Discovery
    "bbca7412-a950-11e3-9109-406186ea4fc5"  # System Discovery
]

report_formats = [
    "5057e5cc-b825-11e4-9d0e-28d24461215b", # Anonymous XML
    "910200ca-dc05-11e1-954f-406186ea4fc5", # ARF
    "5ceff8ba-1f62-11e1-ab9f-406186ea4fc5", # CPE
    "9087b18c-626c-11e3-8892-406186ea4fc5", # CSV Hosts
    "c1645568-627a-11e3-a660-406186ea4fc5", # CSV Results
    "6c248850-1f62-11e1-b082-406186ea4fc5", # HTML
    "77bd6c4a-1f62-11e1-abf0-406186ea4fc5", # ITG
    "a684c02c-b531-11e1-bdc2-406186ea4fc5", # LaTeX
    "9ca6fe72-1f62-11e1-9e7c-406186ea4fc5", # NBE
    "c402cc3e-b531-11e1-9163-406186ea4fc5", # PDF
    "9e5e5deb-879e-4ecc-8be6-a71cd0875cdd", # Topology SVG
    "a3810a62-1f62-11e1-9219-406186ea4fc5", # TXT
    "c15ad349-bd8d-457a-880a-c7056532ee15", # Verinice ISM
    "50c9950a-f326-11e4-800c-28d24461215b", # Verinice ITG
    "a994b278-1f62-11e1-96ac-406186ea4fc5", # XML
]

config = configs[2]
report_format = report_formats[5]

if len(sys.argv) < 3:
    sys.exit('Usage: %s <scan target> <output file>' % sys.argv[0])

if len(sys.argv) == 4 && sys.argv[4] == '--update':
    print('Starting and updating OpenVAS')
    subprocess.call(['/update'])
else:
    print('Starting OpenVAS')
    subprocess.call(['/start'])

print('Starting scan')

omp_logon = "-u admin -w admin -h 127.0.0.1 -p 9390"

create_target = "omp {0} --xml '<create_target><name>{1}</name><hosts>{1}</hosts></create_target>'".format(omp_logon, sys.argv[1])
create_target_response = subprocess.check_output(create_target, stderr=subprocess.STDOUT, shell=True)
print("Create target reponse: {}".format(create_target_response))

target_id = etree.XML(create_target_response).xpath("//create_target_response")[0].get("id")
print("Target ID: {}".format(target_id))

create_task = ("omp {} -C --target={} --config={} --name=scan").format(omp_logon, target_id, config)
task_id = subprocess.check_output(create_task, stderr=subprocess.STDOUT, shell=True).strip()
print("Task ID: {}".format(task_id))

start_task = "omp {} -S {}".format(omp_logon, task_id)
start_task_response = subprocess.check_output(start_task, stderr=subprocess.STDOUT, shell=True)
print("Start task response: {}".format(start_task_response))

print("Waiting for task to finish")

status = ""
get_status = "omp {} --xml '<get_tasks task_id=\"{}\"/>'".format(omp_logon, task_id)

while status != "Done":
    try:
        time.sleep(10)
        get_status_response = subprocess.check_output(get_status, stderr=subprocess.STDOUT, shell=True)
        status = etree.XML(get_status_response).xpath("//status")[0].text
        progress = etree.XML(get_status_response).xpath("//progress")[0].text
        print("Status: {} {}%".format(status, progress))
    except subprocess.CalledProcessError as exc:
        print("Error: ", exc.output)

openvaslog = open("/var/log/openvas/openvassd.messages", "r").read()
print("OpenVAS Log: {}".format(openvaslog))
report_id = etree.XML(get_status_response).xpath("//report")[0].get("id")
print("Report ID: {}".format(report_id))
get_report = "omp {} -R {} -f {} --details".format(omp_logon, report_id, report_format)
report_response = subprocess.check_output(get_report, stderr=subprocess.STDOUT, shell=True)
print("Report: {}".format(report_response[:30]))

report_filename = os.path.split(sys.argv[2])[1]
export_path = "/openvas/results/" + report_filename
print('Writing report to ' + export_path)

f = open(export_path, 'w')
f.write(report_response)
f.close()

print('Done!')
