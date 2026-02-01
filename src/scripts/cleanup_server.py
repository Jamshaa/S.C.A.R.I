import os
import subprocess
import signal
import time

def kill_port_8000():
    print("🧹 Cleaning up Port 8000...")
    try:
        # Find PIDs
        output = subprocess.check_output('netstat -ano | findstr :8000', shell=True).decode()
        pids = set()
        for line in output.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 5:
                pids.add(parts[-1])
        
        for pid in pids:
            if pid == '0': continue
            print(f"   - Killing PID {pid}")
            try:
                subprocess.run(f'taskkill /F /PID {pid} /T', shell=True, check=False)
            except:
                pass
        
        print("✅ Port 8000 should be clear now.")
        return True
    except subprocess.CalledProcessError:
        print("ℹ️ No processes found on Port 8000.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    kill_port_8000()
