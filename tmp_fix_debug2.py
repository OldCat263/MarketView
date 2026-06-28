import paramiko

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

def ssh_cmd(cmd):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, e = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r

print('=== Server logs (full batch related) ===')
r = ssh_cmd('journalctl -u marketview --no-pager -n 100 --output cat')
print(r[-2000:])

print('\n=== Cached file check ===')
r = ssh_cmd('ls -la /opt/marketview/backend/__pycache__/*.pyc 2>/dev/null; ls -la /opt/marketview/backend/*.json 2>/dev/null')
print(r)

print('\n=== Test single score ===')
r = ssh_cmd('cd /opt/marketview && python3 -c "from backend.fetcher.scorer import _percentile_rank; print(_percentile_rank([0.85,0.72,0.91,0.66], \"dummy\")); print(_percentile_rank([{\"a\":1},{\"a\":2},{\"a\":3}], \"a\"))"')
print(f'single_score_test: {r}')

print('DONE')
