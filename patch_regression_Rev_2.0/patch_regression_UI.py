# -*- coding: utf-8 -*-
"""
Patch regression UI

@author: Carlos Abido
"""
try:
    from tkinter import *  # Python 3.x
    import tkinter as tk
    from tkinter import ttk
    import tkinter.font as tkFont
    from tkinter import filedialog, messagebox
except ImportError:
    from Tkinter import *  # Python 2.x
    import Tkinter as tk
    from Tkinter import ttk
    import Tkinter.font as tkFont
    from Tkinter import filedialog, messagebox

import pdb
import subprocess, sys
import os

#path os the main script.
pathToScript = '%s\\script' % os.getcwd()
allFiles = os.listdir(pathToScript)
for x in allFiles:
    if 'patch_regression_Rev' in x and 'bak' not in x:
        script = '%s\\%s' % (pathToScript, x)

ver = sys.version

# Initial settings
root = tk.Tk()
root.title("PatchRegression UI")
style = ttk.Style()
style.theme_use("clam")
root.geometry("700x450")
root.configure(background='#f0f3f5')
root.resizable(width=False, height=False)
button_font = tkFont.Font(family="FranklinGothic-Book 20 bold", size=12)
root.columnconfigure(2, minsize=100)
header_font = tkFont.Font(family="Arial", size=15, weight="bold")
header_label = tk.Label(root, text="Patch Regression", font=header_font, fg="blue")
header_label.grid(row=0, column=0, columnspan=3, pady=10)

# Variables of the grip entry
bios_path = tk.StringVar()
ucode_path = tk.StringVar()
swconfigs_path = tk.StringVar()
log_path = tk.StringVar()
task_path = tk.StringVar()

# State of checkbuttons
var_bios = tk.BooleanVar() #value=True to auto select checkbutton
var_ucode = tk.BooleanVar()
var_swconfigs = tk.BooleanVar()
var_log = tk.BooleanVar()
var_flash = tk.BooleanVar()
var_hton = tk.BooleanVar()
var_htoff = tk.BooleanVar()
var_copy = tk.BooleanVar()
var_unlock = tk.BooleanVar()
var_delpatch = tk.BooleanVar()
var_task = tk.BooleanVar()

# Help menu
def open_help():
    help_text = '''
This script is to automatically perform Patch regressions

1. Remove old patches stitched in BIOS and stitches new patch
2. Copies ucode and stitched bios to share drive called out in ini file
3. Stitches knobs of each software config and moves to correct share drive 
4. Flash BIOS per software config specified or from swconfig in env var
5. Unlocks station after it has reached F5 or F6 

'-b', '--bios' BIOS path needs to be a full valid path to binary.
                      
'-u', '--ucode' Ucode path needs to be a full valid path to pdb file,
                    
'-sc', '--swconfigs' SwConfig needs to have full path to use user specified knobs.
                     If left blank it will read from ini file.
                        
'-f', '--flash' Argument is used to trigger BIOS flash
                If not used flash feature will be skipped.
                        
'-t', '--task' The Task or software config is used for BIOS flashing.
               If left blank it will be read from SwConfig env var.
               
'-c', '--copy', Argument is used to trigger the copy of both Binary and Patch to share drive
                  
'-ul', '--unlock',help = This argument will unlock the system in automation.,
                    
'-l',  '--log' Log file created for script. User can specify log file full path to be used
               if left blank the file from ini will be used.
                    
'-d', '--delpatch' delete all previous patches in BIOS.
                   if left blank it will update the CPUID from patch,                        
'''
    messagebox.showinfo("Help", help_text)

# Open explorer to select files to import.
def browse_bios():
    bios_path.set(filedialog.askopenfilename())

def browse_ucode():
    ucode_path.set(filedialog.askopenfilename())

def browse_swconfigs():
    swconfigs_path.set(filedialog.askopenfilename())    

def browse_log():
    log_path.set(filedialog.askopenfilename())
    
def browse_task():
    log_path.set(filedialog.askopenfilename())

# Functions to check checkbuttons toggle 
def toggle_bios_path(entry_bios, button_bios):
    if var_bios.get():
        entry_bios.config(state=tk.NORMAL)
        button_bios.config(state=tk.NORMAL)
    else:
        entry_bios.config(state=tk.DISABLED)
        button_bios.config(state=tk.DISABLED)

def toggle_ucode_path(entry_ucode, button_ucode):
    if var_ucode.get():
        entry_ucode.config(state=tk.NORMAL)
        button_ucode.config(state=tk.NORMAL)
    else:
        entry_ucode.config(state=tk.DISABLED)
        button_ucode.config(state=tk.DISABLED)

def toggle_swconfigs_path(entry_swconfigs, button_swconfigs):
    if var_swconfigs.get():
        entry_swconfigs.config(state=tk.NORMAL)
        button_swconfigs.config(state=tk.NORMAL)
    else:
        entry_swconfigs.config(state=tk.DISABLED)
        button_swconfigs.config(state=tk.DISABLED)

