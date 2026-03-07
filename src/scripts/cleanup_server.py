import psutil

def kill_port_8000():
    print('🧹 Cleaning up Port 8000...')
    try:
        killed = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                connections = proc.connections()
                for conn in connections:
                    if conn.laddr.port == 8000:
                        print(f"   - Killing process {proc.info['name']} (PID {proc.info['pid']})")
                        proc.kill()
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
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