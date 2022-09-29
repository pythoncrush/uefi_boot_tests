import os
import serial.tools.list_ports
import subprocess
import time
import re
import sys
import datetime
import threading

def custom_list_check():
	custom_list =[]
	custom_dict ={}
	global custom_list_flag
	custom_list_flag = 0
	try:
		custom_list_file_name = str(sys.argv[2])
		arg_check = re.search('(\S{1})(.+$)',custom_list_file_name)
		if arg_check:
			if arg_check.group(1) == "\\":
				custom_list_flag = None	
		if custom_list_flag is not None:
			list_handle = open(custom_list_file_name, 'r')
			for line in list_handle:
				line = line.strip()
				custom_list.append(line)
				custom_dict = {element:0 for element in custom_list}
			custom_list_flag = 1
			return(custom_dict)		
	except IndexError:
		custom_list_flag = None

	try:
		custom_list_file_name = str(sys.argv[3])
		custom_list_flag = 0
		arg_check = re.search('(\S{1})(.+$)',custom_list_file_name)
		if arg_check:
			if arg_check.group(1) == "\\":
				custom_list_flag = None	
		if custom_list_flag is not None:					
			list_handle = open(custom_list_file_name, 'r')
			for line in list_handle:
				line = line.strip()
				custom_list.append(line)
				custom_dict = {element:0 for element in custom_list}
			custom_list_flag = 1
			return(custom_dict)
	except IndexError:
		custom_list_flag = None	

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
	
	try:	
		return all_ports[-1]

	except IndexError as e:
		if e:
			print "Unable to get serial port, double check setup"
			os._exit(0)

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
	print "Enter UEFI shell function called"
	UEFI = 0
	t = threading.Thread(target=reset_device)
	t.daemon = True
	t.start()
		
	for num in range(0,5000):
		ser.write("\033\133\110\r\n")
		out = ser.read(size=64)
		out = out.split(",")
		for line in out:
			#print "the current line is " +line
			m3 = re.search('(EBL >)|(Hotkey detected, entering Menu)',line)
			if m3:
				if m3.group(1) or m3.group(2):
					print "Successfully entered UEFI shell!"
					UEFI = 1
					#print "UEFI is 1***********\n"
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

def mount_partition():
	print "Mount partition function called"
	tests_found = {}
	global tests_to_run
	cmd = ['cd FV'+str(item)+':' for item in range(0,6)]
	cmd2 = ['cd FS'+str(item)+':' for item in range(0,6)]
	success_flag = 0
	global assert_flag
	global test_partition_cmd
	
	if assert_flag is 1:
		print "Mounting previous partition used before assert"
		ser.write(test_partition_cmd.encode('ascii')+'\r\n')
		success_flag = 1
		return success_flag

	for c in cmd:
		ser.write(c.encode('ascii')+'\r\n')
		out = ser.read(size=64)
		m1 = re.search('cd returned Invalid Parameter error',out)
		if m1:
			print("Encountered an error")
			print "Trying next partition"
			continue
		else:
			print "Changed directory to partition " +c[-4:]
			tests_found = get_efi_tests()
			if assert_flag is 0:
				if not tests_found:
					print "no tests found"
				else:
					print "The tests found are"
					for x,y in tests_found.items():
						if y ==0:
							print x
					if len(tests_found) > 10 :
						success_flag = 1
						print "Will begin execution now on " + c[-4:]
						test_partition_cmd = c
						return success_flag
					else:
						success_flag = 0
	#For SD card tests, not supported for LA, leaving this here because its good code for older targets like 8996
	if success_flag == 0:
		for c2 in cmd2:
			ser.write(c2.encode('ascii')+'\r\n')
			out = ser.read(size=64)
			m1 = re.search('cd returned Invalid Parameter error',out)
			if m1:
				print("Encountered an error")
				print "Trying next partition on SD card"
				continue
			else:
				print "Changed directory to SD partition " +c2[-4:]
	
	
	return success_flag

def get_efi_tests():
	global tests_to_run
	tests_to_run =[]
	global tests_dict
	tests_dict = {}
	cmd = 'dir'
	cmd2 = 'd'
	ser.write(cmd.encode('ascii')+'\r\n')
	#This is in case the list is too long and requires an extra key press
	ser.write(cmd2.encode('ascii')+'\r\n')
	ser.write(cmd2.encode('ascii')+'\r\n')
	ser.write(cmd2.encode('ascii')+'\r\n')
	time.sleep( 50 )
	
	out = ser.read(size=16384)
	out = out.split("\n")

	for line in out:
		m = re.search('\s+\S+\s+App\s+\S+\s+(\S+)',line)
		if m:
			tests_to_run.append(m.group(1))
		tests_dict = {element:0 for element in tests_to_run}
	return tests_dict	

