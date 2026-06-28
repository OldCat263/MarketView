"""热修复部署 — 仅推送 main.py + 验证 batch predict"""
import paramiko
import sys, os, time, json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'
REMOTE = '/opt/marketview'
LOCAL = r'd:\服务器ETF'

def run_ssh(ssh, cmd, print_output=True):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    exit_code = stdout.channel.recv_exit_status()
    if print_output:
        if out.strip(): print(out.strip())
        if err.strip(): print('[stderr]', err.strip())
    return out, err, exit_code

def main():
    print('=' * 60)
    print('MarketView 热修复部署 — main.py')
    print('=' * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f'\n🔌 连接 {USER}@{HOST}...')
        ssh.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)
        print('✅ 已连接')

        # Step 1: 推送 main.py
        print('\n【Step 1】推送 backend/main.py')
        local_path = os.path.join(LOCAL, 'backend', 'main.py')
        remote_path = f'{REMOTE}/backend/main.py'
        sftp = ssh.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        size_kb = os.path.getsize(local_path) / 1024
        print(f'  ✅ main.py 已推送 ({size_kb:.1f} KB)')

        # Step 2: 重启
        print('\n【Step 2】重启 marketview')
        run_ssh(ssh, 'systemctl restart marketview')
        time.sleep(3)
        run_ssh(ssh, 'systemctl status marketview --no-pager | head -10')

        # Step 3: 等 40s
        print('\n【Step 3】等待 40s 让所有模块加载就绪...')
        for i in range(40, 0, -5):
            print(f'  剩余 {i}s...')
            time.sleep(5)

        # Step 4: Health check
        print('\n【Step 4】Health Check')
        out, _, _ = run_ssh(ssh, "curl -s http://localhost:8000/api/health", print_output=True)

        # Step 5: Trigger batch predict
        print('\n【Step 5】触发 predict/batch/stock (pool_size=50)')
        out, _, _ = run_ssh(ssh,
            "curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=50'",
            print_output=True)

        # Step 6: 等 15s
        print('\n【Step 6】等待 15s 让 batch 计算完成...')
        time.sleep(15)

        # Step 7: Get rank
        print('\n【Step 7】获取 predict/rank/stock')
        out, _, _ = run_ssh(ssh,
            "curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'",
            print_output=True)

        # 解析结果
        try:
            data = json.loads(out.strip()) if out.strip() else {}
            rank_count = len(data.get('data', []))
            print(f'\n  📊 排名条数: {rank_count}')
            if rank_count > 0:
                print('  ✅ 验证通过 — 有有效排名数据')
            else:
                print('  ⚠️ 排名为空，检查 data 结构')
                print(f'  完整响应 keys: {list(data.keys())}')
        except Exception as e:
            print(f'  ⚠️ JSON 解析失败: {e}')
            print(f'  原始输出前200字: {out[:200]}')

        print('\n' + '=' * 60)
        print('✅ 热修复部署完成')
        print('=' * 60)

    except Exception as e:
        print(f'\n❌ 部署失败: {e}')
        return 1
    finally:
        ssh.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
