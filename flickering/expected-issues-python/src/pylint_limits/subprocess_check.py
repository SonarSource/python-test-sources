import subprocess

subprocess.run("exit 1", shell=True)  # [subprocess-run-check]
subprocess.run("exit 1", shell=True, check=False)  # [subprocess-run-check]
subprocess.run("exit 1", shell=True, check=True)

# subprocess.run() # [subprocess-run-check]


proc = subprocess.run("exit 1", shell=True) # False Positive
proc.check_returncode()


import foo
def bar():
    a = 5

