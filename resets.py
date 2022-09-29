import os
import serial.tools.list_ports
import subprocess
import time
import re
import sys
import datetime
import threading

def gen_time_stamp():
	ts = time.time()
	stamp = datetime.datetime.fromtimestamp(ts).strftime('%m-%d-%Y-%H-%M-%S')
	return stamp

def gen_time_stamp_seconds():
	ts = int(round(time.time()))
	return ts

def get_serial_port():
	ports = list(serial.tools.list_ports.comports())
	all_ports = []
	for port_no, description, address in ports:
		if 'USB Serial Port' in description:
			all_ports.append(port_no)
	return all_ports[-1]


def connect_to_serial():
	global ser
	global comport
	comport = get_serial_port()
	if comport is None:
		print "Stopping program, double check setup, unable to find serial comport"
		os._exit(0)
	try:
		ser = serial.Serial(comport,115200, timeout=1)
		print("connected to: " +str(ser.portstr))
	except serial.serialutil.SerialException as e:
		if e:
			print "e is " +str(e)
			print "It seems the serial port " +comport +" is occupied, confirm there is no client connected to it"
			ser = "None"
			print "Stopping program, double check setup"
			os._exit(0)
	return ser
	
def enter_UEFI_shell():
	print "enter UEFI shell function called"
	UEFI = 0
	if count is 1:
		t = threading.Thread(target=reset_device)
		t.daemon = True
		t.start()
		
	for num in range(0,5000):
		ser.write("\033\133\110\r\n")
		out = ser.read(size=64)
		out = out.split(",")
		for line in out:
			#print "the current line is " +out
			m3 = re.search('(EBL >)|(Hotkey detected, entering Menu)',line)
			if m3:
				if m3.group(1) or m3.group(2):
					print "Successfully entered UEFI shell!"
					UEFI = 1
					print "Sleeping for 50 seconds...so that shell is accessible\n"
					time.sleep( 50 )	
					ser.write("\r\n")
					ser.write("\r\n")
					return
			else:
				continue		
		#print "sending bds key"
	
	
	if UEFI is 0:
		print "Did not enter UEFI shell"
		print "Stopping program, double check setup"
		print "last data read was " +str(out)
		os._exit(0)
	return UEFI

def send_reset_command():
    cmd = 'reset'
    ser.write(cmd.encode('ascii')+'\r\n')
    return None	

def reset_device():
	#comport = get_serial_port()
	#ser = connect_to_serial()
	#boot_path,os_type = get_boot_path()
	print "Resetting device function called"
	adb_cmd = "adb devices"
	adb_rsp = subprocess.check_output(adb_cmd, shell=True)
	a1 = re.search('(\S{8})\s+device',adb_rsp)
	if a1:
		print "Device is in adb mode, rebooting into shell"
		adb_reboot_cmd = "adb reboot"
		bldr_rsp = subprocess.check_output(adb_reboot_cmd, shell=True)
	elif not a1:
		fb_cmd = "fastboot devices"
		fast_boot_device_rsp = subprocess.check_output(fb_cmd, shell=True)
		#print "fast_boot_device_rsp is " +fast_boot_device_rsp
		f1 = re.search('(\S+\s+fastboot)',fast_boot_device_rsp)
		if f1:
			flash_rsp = subprocess.check_output("fastboot reboot", shell=True)
			m1 = re.search('error: device',flash_rsp)
					
		else:
			try:
				print "Using spiderboard to reset device since adb and fastboot methods failed"
				spr_rsp = subprocess.check_output("device_controller.exe --use_tac exit_edl", shell=True)
					
			except subprocess.CalledProcessError as e2:
				print "Tried to use used spiderboard to reset device and failed, please connect TAC cable or manually power cycle to enter BDS menu"
				print e2.output
				print "Stopping program, double check setup"
				os._exit(0)


	return None

	
def execute_efi():
	if count is 1:
		get_serial_port()
		connect_to_serial()
		enter_UEFI_shell()
		send_reset_command()
	else:
		enter_UEFI_shell()
		send_reset_command()
	return None

global count

try:
	number_of_resets = str(sys.argv[1])
	count =1
	
except IndexError:
		number_of_resets = None
		print "Stopping program, please provide the number of resets to execute"
		os._exit(0)


while (number_of_resets > 0):
	print "Executing reset # " +str(count)
	execute_efi()
	number_of_resets = int(number_of_resets) -1
	count +=1
else:
	print "Finished all tests!"