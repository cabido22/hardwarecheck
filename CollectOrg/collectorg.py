"""

This is the icelakex/itpii version of collectorg.
Written By: Jonathan Bentley (jonathan.b.bentley@intel.com)

Running this script will parse the .rpt file and the .res file for a given seed failure.
It will use that information to generate a table that tells the user what instructions the seed
was attempting to execute when the seed failed.

"""


from __future__ import absolute_import
from __future__ import print_function
#from common import toolbox
from bigcore.toolext.CoreIP.DebugUtils import toolbox
from bigcore.toolext.CoreIP.DebugUtils.textutils import AsciiTable
#from alderlake.utilities.textutils import AsciiTable


#from components.ordereddict import odict
#from alderlake.debug.domains.gfx.access.components.ordereddict import odict

_log = toolbox.getLogger("collectorg")



import os, time, re, sys, shutil
import json
import weakref
import six.moves.configparser, optparse, shutil

#import ReportFile
import skylakex.cafe.hopper.ReportFile as ReportFile
#from skylakex.cafe.tools import ReportFile
#from haswellx.cafe.tools import ReportFile


class ResFile(object):
	def __init__(self, resfile):
		"""Initializes ResFile Object by setting the filename and calling the parse function"""
		
		self.filename = resfile
		# These variables will allows us to map back and forth between thread and apic
		self.map_thread2apic = {}
		self.map_apic2thread = {}
		self.thread_cs = {}
		self.thread_rip = {}
		self.thread_halted = {}
		
		self.parse() # Parse the res file we've been given

		
	def parse(self):
		"""Parse the threads and cs:rip for the threads in the file pointed to by filename"""
		
		config = six.moves.configparser.RawConfigParser()
		config.read([self.filename])
		sectlist = config.sections()
		threadslist = []
		numthread = 0
		# Iterating through the section list - looking for thread sections
		for sect in sectlist:
			if sect[0:9] == "Thread #P":
				if sect[-4:] != "LBRs":
					threadslist.append(sect)
		# Now we have a list with all of the threads in it
		
		# These are just some variables to help get the cs and rip for each thread
		cs = ""
		rip = ""
		
		# This for loop gets the cs and rip values for each thread
		for thread in threadslist:
			numthread = int(thread[9:],16)
			try:
				thread_halt = config.get(thread, "Thread Halt")
			except: # if we didn't find section, assume it halted for now....
				thread_halt = "True"
			if thread_halt.count("False"):
				_log.result("Skipping thread: %d b/c it failed to halt"%numthread)
				self.thread_halted[numthread] = False
				continue
			try:
				thread_halt = config.get(thread, "RIP")
				# thread must have halted
				self.thread_halted[numthread] = True
				cs = config.get(thread, "cs")
				cs = cs[2:]
				cs = int(cs, 16)
				self.thread_cs[numthread] = cs
				rip = config.get(thread, "rip")
				rip = rip[2:]
				rip = int(rip, 16)
				self.thread_rip[numthread] = rip
			except: #thread halt must have failed with ERROR message 
				_log.result("Skipping thread: %d Thread halt resulted in error"%numthread)
				self.thread_halted[numthread] = False
				continue

		# These are just some variables to help get apicid for each thread
		apicid = 0
		temp = ""
		apic_temp = 0
		
		# This for loop gets the apic ids for each thread
		for thread in threadslist:
			numthread = int(thread[9:],16)
			temp = config.get(thread, "apicid")
			apic_temp = temp[2:]
			apicid = int(apic_temp, 16)
			self.map_thread2apic[numthread] = apicid
		
		# This for loop generates a list of threads for each apicid
		for item in self.map_thread2apic:
			self.map_apic2thread[self.map_thread2apic[item]] = item
			
		
		#import pdb;pdb.set_trace()

