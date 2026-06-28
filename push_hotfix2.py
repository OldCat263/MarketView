import paramiko, json, time

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

def ssh_cmd(cmd, timeout=30):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ssh.close()
    return out, err

print('=== Raw health ===')
out, err = ssh_cmd('curl -s http://localhost:8000/api/health')
print(f'out: {out}')
print(f'err: {err}')

print('\n=== Raw health (verbose) ===')
out, err = ssh_cmd('curl -s http://localhost:8000/api/health?detail=detail')
print(f'out: {out[:2000]}')

print('\n=== systemctl status ===')
out, err = ssh_cmd('systemctl status marketview --no-pager -l')
print(out[:1000])

print('\n=== Try predict batch again ===')
out, err = ssh_cmd('curl -s -X POST "http://localhost:8000/api/predict/batch/stock?pool_size=50"', timeout=60)
print(f'batch: {out}')

print('\n=== Wait 20s then rank ===')
time.sleep(20)
out, err = ssh_cmd('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10"', timeout=30)
print(f'rank: {out[:2000]}')

print('\n=== Check spot data ===')
out, err = ssh_cmd('curl -s "http://localhost:8000/api/spot/stock?limit=3"', timeout=30)
print(f'spot: {out[:500]}')
