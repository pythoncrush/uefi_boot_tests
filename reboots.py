import os
import subprocess
import time
import re
import sys
import datetime
import threading


#state_flag
#adb devices = 1
#fastboot devices =2
#rebooting = 3
#error =4

class States():
	def __init__(self,value):
		self.value = value
	def assign_command(self,cmd):
		self.cmd =cmd
	
adb_mode = States(1)
fastboot_mode = States(2)
error_mode = States(0)


adb_mode.assign_command("adb devices")
fastboot_mode.assign_command("fastboot devices")

def get_state():
	cmd_list =(fastboot_mode.cmd,adb_mode.cmd)
	for cmd in cmd_list:
		try:
			current_cmd = cmd
			cmd_rsp = subprocess.check_output(current_cmd, shell=True)
			m1 = re.search('(\S{8}\s+device)|(fastboot)|(error:)',cmd_rsp)
			if m1:
				if m1.group(1):
					return adb_mode.value
				if m1.group(2):
					return fastboot_mode.value
				if m1.group(3):
					return error_mode.value
		except 	subprocess.CalledProcessError as e:
			print "command " +cmd + "failed"
			print "exiting program, double check setup"
			print e.output
			return "error"
			os._exit(0)

def change_state():
	for x in range(0,10):
		time.sleep(3)
		state = get_state()
		if state is not error_mode.value:
			break
	
	if state is error_mode.value:
		print "exiting program, double check setup"
		os._exit(0)
	if state is adb_mode.value:
		try:
			cmd_rsp = subprocess.check_output("adb reboot bootloader", shell=True)
			if not cmd_rsp:
				print "entered adb mode successfully"
				return "adb_success"
			else:
				return "adb_failure"
		except 	subprocess.CalledProcessError as e:
			print "exiting program, double check setup"
			print e.output
			return "error"
			os._exit(0)

	if state is fastboot_mode.value:
		try:
			cmd_rsp = subprocess.check_output("fastboot reboot", shell=True)
			if not cmd_rsp:
				print "entered fastboot mode successfully"
				return "fastboot_success"
			else:
				return "fastboot_failure"
		except 	subprocess.CalledProcessError as e:
			print "exiting program, double check setup"
			print e.output
			return "error"
			os._exit(0)		

try:
		number_of_iterations = str(sys.argv[1])
		arg_check = re.search('(\d+)',number_of_iterations)
		if arg_check.group(1):
			print "User wants to execute "+ arg_check.group(1) + " iterations of reboots"
		else:
			print "unknown iteration input, exiting program"
			os._exit(0)
except IndexError:
		number_of_iterations = None
		print "missing iteration argument, please provide an integer"
		os._exit(0)

results = []
count =1
while(number_of_iterations > 0):
	print "Executing iteration # ",count
	verdict = change_state()
	results.append(verdict)
	number_of_iterations = int(number_of_iterations) -1
	count +=1
	time.sleep(75)
else:
	fbs=0
	fbf=0
	ads=0
	adf=0
	#print results
	for result in results:
		if result =="fastboot_success":
			fbs +=1
		if result =="fastboot_failure":
			fbf +=1
		if result =="adb_success":
			ads +=1
		if result =="adb_failure":
			adf +=1	

	print "Transition to Fastboot passed ", fbs 
	print "Transition to Fastboot failed ", fbf
	print "Transition to ADB passed      ", ads
	print "Transition to ADB failed      ", adf

# def fb_to_adb():
# 	fb_cmd = "fastboot devices"
# 	for num in range(0,5):
# 		time.sleep( 3 )	
# 		fast_boot_device_rsp = subprocess.check_output(fb_cmd, shell=True)
# 		print "fast_boot_device_rsp is " +fast_boot_device_rsp
# 		f1 = re.search('(\S{8}\s+fastboot)',fast_boot_device_rsp)
# 		if f1:
# 			if f1.group(1):
# 				print "Device is in fastboot mode, will now try to reboot to adb mode"
# 				break
# 			else:
# 				print "Device is not in fastboot mode, sleeping 3 seconds and will check again"

# 	for num in range(0,5):
# 		time.sleep( 3 )	
# 		try:
# 			flash_cmd = "fastboot reboot"
# 			fast_rsp = subprocess.check_output(flash_cmd, shell=True)
# 			m1 = re.search('(error: device)(rebooting\.{3})',fast_rsp)
# 			if m1:
# 				if m1.gorup(2):
# 					print "Fastboot reboot passed"
# 					print "Calling adb to fb function now"
# 					adb_to_fb()
# 					return
# 				else:
# 					print "Device did not reboot yet, sleeping 3 seconds and will check again"
# 		except 	subprocess.CalledProcessError as e:
# 			print "device is not in adb mode"
# 			print e.output
# 			print "Calling adb check function"
# 			adb_to_fb()
# 	return

# def adb_to_fb():
# 	adb_cmd = "adb devices"
# 	for num in range(0,60):
# 		time.sleep( 3 )	
# 		adb_device_rsp = subprocess.check_output(adb_cmd, shell=True)
# 		print "adb devices response is \n" +adb_device_rsp
# 		f2 = re.search('(\S+\s+device)|(error: device not found)',adb_device_rsp)
# 		if f2:
# 			if f2.group(1):
# 				print "Device is in adb mode, will reboot to fastboot mode"
# 				adb_cmd2 = "adb reboot bootloader"
# 				try:
# 					adb_cmd2_rsp = subprocess.check_output(adb_cmd2, shell=True)
# 					print "adb to fastboot reboot passed"
# 					fb_to_adb()
# 				except 	subprocess.CalledProcessError as e2:
# 					print "device is not in adb mode"
# 					print e2.output
# 					print "Calling fastboot check function"
# 					fb_to_adb()
# 	else:
# 		print "timeout after 3 mins did not find device in adb mode exiting program"
# 		os._exit(0)
# 	return	