class EIPDumpResFile(ResFile):
	def __init__(self, resfile):
		super(EIPDumpResFile, self).__init__(resfile)
	def parse(self):
		"""Parse the threads and cs:rip for the threads in the file pointed to by filename"""
		import re
		threadslist = []
		numthread = 0
		with open(self.filename) as fp:
			eips = json.load(fp)
			halted_eips = eips["halted"]
			nonrenamed_eips = eips["nonrenamed"]
			for i in nonrenamed_eips.keys():
				key = i
				if key in halted_eips.keys():
					threadslist.append((key, halted_eips[key][1], halted_eips[key][0]))
				else:
					threadslist.append((key, nonrenamed_eips[key], "-0x1"))
			#for res in section_re.findall(data):
			#	threadslist.append((res[0], res[1], res[2]))
			#for res in no_halt_re.findall(data):
			#	self.thread_halted[int(res, 16)] = False
		cs = ""
		rip = ""
		for thread in threadslist:
			numthread = int(thread[0],16)
			try:
				thread_halt = thread[1]
				self.thread_halted[numthread] = True
				cs = thread[2]
				cs = int(cs, 16)
				self.thread_cs[numthread] = cs
				rip = thread[1]
				rip = int(rip, 16)
				self.thread_rip[numthread] = rip
			except: #thread halt must have failed with ERROR message 
				_log.result("Skipping thread: %d Thread halt resulted in error"%numthread)
				self.thread_halted[numthread] = False
				continue
		apicid = 0
		temp = ""
		apic_temp = 0
		for thread in threadslist:
			numthread = int(thread[0],16)
			apic_temp = thread[0]
			apicid = int(apic_temp, 16)
			self.map_thread2apic[numthread] = apicid
		for item in self.map_thread2apic:
			self.map_apic2thread[self.map_thread2apic[item]] = item

class PostElFile(ResFile):
	def __init__(self, resfile):
		super(PostElResFile, self).__init__(resfile)
	def parse(self):
		"""Parse the threads and cs:rip for the threads in the file pointed to by filename"""
		import re
		threadslist = []
		numthread = 0
		section_re = re.compile(r"apicid=\[\d+b\] (0x[0-9a-fA-F]+).*?rip = \[\d+b\] (0x[0-9a-fA-F]+)..cs = \[\d+b\] (0x[0-9a-fA-F]+)", re.DOTALL)
		no_halt_re = re.compile(r"can't halt thread (0x[0-9a-fA-F]+)")
		with open(self.filename) as fp:
			data = fp.read()
			for res in section_re.findall(data):
				threadslist.append((res[0], res[1], res[2]))
			for res in no_halt_re.findall(data):
				self.thread_halted[int(res, 16)] = False
		cs = ""
		rip = ""
		for thread in threadslist:
			numthread = int(thread[0],16)
			try:
				thread_halt = thread[1]
				self.thread_halted[numthread] = True
				cs = thread[2]
				cs = int(cs, 16)
				self.thread_cs[numthread] = cs
				rip = thread[1]
				rip = int(rip, 16)
				self.thread_rip[numthread] = rip
			except: #thread halt must have failed with ERROR message 
				_log.result("Skipping thread: %d Thread halt resulted in error"%numthread)
				self.thread_halted[numthread] = False
				continue
		apicid = 0
		temp = ""
		apic_temp = 0
		for thread in threadslist:
			numthread = int(thread[0],16)
			apic_temp = thread[0]
			apicid = int(apic_temp, 16)
			self.map_thread2apic[numthread] = apicid
		for item in self.map_thread2apic:
			self.map_apic2thread[self.map_thread2apic[item]] = item

class ResFile(ResFile):
	def __init__(self, resfile):
		super(PostElResFile, self).__init__(resfile)
	def parse(self):
		"""Parse the threads and cs:rip for the threads in the file pointed to by filename"""
		import re
		threadslist = []
		numthread = 0
		section_re = re.compile(r"apicid=\[\d+b\] (0x[0-9a-fA-F]+).*?rip = \[\d+b\] (0x[0-9a-fA-F]+)..cs = \[\d+b\] (0x[0-9a-fA-F]+)", re.DOTALL)
		no_halt_re = re.compile(r"can't halt thread (0x[0-9a-fA-F]+)")
		with open(self.filename) as fp:
			data = fp.read()
			for res in section_re.findall(data):
				threadslist.append((res[0], res[2], res[3]))
			for res in no_halt_re.findall(data):
				self.thread_halted[int(res, 16)] = False
		cs = ""
		rip = ""
		for thread in threadslist:
			numthread = int(thread[0],16)
			try:
				thread_halt = thread[1]
				self.thread_halted[numthread] = True
				cs = thread[2]
				cs = int(cs, 16)
				self.thread_cs[numthread] = cs
				rip = thread[1]
				rip = int(rip, 16)
				self.thread_rip[numthread] = rip
			except: #thread halt must have failed with ERROR message 
				_log.result("Skipping thread: %d Thread halt resulted in error"%numthread)
				self.thread_halted[numthread] = False
				continue
		apicid = 0
		temp = ""
		apic_temp = 0
		for thread in threadslist:
			numthread = int(thread[0],16)
			apic_temp = thread[0]
			apicid = int(apic_temp, 16)
			self.map_thread2apic[numthread] = apicid
		for item in self.map_thread2apic:
			self.map_apic2thread[self.map_thread2apic[item]] = item