def run_efi_tests():
	global g_list 
	global tests_to_run
	global asserted_tests
	global unknown_tests
	global passed_tests
	global failed_tests
	global stamp
	global completed_test
	global assert_flag
	global log_name
	global f
	global tests_dict
	global remaining_tests

	completed_test =0
   	start_time = 0
   	end_time = 0
   	total_time = 0
   	test_status = 2

	if assert_flag is 1:
		print "Skipping time and test initilization since we already have them"
		print>>f, "Skipping time and test initilization since we already have them from previous session"
		print "tests remaining are these:"
		# print>>f, "tests remaining are these\n"
		# for x,y in tests_dict.items():
		# 	if y ==0:
		# 		print x
		# 		print>>f,x

	else:
		if custom_list_flag is 1:
			tests_dict = custom_list_check()
			print "User has provided a custom list for execution, only these tests will be executed:"
		else:
			tests_dict = get_efi_tests()
		stamp = gen_time_stamp()
		

	log_name = "log_file_" +stamp +".txt"
	f = open(log_name, 'a')
	f.write("These are the tests that will be executed\n")
	for x,y in tests_dict.items():
			if y ==0:
				print x
				print>>f,x

	for key,val in tests_dict.items():
		if val == 0:
			test_status = 0
			total_time = 0
			test_iteration = key
			if test_iteration == "DepTest":
				test_iteration = "start DepTest -X"
				test_api_name = test_iteration[6:]
				test_api_name = test_api_name[:-3]
				ser.write(test_iteration.encode('ascii')+'\n')
			elif test_iteration == "DisplayApp":
				test_iteration = "start DisplayApp -bvt"
				ser.write(test_iteration.encode('ascii')+'\n')
				test_api_name = test_iteration[6:]
				test_api_name = test_api_name[:-5]
			elif test_iteration == "ButtonsTest":
				test_iteration = "start ButtonsTest"
				ser.write(test_iteration.encode('ascii')+'\n')
				for key_cmd in range(0,30):
					ser.write("\033\133\110\r\n")
					time.sleep(5)
				test_api_name = test_iteration[6:]	
			else:
				test_iteration = "start " +test_iteration	
				ser.write(test_iteration.encode('ascii')+'\n')
				test_api_name = test_iteration[6:]
			
			f.write("Executing *************************" +test_api_name +"\n")
			print "Executing *************************" +test_api_name +"\n"

			while(total_time <= 300):
				if(test_status == 1):
					break
				start_time = gen_time_stamp_seconds()
				if test_api_name == "DisplayApp":
					print "sleeping for 600 seconds"
					print>>f,"sleeping for 600 seconds"
					time.sleep(600)	
				elif test_api_name == "EraseTest":
					print "sleeping for 180 seconds"
					print>>f,"sleeping for 180 seconds"
					time.sleep(180)	
				else:
					print "sleeping for 30 seconds"
					print>>f,"sleeping for 30 seconds"
					time.sleep(30)
				out = ser.read(size=16384)
				out = out.split("\n")
				for line in out:
					regex_pattern =  "(ASSERT|assert)|(\*{5}\sTEST\s+\S+\s+PASSED\s+\*{8}|KNOWN BUG)|(FAILED|error|Error|ERROR|Not Found)|(EBL)"
					a1 = re.search(regex_pattern,line)
					if a1:
						if a1.group(1):
							#ASSERTED CASE
							assert_flag =1
							print "Removing *************************" +test_api_name +" Because it asserted\n"
							f.write("Removing *************************" +test_api_name +" Because it asserted\n")
							tests_dict[key] = "assert"
							print>>f, line
							print line +"\n"
							print>>f, "Resetting device because an Assert was found"
							print "Resetting device because an Assert was found"
							return
						elif a1.group(2):
							#PASSED CASE
							print "Completed & Passed*************************" +test_api_name +"\n"
							f.write("Completed & Passed *************************" +test_api_name + "\n")
							tests_dict[key] = "pass"
							print>>f, line
							print line +"\n"
							test_status = 1
							break
						elif a1.group(3):
							#FAILED CASE
							print "Completed & Failed *************************" +test_api_name +"\n"
							f.write("Completed & Failed *************************" +test_api_name + "\n")
							tests_dict[key] = "fail"
							print>>f, line
							print line +"\n"
							test_status = 1
							break
						elif a1.group(4):
							#UNKNOWN CASE
							print "Completed & Unknown result *************************" +test_api_name +"\n"
							f.write("Completed & Unknown result *************************" +test_api_name + "\n")
							tests_dict[key] = "unknown"
							print>>f, line
							print line +"\n"
							test_status = 1
							break
					else:
						print>>f, line
						print line +"\n"

				
				end_time = gen_time_stamp_seconds()
				total_time = total_time + (end_time - start_time)
				print "Time in For loop",total_time	
		else:
			print key," has alreeady been executed, skipping"
			continue		
		if (test_status == 0):
			print test_api_name +" is hung...rebooting and continuing the rest of the tests!!"
			print>>f,test_api_name +" is hung...rebooting and continuing the rest of the tests!!"
			tests_dict[key] = "hung"
			assert_flag =1
			f.close
			return
	else:
		completed_test = 1
		asserted_tests = []
		passed_tests = []	
		failed_tests = []
		unknown_tests = []
		hung_tests = []

		for key,val in tests_dict.items():
			if tests_dict[key] is "assert":
				asserted_tests.append(key)
			elif tests_dict[key] is "pass":
				passed_tests.append(key)
			elif tests_dict[key] is "fail":
				failed_tests.append(key)				
			elif tests_dict[key] is "hung":
				hung_tests.append(key)								
			elif tests_dict[key] is "unknown":
				unknown_tests.append(key)									
		total_run_tests = len(passed_tests) + len(failed_tests) + len(asserted_tests) + len(unknown_tests) + len(hung_tests)
		print>>f,"************************************************************"
		print    "************************************************************"
		print >>f,"TOTAL tests run " +str(total_run_tests)
		print     "TOTAL tests run " +str(total_run_tests)
		print >>f,"TOTAL passed tests ", len(passed_tests)
		print     "TOTAL passed tests ", len(passed_tests)
		
		print >>f,"TOTAL failed tests ", len(failed_tests)
		print     "TOTAL failed tests ", len(failed_tests)
		
		print >>f,"TOTAL asserted tests ", len(asserted_tests)
		print     "TOTAL asserted tests ", len(asserted_tests)
		
		print >>f,"TOTAL unknown tests ", len(unknown_tests)
		print     "TOTAL unknown tests ", len(unknown_tests)

		print >>f,"TOTAL hung tests ", len(hung_tests)
		print     "TOTAL hung tests ", len(hung_tests)
		print>>f,"************************************************************"
		print    "************************************************************"

		print>>f, "These tests passed"
		print "These tests passed"
		for passed_test in passed_tests:
			print>>f, passed_test		
			print passed_test		
		print>>f,"************************************************************"
		print    "************************************************************"
			
		print>>f, "These tests failed"
		print "These tests failed:"
		for failed_test in failed_tests:
			print>>f, failed_test
			print failed_test
		print>>f,"************************************************************"
		print    "************************************************************"
			
		print>>f, "These tests asserted"
		print "These tests asserted"
		for asserted_test in asserted_tests:
			print>>f, asserted_test
			print  asserted_test
		print>>f,"************************************************************"
		print    "************************************************************"
		
		print>>f, "These tests had an unknown result"
		print "These tests had an unknown result"
		for unknown_test in unknown_tests:
			print>>f, unknown_test
			print unknown_test
		print>>f,"************************************************************"
		print    "************************************************************"

		print>>f, "These tests had an hung result"
		print "These tests had an hung result"
		for hung_test in hung_tests:
			print>>f, hung_test
			print hung_test
		print>>f,"************************************************************"
		print    "************************************************************"
		
	f.close
	return None	

