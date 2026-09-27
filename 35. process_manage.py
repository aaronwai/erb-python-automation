import psutil
import subprocess
import signal
import os
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class ProcessManager:
    """跨平台程序管理類"""
    def __init__(self):
        self.monitored_processes: Dict[int, subprocess.Popen] = {}

    def list_processes(self, sort_by='memory', limit=20) -> List[Dict]:
        """列出系統程序，修正cpu_percent初始為0問題"""
        processes = []
        proc_list = list(psutil.process_iter(['pid', 'name', 'username',
                                             'memory_percent', 'memory_info',
                                             'status', 'create_time']))
        # 第一次採樣，預熱CPU百分比
        for p in proc_list:
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(0.1)
        # 第二次採樣
        for proc in proc_list:
            try:
                info = proc.info
                info["cpu_percent"] = proc.cpu_percent(interval=None)
                info['memory_mb'] = round(info['memory_info'].rss / (1024**2), 2) if info['memory_info'] else 0
                info['create_time_str'] = datetime.fromtimestamp(info['create_time']).isoformat()
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 排序
        if sort_by == 'memory':
            processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        elif sort_by == 'cpu':
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        elif sort_by == 'name':
            processes.sort(key=lambda x: x['name'] or '')
        return processes[:limit]

    def find_process(self, name_pattern: str, use_regex: bool = False) -> List[Dict]:
        """查找程序，支援簡單字串或regex匹配，保護cmdline=None"""
        matching = []
        pattern_obj = re.compile(name_pattern, re.IGNORECASE) if use_regex else None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                p_name = proc.info['name'].lower()
                match = False
                if use_regex:
                    match = bool(pattern_obj.search(proc.info['name']))
                else:
                    match = name_pattern.lower() in p_name
                if match:
                    cmd = proc.info['cmdline']
                    cmd_str = ' '.join(cmd) if cmd else ''
                    matching.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmd_str
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return matching

    def kill_process(self, pid: int, force: bool = False, timeout: int =3) -> bool:
        """終止程序，加入pid合法性檢查"""
        if pid <= 0:
            print(f"無效PID {pid}")
            return False
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
                print(f"強制終止程序 PID {pid}")
            else:
                proc.terminate()
                print(f"請求終止程序 PID {pid}")
            gone, alive = psutil.wait_procs([proc], timeout=timeout)
            if proc in alive:
                proc.kill()
                print(f"程序未響應，已強制終止 PID {pid}")
            # 從本地追蹤清單移除
            self.monitored_processes.pop(pid, None)
            return True
        except psutil.NoSuchProcess:
            print(f"程序不存在: PID {pid}")
            self.monitored_processes.pop(pid, None)
            return False
        except Exception as e:
            print(f"終止失敗 PID {pid}: {str(e)}")
            return False

    def start_process(self, command: List[str],
                     cwd: Optional[str] = None,
                     env: Optional[Dict] = None) -> Optional[int]:
        """啟動子程序，保留Popen物件方便後續管理，非阻塞pipe"""
        try:
            merged_env = {**os.environ,** env} if env else None
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=merged_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.monitored_processes[process.pid] = process
            print(f"已啟動程序 PID {process.pid}: {' '.join(command)}")
            return process.pid
        except Exception as e:
            print(f"啟動失敗: {str(e)}")
            return None

    def get_subproc_output(self, pid:int) -> Tuple[Optional[str], Optional[str]]:
        """讀取已追蹤子程序的stdout/stderr"""
        p = self.monitored_processes.get(pid)
        if not p:
            return None, None
        out, err = p.communicate()
        return out, err

    def monitor_process(self, pid: int, duration: int = 60,
                       interval: int = 5) -> List[Dict]:
        """監控單一PID資源，修正cpu_percent阻塞問題"""
        snapshots = []
        try:
            proc = psutil.Process(pid)
            proc.cpu_percent(interval=None)
            start_ts = time.time()
            while time.time() - start_ts < duration:
                snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': proc.cpu_percent(interval=None),
                    'memory_percent': proc.memory_percent(),
                    'memory_mb': round(proc.memory_info().rss / (1024**2), 2),
                    'num_threads': proc.num_threads(),
                    'status': proc.status()
                }
                snapshots.append(snapshot)
                time.sleep(interval)
        except psutil.NoSuchProcess:
            print(f"程序已結束: PID {pid}")
        except Exception as e:
            print(f"監控異常: {str(e)}")
        return snapshots

    def get_service_status(self, service_name: str) -> Dict:
        """跨平台服務狀態查詢 (systemd / launchctl / Windows sc)"""
        os_name = platform.system()
        try:
            if os_name == "Linux":
                result = subprocess.run(
                    ['systemctl', 'status', service_name],
                    capture_output=True, text=True, timeout=10
                )
                is_active = 'Active: active (running)' in result.stdout
                return {
                    'name': service_name,
                    'platform': os_name,
                    'is_active': is_active,
                    'raw': result.stdout if result.returncode ==0 else result.stderr
                }
            elif os_name == "Darwin":
                result = subprocess.run(
                    ["launchctl", "list", service_name],
                    capture_output=True, text=True, timeout=10
                )
                is_active = result.returncode == 0
                return {
                    'name': service_name,
                    'platform': os_name,
                    'is_active': is_active,
                    'raw': result.stdout
                }
            elif os_name == "Windows":
                result = subprocess.run(
                    ["sc", "query", service_name],
                    capture_output=True, text=True, timeout=10
                )
                is_active = "STATE: 4 RUNNING" in result.stdout
                return {
                    'name': service_name,
                    'platform': os_name,
                    'is_active': is_active,
                    'raw': result.stdout
                }
            else:
                return {"name":service_name, "error":f"平台 {os_name} 不支援服務查詢"}
        except Exception as e:
            return {'name': service_name, 'error': str(e)}

    def control_service(self, service_name: str, action: str) -> bool:
        """跨平台服務控制 start/stop/restart/enable"""
        valid_actions = ['start', 'stop', 'restart', 'enable', 'disable']
        if action not in valid_actions:
            print(f"無效操作: {action}")
            return False
        os_name = platform.system()
        cmd = None
        try:
            if os_name == "Linux":
                cmd = ['systemctl', action, service_name]
            elif os_name == "Darwin":
                map_act = {"start":"bootstrap", "stop":"bootout", "restart":"kickstart"}
                if action in map_act:
                    cmd = ["launchctl", map_act[action], service_name]
                else:
                    print(f"macOS launchctl 不支援 {action}")
                    return False
            elif os_name == "Windows":
                map_act = {"start":["start"], "stop":["stop"], "restart":["stop","start"]}
                if action not in map_act:
                    print(f"Windows sc 不支援 {action}")
                    return False
                for subcmd in map_act[action]:
                    r = subprocess.run(["sc", subcmd, service_name], capture_output=True, text=True, timeout=30)
                    if r.returncode !=0:
                        print(f"{subcmd}失敗: {r.stderr}")
                        return False
                return True
            if not cmd:
                print(f"平台 {os_name} 不支援服務控制")
                return False
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode ==0
            print(f"服務 {service_name} {action}: {'成功' if success else '失敗'}")
            if not success:
                print(f"stderr: {result.stderr}")
            return success
        except Exception as e:
            print(f"服務操作異常: {str(e)}")
            return False

# 使用示例
if __name__ == "__main__":
    pm = ProcessManager()
    # 列出資源最高程序
    print("資源使用最高程序：")
    procs = pm.list_processes(sort_by='memory', limit=10)
    for p in procs:
        print(f"PID {p['pid']:6d} | {p['name']:18s} | CPU: {p['cpu_percent']:5.1f}% | RSS: {p['memory_mb']:8.2f} MB")

    print("\n查找 python 程序：")
    python_procs = pm.find_process("python")
    for p in python_procs:
        print(f"PID {p['pid']}: {p['cmdline'][:100]}")

    # 監控範例
    # snapshots = pm.monitor_process(1234, duration=30, interval=2)