class Collect:
	def __init__(self):
		"""Class for calling parsing functions and for generating table"""
		
		self.rptfile = None # holds report file object
		self.resfile = None # holds res file object
		# The following allows conversion from cafe thread to itp thread and vice versa
		self.cafe2apic = {}
		self.apic2cafe = {}
		self.thread2apic = {}
		self.apic2thread = {}
		self.thread2cafe = {}
		self.cafe2thread = {}
		self.sects_found = {} # holds 'section':'linenumber' pairs
		
		
		
	def start(self,resfile, rptfile, apath):
		self.rptfilename = rptfile
		self.resfilename = resfile
	
		lcase_rpt = self.rptfilename.lower()
		lcase_res = self.resfilename.lower()

		_log.result("\nParsing Report file...")
		self.rptfile = ReportFile.ReportFile(  self.rptfilename )
		# Copy zpickle File from Regenerate to User.Analysis
		shutil.copy(self.rptfilename+'.zpickle', apath)
		_log.result("\nParsing Res file...")
		if self.resfilename.endswith("eip_dump.json"):
			self.resfile = EIPDumpResFile(self.resfilename)
		elif self.resfilename.endswith("el_post.log"):
			self.resfile = PostElFile(self.resfilename)
		else:
			self.resfile = ResFile(self.resfilename)
		
		# Generate the thread2cafe dictionary
		for item in self.resfile.map_thread2apic:
			if (self.resfile.map_thread2apic[item] in self.rptfile.map_apic2cafe) == True:
				self.thread2cafe[item] = self.rptfile.map_apic2cafe[self.resfile.map_thread2apic[item]]
		
		# Generate the cafe2thread dictionary
		for item in self.thread2cafe:
			self.cafe2thread[self.thread2cafe[item]] = item
		
		_log.result("")
		
		self.whereami() # Calls function to write table with values
		
		_log.closeFile()
		#import pdb;pdb.set_trace()
		
		
	def whereami(self,**kwargs):
		"""Prints the table to the console and to the log file -- No Paramters Needed"""
		
		log = kwargs.get('collectorg',_log)
		table = AsciiTable(log.result)
		# print where we are at in the report file if we can find it
		#all_threads = self.map_cafe2itp.keys()
		#all_threads.sort()
		table.setColumnName(0,"C##")
		table.setColumnName(1,"P##")
		table.setColumnName(2,"CS")
		table.setColumnJustify("CS","right")
		table.setColumnName(3,"RIP")
		table.setColumnJustify("RIP","right")
		table.setColumnName(4,"Instr")
		table.setColumnName(5,"Recipe")
		table.setColumnName(6, "Opcode")
		table.setColumnName(7, "Non-renamed")
		#table.setColumnName(6,"J$")
		table.setRowJustify("all","center") # so that we align when we have multiple instructions
		table.setBorder("row","-")
		i=-1
		#import pdb; pdb.set_trace()
		for cthread in self.cafe2thread:
			ithread_num = self.cafe2thread[cthread]
			# skipt the row if the thread didn't halt
			if not self.resfile.thread_halted.get(ithread_num,False):
				continue
			i+=1 
			if i%2==1: table.setRowColor(i,'grey,blue')
			table.write(i,"C##","%d"%cthread)
			
			table.write(i,"P##","%d"%ithread_num)
			
			cs = self.resfile.thread_cs[ithread_num]
			rip = self.resfile.thread_rip[ithread_num]
			table.write(i,"CS","0x%04x"%cs)
			# try to add some leading 0's to help debuggers and cafe rpt file...
			if rip<(1<<32):     table.write(i,"RIP","0x%08x"%rip)
			elif rip<(1<<48):   table.write(i,"RIP","0x%012x"%rip)
			else:               table.write(i,"RIP","0x%016x"%rip)
			instr = None
			if cs != -1:
				instr = self.rptfile.getinstr(cs, rip)
			else:
				instr = self.rptfile.getinstrLA(rip)
				table.write(i, "Non-renamed", "*")
			if instr != None: 
				if instr.prev_instr: # good for seeing MWAITs
					table.write(i,"Instr","%s\n"%instr.prev_instr.instruction)
					table.write(i,"Recipe","%s %s\n"%(instr.prev_instr.recipe_info,instr.prev_instr.comment))
					table.write(i,"Opcode","%s\n"%instr.prev_instr.instr_bytes)
				# now output current
				table.write(i,"Instr","%s"%instr.instruction)
				table.write(i,"Recipe","%s %s"%(instr.recipe_info,instr.comment))
				table.write(i,"Opcode", instr.instr_bytes)
				# now output instr after
				if instr.next_instr:
					table.write(i,"Instr","\n%s"%instr.next_instr.instruction)
					table.write(i,"Recipe","\n%s %s"%(instr.next_instr.recipe_info,instr.next_instr.comment))
					table.write(i,"Opcode","\n%s"%instr.next_instr.instr_bytes)
				# keep up with last PA
				phys = instr.PA
			elif cs==0x10: # in setup/completion code
				phys = rip
			else:  # we apparently don't know about this location..
				phys = None
			

		table.show()
		
		_log.info("\n\nSECTIONS AND LINE NUMBERS OF REPORT FILE\n\n")
		
		
		for key in self.rptfile.sects_found:
			_log.info(str(self.rptfile.sects_found[key]) + '\t\t' + str(key))