def reset_device():
	#comport = get_serial_port()
	#ser = connect_to_serial()
	boot_path,os_type = get_boot_path()
	print "Resetting device function called"
	if os_type == "LA":
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


	if os_type == "WP":
		spr_rsp = subprocess.check_output("device_controller.exe --use_tac exit_edl", shell=True)
	return None

def get_boot_path():
	rtn_vals =[]
	build_path = str(sys.argv[1])
	
	try:
		overridden_boot = str(sys.argv[2])
		arg_check = re.search('(\S{1})(.+$)',overridden_boot)
		if arg_check:
			if arg_check.group(1) != "\\":
				overridden_boot = 'null'	
	except IndexError:
		overridden_boot = 'null'
	cwd = os.getcwd() 
	os.chdir(build_path)

	sys.path.append(os.path.join(os.path.dirname(__file__), 'common/build/lib'))
	import meta_lib as ml
	mi = ml.meta_info()
	
	if overridden_boot == "null":
		boot_path = mi.get_build_path('boot')
	else:
		m1 = re.search('\S+(.+$)',overridden_boot)
		if m1:
			if m1.group(1) == "\\":
				boot_path = overridden_boot
			else:
				boot_path = overridden_boot + "\\"
			
	print "boot path is " +boot_path
	print "build path is" +build_path
	
	rtn_vals.append(boot_path)
	
	m = re.search('MSM(\d+).(\w+)',build_path)
	if m:
		target_number = m.group(1)
		OS_type = m.group(2)

	if OS_type == "WP":
		print "Path provided by user points to a " +target_number+ " device with Windows Mobile OS"
 
	elif OS_type == "LA":
		print "Path provided by user points to a " +target_number+ " device with Linux android OS"

	else:
		print "Path provided by user points to a " +target_number+ " device with an Unknown OS"
	
	rtn_vals.append(OS_type)
	os.chdir(cwd)
	return rtn_vals

	
