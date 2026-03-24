import psutil

def kill_port_8000():
    print('🧹 Cleaning up Port 8000...')
    try:
        killed = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = (proc.info['name'] or '').lower()
                if 'python' not in proc_name and 'uvicorn' not in proc_name:
                    continue
                connections = proc.net_connections(kind='inet')
                for conn in connections:
                    if getattr(conn.laddr, 'port', None) == 8000:
                        print(f"   - Stopping process {proc.info['name']} (PID {proc.info['pid']})")
                        proc.terminate()
                        try:
                            proc.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        if killed:
            print('✅ Port 8000 processes terminated.')
        else:
            print('ℹ️ No processes found on Port 8000.')
        return True
    except Exception as e:
        print(f'❌ Error during cleanup: {e}')
        return False
if __name__ == '__main__':
    kill_port_8000()
