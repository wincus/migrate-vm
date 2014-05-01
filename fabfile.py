from fabric.api import run,env,put,cd,sudo,settings,local
from fabric.exceptions import CommandTimeout

env.warn_only = True
libvirt_path = "/var/lib/libvirt/images"
org = "user@org.server.com"  # source server
dst = "user@dst.server.com"  # destination server
tmp = "/var/tmp"

env.forward_agent = True

def sleep():
	run("sleep 3")

def status_vm(vm):
	sudo("virsh domstate %s" % vm)

def shutdown_vm(vm):
	with settings(host_string=org):
		sudo("virsh shutdown %s" % vm)
		while True:
			local("sleep 5")
		        result = sudo("virsh domstate %s" % vm)
			if "shut off" in result:
				return True

def get_disks(vm):
	with settings(host_string=org):
		disks = sudo("virsh domblklist %s" % vm)
		return disks

def check_dsk_presence(disk):
	with settings(host_string=dst):
		result = sudo("test -f %s/%s" % (libvirt_path,disk.strip()))
		if result.return_code == 0:
			return True
		else:
			return False

def copy_disk_tmp(disk):
	with settings(host_string=org):
		run("scp %s/%s %s:%s/" % (libvirt_path,disk.strip(),dst,tmp))

def mv_disk_from_tmp(disk):
	with settings(host_string=dst):
		sudo("mv -v %s/%s %s" % (tmp,disk.strip(),libvirt_path))

def copy_vm_blk(vm):
	with settings(host_string=org):
		disks = get_disks(vm)
		for line in disks.split("\n"):
			if "/var/lib/libvirt/images" in line:
				disk_name = line.split("/")
				if check_dsk_presence(disk_name[-1]):
					print "already there"
				else:
					print "should copy it"
					copy_disk_tmp(disk_name[-1].strip())
					mv_disk_from_tmp(disk_name[-1].strip())
def dump_xml(vm):
	with settings(host_string=org):
		xml = sudo("virsh dumpxml %s > /tmp/%s.xml" % (vm,vm))
		if xml.return_code == 0:
			run("scp /tmp/%s.xml %s:/tmp" % (vm,dst))
			return True
		else:
			return False

def define_vm(vm):
	with settings(host_string=dst):
		sudo("virsh define /tmp/%s.xml" % vm)
	
def autostart_vm(vm):
	with settings(host_string=dst):
		sudo("virsh autostart %s" % vm)

def start_vm(vm):
	with settings(host_string=dst):
		sudo("virsh start %s" % vm)

def migrate_vm(vm):
	shutdown_vm(vm)  #shuts down and waits
	copy_vm_blk(vm)  #cp storage
	dump_xml(vm)     #dump & copy
	define_vm(vm)	 #creates vm
	autostart_vm(vm) #autostartsvm
	start_vm(vm)	 #start vm
