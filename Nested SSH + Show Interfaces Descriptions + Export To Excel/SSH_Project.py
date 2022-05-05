import paramiko
import textfsm
import tempfile
import pandas as pd

selx = input("Tampa or Sparta Shiva? 'T' or 's'")  
if selx.lower() == 't':
  ip = "24.95.243.21"
elif selx.lower() == 's':
  ip =  "47.44.239.21" 
un = input("Enter JumpServer Username")
pw = input("Enter JumpServer Password")
ip1 = input("Enter Target Device IP")
un1 = input("Enter Target Device Username")
pw1 = input("Enter Target Device Password")


template_juniper_junos_show_interfaces = '''Value Required INTERFACE (\S+)
Value LINK_STATUS (\w+)
Value ADMIN_STATE (\S+)
Value HARDWARE_TYPE (\S+)
Value DESCRIPTION (\w+.*)
Value DESTINATION (\S+)
Value LOCAL (\S+)
Value MTU (\d+|Unlimited)

Start
  ^\s*\S+\s+interface -> Continue.Record
  ^Physical\s+interface:\s+${INTERFACE},\s+${ADMIN_STATE},\s+Physical\s+link\s+is\s+${LINK_STATUS}
  ^.*Description:\s+${DESCRIPTION}
  ^.*ype:\s+${HARDWARE_TYPE},.*MTU:\s+${MTU}.*
  ^\s+Logical\s+interface\s+${INTERFACE}
  ^.*Destination:\s+${DESTINATION},\s+Local:\s+${LOCAL},.*
  ^\s*$$
  ^{master:\d+}
''' 

def parse_textfsm(template, output):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    with open(tmp.name, "w") as f:
        f.write(template)

    with open(tmp.name, "r") as f:
        fsm = textfsm.TextFSM(f)
        fsm_results = fsm.ParseText(output)
        parsed = [dict(zip(fsm.header, row))for row in fsm_results]

    return parsed

def cmd(command):      
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=un, password=pw)

    vmtransport = ssh.get_transport()
    dest_addr = (ip1, 22)
    local_addr = (ip, 22)
    vmchannel = vmtransport.open_channel("direct-tcpip", dest_addr, local_addr)

    sh1 = paramiko.SSHClient()
    sh1.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    sh1.connect(ip1, username = un1, password = pw1, sock=vmchannel)

    stdin, stdout, stderr = sh1.exec_command(command)
    stdin.close()
    output = stdout.read()
    output_err = stderr.read()

    if output_err:
        return output_err.decode('utf-8')
    else:
        return output.decode('utf-8')



output_t0 = cmd(command = 'show interfaces')
parsed_t0 = parse_textfsm(template = template_juniper_junos_show_interfaces, output = output_t0)


df = pd.DataFrame(parsed_t0)
df.to_excel("MXOutput.xlsx", index=False)