def getrptfile(faildir):
	"""Given a dir, return the rpt file"""
	
	if os.path.exists("%s\\Regenerate"%faildir):
		for filename in os.listdir("%s\\Regenerate"%faildir):
			if filename.endswith(".rpt"):
				
				return "%s\\Regenerate\\%s"%(faildir, filename)
	# If we didn't find it here, then check the collect....
	if os.path.exists("%s\\Collect"%faildir):
		for filename in os.listdir("%s\\Collect"%faildir):
			if filename.endswith(".rpt"):
				return "%s\\Collect\\%s"%(faildir, filename)
	_log.result("Could not find Report file")


def getresfile(faildir):
	"""Given a dir, return the res file"""
	# If backup exists, then that must be the one we should use
	if os.path.exists("%s\\Collect"%faildir):
		for filename in os.listdir("%s\\Collect"%faildir):
			if filename.endswith("eip_dump.json"):
				_log.result("Using eip_dump.json file")
				return "%s\\Collect\\%s"%(faildir, filename)	
	if os.path.exists("%s\\Collect"%faildir):
		for filename in os.listdir("%s\\Collect"%faildir):
			if filename.endswith("el_post.log"):
				_log.result("Using post_el.log file")
				return "%s\\Collect\\%s"%(faildir, filename)	
	_log.result("Could not find post_el file...trying Resbackup file")
	if os.path.exists("%s\\Collect"%faildir):
		for filename in os.listdir("%s\\Collect"%faildir):
			if filename.endswith(".resbackup"):
				_log.result("Using .resbackup file")
				return "%s\\Collect\\%s"%(faildir, filename)	
	_log.result("Could not find Res backup file...trying RES file")
	if os.path.exists("%s\\Collect"%faildir):
		for filename in os.listdir("%s\\Collect"%faildir):
			if filename.endswith(".res"):
				return "%s\\Collect\\%s"%(faildir, filename)
	_log.result("Could not find Res file")
	return


