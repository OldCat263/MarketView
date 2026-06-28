import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Test: strip all suffixes, test with Tencent
tests = [
    ('105.INLF', 'us105'),
    ('107.SOXS', 'us107'),  
]
# But us105/us107 already failed. Let me check if akshare em works for these
cmd = 'cd /opt/marketview/backend && /usr/local/bin/python311 -c "import akshare as ak; df=ak.stock_us_spot_em(); r=df[df.apply(lambda row: row.astype(str).str.contains(\"105.INLF\").any(),axis=1) | df.apply(lambda row: row.astype(str).str.contains(\"107.SOXS\").any(),axis=1)]; print(r[[\"代码\",\"名称\"]].to_string())" 2>&1'
_, o, _ = ssh.exec_command(cmd)
print('akshare lookup:', o.read().decode(errors='replace')[:500])

# Check what stock_us_spot_em actually returns for a few rows  
_, o, _ = ssh.exec_command('cd /opt/marketview/backend && /usr/local/bin/python311 -c "import akshare as ak; df=ak.stock_us_spot_em(); print(df[[\\\"代码\\\",\\\"名称\\\"]].head(10).to_string())" 2>&1')
print('\nakshare em head:', o.read().decode(errors='replace')[:500])

ssh.close()
