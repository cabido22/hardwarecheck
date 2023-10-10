import re,sys,os
from types import LongType,IntType
import weakref
import cPickle,time,zlib
from functools import partial
import pdb

from components.ordereddict import odict

from common import toolbox
from copy import copy

_log = toolbox.getLogger("hopper")

# very simple class used to store instruction information
class Instruction:
    # some defaults needed
    prev_instr = None
    next_instr = None
    instruction = ""
    recipe_info = ""
    def __str__(self):
        keys = self.__dict__.keys()
        m = ""
        keys.sort()
        for k in keys:
            val = getattr(self,k)
            if type(val) in [LongType,IntType]:
                m+="%s=0x%x\n"%(k,val)
            else:
                m += "%s=%s\n"%(k,val)
        return m
    

class ReportFile:
    filename=None
    # so we can map back and forth between cafe and apic
    map_cafe2apic = None
    map_apic2cafe = None
    map_cafe2phys = None
    map_phys2cafe = None        
    active_cthreads = None
    # these get filled in and used by various functions
    checkpoints = None
    last_checkpoint = None
    sects_found = None
    sects_search = None
    random_instrs_by_thread = None
    instrs_by_cs_rip = None
    instrs_by_LA = None
    # to help with pickle unpickling....
    pickle_attrs = ['filename','map_cafe2apic','map_apic2cafe','map_cafe2phys','map_phys2cafe','active_cthreads']
    #checpoint_re = re.compile("\[(\d+)\].*CS:(\w+)\s+Addr Range:(\w+)L\s+\((\w+)P\).*CheckPointNum_(\w+)")
    checkpoint_re = re.compile("\[(\d+)\]\s+CS:(\w+)\s+Addr Range:.*\)(.*) AsmFile")
    handler_re   = re.compile("\[(\d+)\]\s+CS:(\w+)\s+Addr Range:.*\)(.*Handler)") # Addr Range is gready on purpose .* is 
    misc_sect_re   = re.compile("\[(\d+)\]\s+CS:(\w+)\s+Addr Range:.*\)(.*)")# Addr Range is gready on purpose .* is 
    fixed_code_re = re.compile("\[(\d+)\]\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+([a-zA-Z0-9-$]+)\s+(.*?;)")
                    # groups created are: thread,eip,lip,pip,mtype,mode,instr
    
    def __init__(self,reportfile):
        self.filename = reportfile
        self.picklefilename = self.filename+".zpickle"
        # so we can map back and forth between cafe and apic
        self.version = 1 # used to flag when the pickle will break
        self.map_cafe2apic = {}
        self.map_apic2cafe = {}
        self.map_cafe2phys = {}
        self.map_phys2cafe = {}        
        self.active_cthreads = []        
        self.sects_found = odict() # holds 'section':'linenumber' pairs
        self.checkpoints = odict()
        self.last_checkpoint = None
        self.sects_search = [r'Processor Mode encoding legend:', r'Thread.[0-9]+.Instrs', r'Thread.[0-9]+.Ordered.Access.List', r'//.We.are.in.final.completion.code,.lots.of.specialized.stuff.to.do', r'The.SMM.Setup/Completion.code', r'Thread.[0-9]+.Prior.access.generation.methods', r'Usage.Report:', r'accesses.broken.down.by', r'Alignment.Summary', r'Split.Summary', r'MTRR.Info', r'Thread.0.[eE]xception', r'This.is.the.code.where.all.random.SMIs.on.thread.[0-9]+.go', r'STRESSOR_DEBUG_INFO_BLOCK', r'Stressor.Debug.Info.Setup.Thread.[0-9]+', r'Thread.[0-9]+.Memory.Stressor.setup.code', r'This.is.the.SMM.handler.for.thread.[0-9]+', r'Stressor.Service:', r'stressors.generic.debug.handlers', r'default.stressor.handler', r'This.is.the.fault.handler.that.is.used.when.a.fault.is.encountered.in', r'SIPIBlock.Info', r'Thread.[0-9]+.Setup.Code.Info', r'PostSi.Debug.Thread.Assignment.Summary', r'Thread.[0-9]+.completion.code.location.info', r'We.have.to.send.APIC.messages.a.lot.in.the.SMM.code\...This.code.handles.xapic/legacy.apic.via.the.assembly', r'This.is.the.code.where.all.threads.except.the.one.that.sends.the.mailbox.signal.will.end', r'//.These.are.the.MCA.info.dump.blocks', r'External.Event.Setup.Info:', r'WINDOW.SUMMARY', r'DECODING.DEBUG.INFO.EVENTS.MEMORY', r'SMM.ENABLING/DISABLING.INFORMATION', r'Power.Management.Debug.Information', r'ACModule.Debug.Information', r'Thermal.debug.information:', r'\-b_internal.Cafe', r'\-workarounds', r'This.is.the.code.where.all.threads.except.the.one.that.sends.the.mailbox.signal']
        self.parse() # parse the report file we've been given
                
        
    def parse(self):
        """Parse all the data from found in the file pointed to be filename"""
        if os.path.exists(self.picklefilename):
            try:
                stime = time.time()
                self.read_pickle()
                etime = time.time()
                print 'Pickle load time: %0.02f'%(etime-stime)
                return
            except:
                import traceback
                traceback.print_exc()
                print "Loading pickle failed...falling back on parsing manually"                
        # Do all the heavy parsing work
        stime = time.time()
        filedata = open(self.filename).readlines()
        self.parseCafeMap(filedata)
        self.parseInstructions(filedata)
        etime = time.time()
        print 'Parse time was: %0.02f'%(etime-stime)
        # now write pickle
        stime = time.time()
        self.write_pickle()
        etime = time.time()
        print 'Pickle write time: %0.02f'%(etime-stime)

    
    def parseCafeMap(self,filedata):
        """
        :param filedata: readlines data from the report file"
        """
        # reinitialize these variables
        self.map_cafe2apic = {}
        self.map_apic2cafe = {}
        self.map_cafe2phys = {}
        self.map_phys2cafe = {}
        self.active_cthreads = []  
        
        self.sects_found = odict() # holds 'section':'linenumber' pairs
        self.sects_search = [r'Processor Mode encoding legend:', r'Thread.[0-9]+.Instrs', r'Thread.[0-9]+.Ordered.Access.List', r'//.We.are.in.final.completion.code,.lots.of.specialized.stuff.to.do', r'The.SMM.Setup/Completion.code', r'Thread.[0-9]+.Prior.access.generation.methods', r'Usage.Report:', r'accesses.broken.down.by', r'Alignment.Summary', r'Split.Summary', r'MTRR.Info', r'Thread.0.[eE]xception', r'This.is.the.code.where.all.random.SMIs.on.thread.[0-9]+.go', r'STRESSOR_DEBUG_INFO_BLOCK', r'Stressor.Debug.Info.Setup.Thread.[0-9]+', r'Thread.[0-9]+.Memory.Stressor.setup.code', r'This.is.the.SMM.handler.for.thread.[0-9]+', r'Stressor.Service:', r'stressors.generic.debug.handlers', r'default.stressor.handler', r'This.is.the.fault.handler.that.is.used.when.a.fault.is.encountered.in', r'SIPIBlock.Info', r'Thread.[0-9]+.Setup.Code.Info', r'PostSi.Debug.Thread.Assignment.Summary', r'Thread.[0-9]+.completion.code.location.info', r'We.have.to.send.APIC.messages.a.lot.in.the.SMM.code\...This.code.handles.xapic/legacy.apic.via.the.assembly', r'This.is.the.code.where.all.threads.except.the.one.that.sends.the.mailbox.signal.will.end', r'//.These.are.the.MCA.info.dump.blocks', r'External.Event.Setup.Info:', r'WINDOW.SUMMARY', r'DECODING.DEBUG.INFO.EVENTS.MEMORY', r'SMM.ENABLING/DISABLING.INFORMATION', r'Power.Management.Debug.Information', r'ACModule.Debug.Information', r'Thermal.debug.information:', r'\-b_internal.Cafe', r'\-workarounds', r'This.is.the.code.where.all.threads.except.the.one.that.sends.the.mailbox.signal']        
        _log.result("Searching for thread assignment table...\n")
        parsing=False
        for line in filedata:
            # if we haven't found line out start line yet start stage one
            if line.startswith("PostSi Debug Thread Assignment"):
                parsing = True
            elif parsing==False: # skip all lines until parsing is on
                continue
            if line.strip()=="": # if empty line is hit while we are parsing, then stop
                break 
            # ok, we're parsing do our regex
            match = re.search("(\d+)\s+(.*)\s+(\w+).*\[\s*(\d+)\]\s*\w*",line)
            if match==None:
                continue # if we didn't match, just go one
            physthread = int(match.group(1))
            apicid = int(match.group(3),16)
            cafethread = int(match.group(4))
            self.map_cafe2apic[cafethread]=apicid
            self.map_apic2cafe[apicid]=cafethread
            self.map_cafe2phys[cafethread]=physthread
            self.map_phys2cafe[physthread]=cafethread
            if match.group(0).count("ACTIVE"): # store off that this thread is active
                self.active_cthreads.append(cafethread)
        # sort this just for the heck of it...there will be a day
        # where we will want to make sure this was in some sort of order...
        self.active_cthreads.sort()
        if len(self.map_cafe2apic.keys())==0:
            _log.result("Could not find/parse thread assignment table\n")
            
            
    def _parseCheckpoints(self,line):
        """only works as part of parseInstructions"""
        # first check for checkpoint header:
        match = self.checkpoint_re.search(line)
        if match is not None:
            # checkpoint header found, save off checkpoint info
            cthread,cs,checkname= match.groups()
            self.last_checkpoint = odict()
            self.last_checkpoint.thread = cthread
            cs = int(cs,16)
            self.last_checkpoint.cs = cs if cs !=0 else 0x10
            self.last_checkpoint.checkname = checkname 
            return True
    
        match = self.handler_re.search(line)
        if match is None: # format for these two are the same
            match = self.misc_sect_re.search(line)
        if match is not None:
            # checkpoint header found, save off checkpoint info
            cthread,cs,checkname= match.groups()
            self.last_checkpoint = odict()
            self.last_checkpoint.thread = cthread
            cs = int(cs,16)
            self.last_checkpoint.cs = cs if cs !=0 else 0x10
            self.last_checkpoint.checkname = checkname 
            return True

        if self.last_checkpoint==None:
            # nothing we can do if we haven't seen a checkpoint...
            return False
        
        # Now a header...see if it fixed code instr
        match = self.fixed_code_re.search(line)
        if match is not None:
            cthread,eip,lip,pip,mtype,mode,instruction = match.groups()
            instr = Instruction()
            instr.instruction = instruction
            # convert to hex
            instr.thread = int(cthread)          
            instr.cs = self.last_checkpoint.cs 
            instr.rip = instr.PA = instr.LA =  int(eip,16)
            instr.comment = ""
            instr.instr_bytes = ""
            instr.PA = int(pip,16)
            instr.recipe_info = self.last_checkpoint.checkname
            self.instrs_by_LA[instr.LA]=instr
            self.instrs_by_cs_rip[(instr.cs,instr.rip)]=instr
            # we have to store in this random by thread due to how the pickling works...
            self.random_instrs_by_thread[instr.thread].append(instr)
            # return checkpoint if we are in one...
            return True
        
        # safety measure in case our RE fails, go for simple
        if line.count("CheckPointNum"):
            self.last_checkpoint = None
            return True
        
        # not matches found
        return False
        
           
    def parseInstructions(self,filedata):
        """
        parses report file for all the instructions
        currently expected to only be called by the parse() function        
        """
         
        
        _log.result("Parsing report file for instructions...\n")

        # taken right out of the quark report file parser
        #regex for getting the instruction information in random/handler code
        #Thread Instr#  CS:rip                LA                 GPA                PA                 MA   Mode   Instr/Mem                  Access Size           Iter   Fault[iter](id)   Misc. Information  Recipe
        #[0]    2079    2780:000020d372101716 0x000020d372101716 0x0000000014b01716 0x0000000014b01716 WT   6D---  MOV AX,  [EDI]              8                     0      GP_13[1](0x1)     dasas_dasas        Handler[6] Rand(123) WindowID(0)
        instr_info_extract = re.compile(r"""
                                            ^\[([0-9a-fA-Fx]+)\]\s*                           #thread number
                                            (\d+)\s+                                          #iteration
                                            ([0-9a-fA-Fx]+):                                  #cs address
                                            ([0-9a-fA-Fx]+)\s+                                #rip address
                                            0x([0-9a-fA-Fx]+)\s+                              #LA
                                            0x([0-9a-fA-Fx]+)\s+                              #GPA
                                            0x([0-9a-fA-Fx]+)\s+                              #PA
                                            ([a-zA-Z0-9]+)\s+                                 #memory access type
                                            ([a-zA-Z0-9-$]+)\s+                               #processor mode
                                            ((?:\ ?[a-zA-Z0-9\[\]\{\}\:\,\*\+\_\/=])*)\s+     #instruction
                                            (?:;([\sa-fx0-9]*);)?\s*                          #instr bytes
                                            (?://*(.*)/*/)?\s*                                # comment block                                                                                        
                                            (\d+)\s+                                          #iter
                                            (\w+\[\d+\]\([a-fA-F0-9xX]+\)\+?)?\s+             #Fault[iter][id]
                                            #([\w\ \,]*)\s+                                    #misc information
                                            #(Handler\[\w+\])?\s*                              #handler info
                                            #(Branch_Shadow\([a-f0-9x]+\))?\s*                 #branch shadow
                                            #([\w\(\)\/0-9]+\(\d+\))?\s*                       #recepie info
                                            #(?:WindowID\((\d+)\))?\s*                         #windowID info
                                            (.*)                                              #any extra info
                                            \s*$                                              #extra white space
                                            """, re.X|re.I)
        setupcomplete = re.compile(r"""
                                            ^\[([0-9a-fA-Fx]+)\]\s*                           #thread number
                                            0x([0-9a-fA-Fx]+)\s+                              #LA
                                            0x([0-9a-fA-Fx]+)\s+                              #GPA
                                            0x([0-9a-fA-Fx]+)\s+                              #PA
                                            ([a-zA-Z0-9]+)\s+                                 #memory access type
                                            ([a-zA-Z0-9-$]+)\s+                               #processor mode
                                            ((?:\ ?[a-zA-Z0-9\[\]\{\}\:\,\*\+\_\/=])*)\s+     #instruction
                                            #(?:;([\sa-fx0-9]*);)?\s*                          #instr bytes
                                            (?://*(.*)/*/)?\s*                                # comment block                                                                                        
                                            #(\d+)\s+                                          #iter
                                            #(\w+\[\d+\]\([a-fA-F0-9xX]+\)\+?)?\s+             #Fault[iter][id]
                                            #([\w\ \,]*)\s+                                    #misc information
                                            #(Handler\[\w+\])?\s*                              #handler info
                                            #(Branch_Shadow\([a-f0-9x]+\))?\s*                 #branch shadow
                                            #([\w\(\)\/0-9]+\(\d+\))?\s*                       #recepie info
                                            #(?:WindowID\((\d+)\))?\s*                         #windowID info
                                            (.*)                                              #any extra info
                                            \s*$                                              #extra white space
                                            """, re.X|re.I)
        self.random_instrs_by_thread = {}
        self.instrs_by_cs_rip = {}
        self.instrs_by_LA = {}
        previnstr = None
        #setupcomplete = r'^\[0\]...0x'
        for linenumber,line in enumerate(filedata):
            # check for instructions since that is what we predominantly have                
            match = re.search(instr_info_extract,line)
            match2 = re.search(setupcomplete, line)
            if match==None:
                if match2 == None:
                    # not a random instruction, check for fixed code:
                    if self._parseCheckpoints(line):
                        continue   
                                                        
                    # not fixed code...check for some section headers
                    sect_found = False
                    for check in self.sects_search:
                        matcher = re.search(check,line)  
                        if matcher==None:
                            continue
                        # This if statement was added for one particular case in the report file that needed more information to make sense in the log file
                        linetemp1 = "This is the fault handler that is used when a fault is encountered in"                    
                        if line[0:-1] == linetemp1:
                            linetemp2 = line[0:-1] + " the setup code or the completion code"
                            self.sects_found[linetemp2] = linenumber+1
                            sect_found = True
                            break
                        else:
                            self.sects_found[line[0:-1]] = linenumber+1
                            sect_found = True
                            break
                    # done with our other checking on to the next line
                    continue

            if linenumber%1000==0:
                sys.stdout.write(".")
            i=1
            if match2 != None:
                instr = Instruction()
                instr.next_instr = None # default to be filled in next time through loop
                tempX = match2.group(i)
                if tempX == 'X' or tempX == 'x':
                    instr.thread = int(999);i+=1
                else:
                    instr.thread = int(match2.group(i));i+=1
                # if we have a previous instruction and it belongs to same thread
                if previnstr != None and previnstr.thread==instr.thread:
                    previnstr.next_instr=weakref.proxy(instr)
                    instr.prev_instr=weakref.proxy(previnstr)
                else:
                    instr.prev_instr=None
                # save off this new instr as the prev instruction
                previnstr = instr
                # on with saving off our data...                
                instr.LA = int(match2.group(i),16)       ;i+=1
                try:
                    instr.GPA = int(match2.group(i),16)
                except: # sometimes its not valid...
                    instr.GPA = None
                i+=1
                try:
                    instr.PA = int(match2.group(i),16)
                except:
                    instr.PA = None
                i+=1
                instr.access_type = match2.group(i)  ;i+=1 #8
                instr.processor_mode = match2.group(i);i+=1 #9
                instr.instruction = match2.group(i)  ;i+=1 #10
                # set to empty string instead of None, if no comment
                instr.comment = match2.group(i) if match2.group(i) is not None else ""
                i+=1
                #instr.misc = match.group(i)         ;i+=1 # 16
                #instr.handler = match.group(i)      ;i+=1 # 17
                #instr.branch_shadow = match.group(i);i+=1 # 18
                text = match2.group(i).split(); i+=1 #
                text = [t.strip() for t in text]
                text = ";".join(text)
                instr.recipe_info = text
                #instr.recipe_info = match.group(i)  ;i+=1 # 19
                #instr.windowid = match.group(i)     ;i+=1 # 20
                #instr.extra = match.group(i)        ;i+=1 # 21

                # save instruction in list by thread
                if not self.random_instrs_by_thread.has_key(instr.thread):
                    self.random_instrs_by_thread[instr.thread] = []  
                self.random_instrs_by_thread[instr.thread].append(instr)
                # hopefully this does not add too much memory...
                #self.instrs_by_cs_rip[(instr.cs,instr.rip)] = instr
                self.instrs_by_LA[instr.LA] = instr
            
            else:
                instr = Instruction()
                instr.next_instr = None # default to be filled in next time through loop
                instr.thread = int(match.group(i));i+=1
                # if we have a previous instruction and it belongs to same thread
                if previnstr != None and previnstr.thread==instr.thread:
                    previnstr.next_instr=weakref.proxy(instr)
                    instr.prev_instr=weakref.proxy(previnstr)
                else:
                    instr.prev_instr=None
                # save off this new instr as the prev instruction
                previnstr = instr
                # on with saving off our data...                
                instr.iteration = match.group(i);i+=1
                instr.cs = int(match.group(i),16)     ;i+=1
                instr.rip = int(match.group(i),16)    ;i+=1
                instr.LA = int(match.group(i),16)       ;i+=1
                try:
                    instr.GPA = int(match.group(i),16)
                except: # sometimes its not valid...
                    instr.GPA = None
                i+=1
                try:
                    instr.PA = int(match.group(i),16)
                except:
                    instr.PA = None
                i+=1
                instr.access_type = match.group(i)  ;i+=1 #8
                instr.processor_mode = match.group(i);i+=1 #9
                instr.instruction = match.group(i)  ;i+=1 #10 
                #instr.access_size = match.group(i)  ;i+=1 # 11
                instr.instr_bytes = match.group(i)  ;i+=1 # 12
                # set to empty string instead of None, if no comment
                instr.comment = match.group(i) if match.group(i) is not None else "" # 13
                i+=1 
                instr.iter = match.group(i)         ;i+=1 # 14
                instr.fault = match.group(i)        ;i+=1 # 15
                #instr.misc = match.group(i)         ;i+=1 # 16
                #instr.handler = match.group(i)      ;i+=1 # 17
                #instr.branch_shadow = match.group(i);i+=1 # 18
                text = match.group(i).split(); i+=1 #
                text = [t.strip() for t in text]
                text = ";".join(text)
                instr.recipe_info = text
                #instr.recipe_info = match.group(i)  ;i+=1 # 19
                #instr.windowid = match.group(i)     ;i+=1 # 20
                #instr.extra = match.group(i)        ;i+=1 # 21

                # save instruction in list by thread
                if not self.random_instrs_by_thread.has_key(instr.thread):
                    self.random_instrs_by_thread[instr.thread] = []  
                self.random_instrs_by_thread[instr.thread].append(instr)
                # hopefully this does not add too much memory...
                self.instrs_by_cs_rip[(instr.cs,instr.rip)] = instr
                self.instrs_by_LA[instr.LA] = instr
        #import pdb;pdb.set_trace()
        sys.stdout.write("\n")        
        
    def getinstr(self,cs,rip):
        """return the instruction object for this cs:rip"""
        return self.instrs_by_cs_rip.get((cs,rip),None)
    
    def getinstrLA(self,lip):
        """return the instruction object for this lip"""
        return self.instrs_by_LA.get(lip, None)
    
    def get_rand_instrs(self,cafethread=None):
        """returns the random instruction list for the specified thread
        :param cafethread: can be used to get just one thread
        """
        if cafethread is not None:
            return self.random_instrs_by_thread[cafethread]
        else:
            return self.random_instrs_by_thread
        
    def write_pickle(self):
        pickleable={}
        for thread,instrs in self.random_instrs_by_thread.items():
            pickleable[thread]=[]
            for i in instrs:
                nexti = copy(i)
                nexti.next_instr = None
                nexti.prev_instr = None
                pickleable[thread].append(nexti)
        #import multiprocessing
        # kick off process to do this and go back to user...turns out this is slower than just doing the job
        # but watch out for MP systems, at that point it may make sense to change this....
        #p = multiprocessing.Process(target=_mt_pickler, args=(self.filename+".pickle",pickleable)
        #p.start()
        
        # SAVE BACKUP of instructions.....b/c we are going to tweak pointer
        backup_random = self.random_instrs_by_thread
        backup_by_ip = self.instrs_by_cs_rip   
        backup_by_lip = self.instrs_by_LA
        try:
            self.random_instrs_by_thread = pickleable
            del self.instrs_by_cs_rip
            del self.instrs_by_LA
            pfile = open(self.picklefilename,"wb")
            pstr = cPickle.dumps(self.__dict__, cPickle.HIGHEST_PROTOCOL)
            zstr = zlib.compress(pstr,zlib.Z_BEST_COMPRESSION)
            pfile.write(zstr)
        #    pickler = cPickle.Pickler(pfile,cPickle.HIGHEST_PROTOCOL)
        #    pickler.dump( self.__dict__ )
        finally:
            self.random_instrs_by_thread = backup_random
            self.instrs_by_cs_rip = backup_by_ip
            self.instrs_by_LA = backup_by_lip
        
    def read_pickle(self):
        #self.__dict__ = cPickle.load(open(self.filename+".pickle","rb"))
        pfile = open(self.picklefilename,"rb")
        zstr = pfile.read()
        pstr = zlib.decompress(zstr)
        self.__dict__ = cPickle.loads(pstr)
        
        self.instrs_by_cs_rip = {}
        self.instrs_by_LA = {}
        for instrs in self.random_instrs_by_thread.values():
            previnstr = instrs[0]
            try:
                self.instrs_by_cs_rip[(previnstr.cs,previnstr.rip)]=previnstr              
            except:
                pass
            self.instrs_by_LA[previnstr.LA] = previnstr
            for i in instrs[1:]:
                previnstr.next_instr = weakref.proxy(i)
                i.prev_instr = weakref.proxy(previnstr)
                try:
                    self.instrs_by_cs_rip[(i.cs,i.rip)]=i
                except:
                    pass
                self.instrs_by_LA[i.LA] = i
                previnstr = i    
        # add in the checkpoints to the instrs by cs rip
        for checkpoints in self.checkpoints.values():
            for checkp in checkpoints.values():
                self.instrs_by_cs_rip[(checkp.cs,checkp.rip)]=checkp
                self.instrs_by_LA[checkp.LA]=checkp
        return



def test():
    rpt = r"\\socore037\c$\SVShare\Run\krpatter\10179\Regenerate.Test\FMR_FH_NA_1_VER_HSX_71.7_010_GRAVY_HSX_SERVER_BASIC_SOSGEM156_2100_265-55bcbe6b_r0.rpt"
    return ReportFile(rpt)

if __name__=="__main__":
    rpt = test()