def run_flow(action):
    """Entry point for the flow"""
    action.log("CollectOrg: Entry to run_flow()")
    try:
       action.test.analysis_data.collect_output_folder = action.output_folder

       cpath = action.test.get_collect_folder()
       #cpath1= action.test.analysis_data.collect_output_folder
       if not os.path.exists(cpath):
          raise Exception("Path '%s' does not exist!"%cpath)
       rpath = cpath.replace(r'\Collect','')
       action.log("FailureFolder: %s" % rpath)
       action.log("CollectFolder: %s" % cpath)
       #apath = action.local_folder
       apath = "%s\\%s" % (rpath,"CollectOrg")#collect_org_default_folder_name)
       action.log("CollectOrgFolder: %s" % apath)
       if not os.path.exists(apath):
          os.mkdir(apath)
       _log.setFile(apath+"\\collectorg.log", overwrite=True)
       _log.setFileLevel(5) # Send messages with RESULT level or higher to File
       _log.setConsoleLevel(25) # Send all messages to the Console
       _log.setFileFormat("simple")

       resfile = getresfile(rpath)
       action.log("ResFile: %s" % resfile)

       rptfile = getrptfile(rpath)	
       action.log("rptFile=%s"%rptfile)

       collect = Collect()
       collect.start(resfile, rptfile, apath)

       from ini2html import ini2html
       ini2html(resfile,apath+"\\res.html")

       action.log("CollectOrg: Done")
       _log.closeFile()

       return collect
    except Exception as e:
       action.log("Unexpected Error! %s"%str(e))
       _log.closeFile()
 

def find_key_in_json(json_file, key):
    """Load ZordonSystem.json to extract ProgramName - Carlos"""
    with open(json_file, "r") as file:
        data = json.load(file)

    result = find_key_recursive(data, key)
    return result

def find_key_recursive(data, key):
    """function to extract key - Carlos"""
    if isinstance(data, dict):
        if key in data:
            return data[key]
        else:
            for sub_data in data.values():
                result = find_key_recursive(sub_data, key)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = find_key_recursive(item, key)
            if result is not None:
                return result
    return None

def get_latest_folder(path):
    """Find the latest folder created"""
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    #latest_folder = max(folders, key=os.path.getctime)
    latest_folder = folders[-1]
    return latest_folder

def debug_run_flow():
    """Entry point for the flow"""
    #action.log("CollectOrg: Entry to run_flow()")
    
    
    try:
       #action.test.analysis_data.collect_output_folder = action.output_folder
       #cpath = r"\\amr\ec\proj\an\CLX\CoreSVFMS\prod\Core_IP-Mass_Exe\AN4CORECAFE303\C35922\Collect"
       
       ### converted hardcode cpath to dynamic path - Carlos ###
       #cpath = r"\\amr.corp.intel.com\EC\proj\an\CLX\CoreSVFMS\prod\Core_IP-PRT\AN4COREPRT053\C48877\Collect"
       zordonpath = r"C:\SVSHARE\ExecutionScripts\CurrentZordonSystem\ZordonSystem.json"
       ProjectName = str(find_key_in_json(zordonpath, 'ProjectName'))
       server_path = r"\\amr.corp.intel.com\EC\proj\an\CLX\CoreSVFMS\prod"
       host = str(os.environ['COMPUTERNAME'])
       path = server_path + '\\' + ProjectName + '\\' + host
       last_folder = get_latest_folder(path)
       cpath = path + '\\' + last_folder + '\\Collect'
       
       ###
       #cpath1= action.test.analysis_data.collect_output_folder
       if not os.path.exists(cpath):
          raise Exception("Path '%s' does not exist!"%cpath)
       
       rpath = cpath.replace(r'\Collect','')
       #action.log("FailureFolder: %s" % rpath)
       #action.log("CollectFolder: %s" % cpath)
       #apath = action.local_folder
       apath = "%s\\%s" % (rpath,"CollectOrg")#collect_org_default_folder_name)
       #action.log("CollectOrgFolder: %s" % apath)
       if not os.path.exists(apath):
          os.mkdir(apath)
       _log.setFile(apath+"\\collectorg.log", overwrite=True)
       _log.setFileLevel(5) # Send messages with RESULT level or higher to File
       _log.setConsoleLevel(25) # Send all messages to the Console
       _log.setFileFormat("simple")

       resfile = getresfile(rpath)
       #action.log("ResFile: %s" % resfile)

       rptfile = getrptfile(rpath)	
       #action.log("rptFile=%s"%rptfile)

       collect = Collect()
       collect.start(resfile, rptfile, apath)
       
       # from ini2html import ini2html
       # ini2html(resfile,apath+"\\res.html")
       
       """Created json2hmtl script output json file - Carlos"""
       from json2html import json2html
       json2html(resfile,apath+"\\res.html")

       #action.log("CollectOrg: Done")
       _log.closeFile()
       return collect
    except Exception as e:
       #action.log("Unexpected Error! %s"%str(e))
       _log.closeFile()

if __name__ =="__main__":
    debug_run_flow()