def flash_tools():
	global stop_flag
	global flash_completed
	flash_completed =0
	stop_flag = 0
	boot_path,os_type = get_boot_path()
	boot_path = boot_path + "boot_images\QcomPkg\QcomTestPkg\Bin\QcomTest\DEBUG\\tests.fv"
		
	if os_type == "LA":
		adb_cmd = "adb devices"
		adb_rsp = subprocess.check_output(adb_cmd, shell=True)
		print adb_rsp
		#a1 = re.search('List of devices attached\n(\S+)\s+device',adb_rsp)
		a1 = re.search('(\S{8})\s+device',adb_rsp)
		if a1:
			print "Device is in adb mode, rebooting into bootloader"
			adb_boot_loader_cmd = "adb reboot bootloader"
			bldr_rsp = subprocess.check_output(adb_boot_loader_cmd, shell=True)
			time.sleep(60)
			
			fb_cmd = "fastboot devices"
			fast_boot_device_rsp = subprocess.check_output(fb_cmd, shell=True)
			print "fast_boot_device_rsp is " +fast_boot_device_rsp
			f1 = re.search('(\S+\s+fastboot)',fast_boot_device_rsp)
			if f1:
				print "Device is in fastboot mode, will now flash toolsfv"
				flash_cmd = "fastboot flash toolsfv " +boot_path
				subprocess.check_output(flash_cmd, shell=True)
				flash_rsp = subprocess.check_output("fastboot reboot", shell=True)
				m1 = re.search('error: device',flash_rsp)
				if m1:
					print "Fastboot reboot failed"
					flash_completed =0
				else:
					flash_completed =1
			else:
				flash_completed =0
		else:
			print "Device is not in adb mode, checking to see if device is in fastboot mode"
			fb_cmd = "fastboot devices"
			fast_boot_device_rsp = subprocess.check_output(fb_cmd, shell=True)
			print "fast_boot_device_rsp is " +fast_boot_device_rsp
			f1 = re.search('(\S+\s+fastboot)',fast_boot_device_rsp)
			if f1:
				if f1.group(1):
					print "Device is in fastboot mode, will now flash toolsfv"
					flash_cmd = "fastboot flash toolsfv " +boot_path
					subprocess.check_output(flash_cmd, shell=True)
					flash_rsp = subprocess.check_output("fastboot reboot", shell=True)
					if not flash_rsp:
						print "Fastboot flash completed successfully, rebooting now using fastboot reboot"
					m1 = re.search('error: device',flash_rsp)
					if m1:
						print "Fastboot reboot failed"
						flash_completed =0
					else:
						print "Fastboot flash completed successfully, rebooting now using fastboot reboot"
						flash_completed =1
			else:
				print "Device is NOT in fastboot mode either, exiting test"
				flash_completed =0
	return flash_completed	

def execute_efi():
	if assert_flag is 0:
		custom_list_check()
		get_serial_port()
		connect_to_serial()
		enter_UEFI_shell()
		mount_partition()
		run_efi_tests()
	else:
		enter_UEFI_shell()
		mount_partition()
		run_efi_tests()
	return None

# stop_flag = flash_tools()
# if stop_flag is 0:
    # os._exit(0)
# time.sleep(180)

global assert_flag
assert_flag =0
execute_efi()

while (assert_flag is 1 and completed_test is 0):
	print "called execute_efi again"
	execute_efi()
else:
	print "Finished all tests!"