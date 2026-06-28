import paramiko
c=paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(" 43.156.133.37\,username=oot\,password=\Qwe134679\,timeout=10,allow_agent=False,look_for_keys=False)
_,o,_=c.exec_command(\grep -n _stock_prefix\\|_CODE_PREFIX /opt/marketview/backend/main.py\)
print(o.read().decode())
c.close()