def toggle_log_path(entry_log, button_log):
    if var_log.get():
        entry_log.config(state=tk.NORMAL)
        button_log.config(state=tk.NORMAL)
    else:
        entry_log.config(state=tk.DISABLED)
        button_log.config(state=tk.DISABLED)
        
def toggle_task_path(entry_task):
    if var_task.get():
        entry_task.config(state=tk.NORMAL)
    else:
        entry_task.config(state=tk.DISABLED)
        
 # Function to enable flags to the full command path.   
def run_script():
    cmd = ['python', script]
    if var_bios.get():
        cmd.extend(['-b', bios_path.get()])
    if var_ucode.get():
        cmd.extend(['-u', ucode_path.get()])
    if var_swconfigs.get():
        cmd.extend(['-sc', swconfigs_path.get()])
    if var_log.get():
        cmd.extend(['-l', log_path.get()])  
    if var_unlock.get():
        cmd.append('-ul')
    if var_flash.get():
        cmd.append('-f')
    if var_hton.get():
        cmd.append('-hn')    
    if var_htoff.get():
        cmd.append('-hf')
    if var_task.get():
        cmd.extend(['-t', task_path.get()])

    print("Full Command: ",' '.join(cmd)) 
    print('---------------------------------------------------------------------------------------------')
    subprocess.call(cmd)

            
# Design the frame work with checkbuttons, bottons, grid entry.
def main():
    tk.Checkbutton(root, text="Full BIOS path:", variable=var_bios, command=lambda: toggle_bios_path(entry_bios, button_bios), font=button_font).grid(row=1, column=0, sticky=tk.W)
    entry_bios = tk.Entry(root, textvariable=bios_path, state=tk.DISABLED, font=button_font, width=40)
    entry_bios.grid(row=1, column=1)
    button_bios = tk.Button(root, text="Browse", command=browse_bios, font=button_font)
    button_bios.grid(row=1, column=2)

    tk.Checkbutton(root, text="Full Ucode path:", variable=var_ucode, command=lambda: toggle_ucode_path(entry_ucode, button_ucode), font=button_font).grid(row=2, column=0, sticky=tk.W)
    entry_ucode = tk.Entry(root, textvariable=ucode_path, state=tk.DISABLED, font=button_font, width=40)
    entry_ucode.grid(row=2, column=1)
    button_ucode = tk.Button(root, text="Browse", command=browse_ucode, font=button_font)
    button_ucode.grid(row=2, column=2)

    tk.Checkbutton(root, text="SwConfig path:", variable=var_swconfigs, command=lambda: toggle_swconfigs_path(entry_swconfigs, button_swconfigs), font=button_font).grid(row=3, column=0, sticky=tk.W)
    entry_swconfigs = tk.Entry(root, textvariable=swconfigs_path, state=tk.DISABLED, font=button_font, width=40)
    entry_swconfigs.grid(row=3, column=1)
    button_swconfigs = tk.Button(root, text="Browse", command=browse_swconfigs, state=tk.DISABLED, font=button_font)
    button_swconfigs.grid(row=3, column=2)

    tk.Checkbutton(root, text="Log path:", variable=var_log, command=lambda: toggle_log_path(entry_log, button_log), font=button_font).grid(row=4, column=0, sticky=tk.W)
    entry_log = tk.Entry(root, textvariable=log_path, state=tk.DISABLED, font=button_font, width=40)
    entry_log.grid(row=4, column=1)
    button_log = tk.Button(root, text="Browse", command=browse_log, state=tk.DISABLED, font=button_font)
    button_log.grid(row=4, column=2)
    
    tk.Checkbutton(root, text='Flash Bios', variable=var_flash, font=button_font).grid(row=14, column=0, sticky=tk.W)
    tk.Checkbutton(root, text='HT ON', variable=var_hton, font=button_font).grid(row=11, column=0, sticky=tk.W)
    tk.Checkbutton(root, text='HT OFF', variable=var_htoff, font=button_font).grid(row=12, column=0, sticky=tk.W)
    
    tk.Checkbutton(root, text="SwConfig to Flash:", variable=var_task, command=lambda: toggle_task_path(entry_task), font=button_font).grid(row=13, column=0, sticky=tk.W)
    entry_task = tk.Entry(root, textvariable=task_path, state=tk.DISABLED, font=button_font, width=20)
    entry_task.grid(row=13, column=1, sticky=tk.W)
    
    tk.Checkbutton(root, text='Unlock System After Boot', variable=var_unlock, font=button_font).grid(row=17, column=0, sticky=tk.W)
    

    tk.Button(root, text="Run script", command=run_script, font=button_font).grid(row=18, column=1, sticky=tk.S)
    tk.Button(root, text="Help", command=open_help, font=button_font).grid(row=25, column=1, sticky=tk.S)
    root.mainloop()

if __name__ == "__main__":
    print('---------------------------------------------------------------------------------------------')
    print('                                 Patch Regression is running...                              ')
    print('---------------------------------------------------------------------------------------------')
    main()
    
