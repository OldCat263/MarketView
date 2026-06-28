import paramiko
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

# Show the full _do_batch code from the server
print("=== Full _do_batch ===")
code = run("sed -n '428,462p' /opt/marketview/backend/main.py")
print(code, flush=True)

# Add debug print to _do_batch
print("\n=== Patching _do_batch with debug ===")
patch = '''sed -i '428,462c\\
    def _do_batch():\\
        try:\\
            raw = _cached_get(module)\\
            print(f"[DEBUG batch/{module}] _cached_get raw type={type(raw).__name__} len={len(raw) if raw else 0} start={str(raw)[:100]}", flush=True)\\
            if raw == '"'"'[]'"'"':\\
                _predict_status[cache_key] = {"'"'progress'"'": 0, "'"'total'"'": 0, "'"'status'"'": "'"'no_data'"'"'}\\
                return\\
            spot_data = json.loads(raw)\\
            print(f"[DEBUG batch/{module}] spot_data type={type(spot_data).__name__} len={len(spot_data) if hasattr(spot_data, '"'"'__len__'"'"') else '"'"'N/A'"'"'}", flush=True)\\
            items = spot_data.get('"'"'data'"'"', spot_data) if isinstance(spot_data, dict) else spot_data\\
            print(f"[DEBUG batch/{module}] items type={type(items).__name__} len={len(items) if hasattr(items, '"'"'__len__'"'"') else '"'"'N/A'"'"'}", flush=True)\\
            codes = []\\
            if isinstance(items, list):\\
                for r in items[:pool_size]:\\
                    c = r.get('"'"'代码'"'"', r.get('"'"'交易对'"'"', '"'"''"'"'))\\
                    if c:\\
                        pf = _CODE_PREFIX.get(module)\\
                        codes.append(pf(c) if pf else c)\\
                print(f"[DEBUG batch/{module}] codes extracted: {len(codes)}\\"'"', flush=True)\\
                if codes: print(f"[DEBUG batch/{module}] first codes: {codes[:3]}\\"'"', flush=True)\\
            results = scorer.rank_batch(module, codes, '"'"'1d'"'"', '"'"'quick'"'"', max_workers=5)\\
            print(f"[DEBUG batch/{module}] results: {len(results)}\\'"'"', flush=True)\\
            with _predict_lock:\\
                _predict_cache[cache_key] = {"'"'data'"'": results, "'"'ts'"'": time.time()}\\
            _predict_status[cache_key] = {"'"'progress'"'": len(results), "'"'total'"'": len(codes), "'"'status'"'": "'"'done'"'"'}\\
            with _sse_lock:\\
                for q in _sse_queues.get('"'"'predict'"'"', []):\\
                    try:\\
                        q.put_nowait({"'"'type'"'": "'"'rank_update'"'"', "'"'data'"'": results[:50], "'"'ts'"'": time.time()})\\
                    except queue.Full:\\
                        pass\\
        except Exception as e:\\
            import traceback\\
            print(f"[DEBUG batch/{module}] ERROR: {e}\\"'"', flush=True)\\
            traceback.print_exc()\\
            _predict_status[cache_key] = {"'"'progress'"'": 0, "'"'total'"'": 0, "'"'status'"'": f"'"'error: {e}'"'"'}\\
' /opt/marketview/backend/main.py'''

# Actually, the sed approach is complex and fragile. Let me just test if _cached_get works differently in the running process
# by triggering batch and checking the logs immediately

print("=== Triggering batch with immediate log tail ===")
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=10'")
print(f"Batch response: {batch}", flush=True)

import time
time.sleep(10)

# Check for any debug/error output  
print("\n=== Logs after batch ===")
log = run("journalctl -u marketview --no-pager --since '30 sec ago' -o cat | grep -v 'SettingWithCopyWarning\|pd.to_numeric\|temp_df\|See the caveats\|Try using\|A value\|df\\[col\\]' | tail -30")
print(log, flush=True)

# The real question: does _cached_get work correctly for _do_batch in the running FastAPI process?
# Let me write a test that runs INSIDE the FastAPI process by using a simple API endpoint trick
# Actually the simplest test: the health endpoint calls _cached_get and it works. Let me check 
# if there's something special about how predict_batch calls _cached_get

print("\n=== Checking if predict_batch code matches expect ===")
code = run("sed -n '420,470p' /opt/marketview/backend/main.py | head -35")
print(code, flush=True)

ssh.close()
