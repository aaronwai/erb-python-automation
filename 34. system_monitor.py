import os
import sys
import platform
import psutil
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import json
import time

class SystemMonitor:
    """系統監控類（psutil）"""
    def __init__(self):
        self.os_type = platform.system()
        self.start_time = datetime.now()
        self._last_snapshot = None
        self._last_snapshot_ts = 0

    def get_system_info(self, cache_seconds: float = 0):
        """
        獲取完整系統資訊快照
        Args:
            cache_seconds: 快取有效期，若上次採樣未超過此時間，直接回傳快取，避免重複阻塞採樣
        """
        now_ts = time.time()
        if cache_seconds > 0 and self._last_snapshot is not None:
            if now_ts - self._last_snapshot_ts < cache_seconds:
                return self._last_snapshot

        info = {
            'basic': self._get_basic_info(),
            'cpu': self._get_cpu_info(),
            'memory': self._get_memory_info(),
            'disk': self._get_disk_info(),
            'network': self._get_network_info(),
            'boot_time': self._get_boot_time()
        }
        self._last_snapshot = info
        self._last_snapshot_ts = now_ts
        return info

    def _get_basic_info(self):
        """基本系統資訊"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.architecture()[0],
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'python_executable': sys.executable
        }

    def _get_cpu_info(self, cpu_interval: float = 0.5):
        """CPU 資訊（縮短interval，可自行調整；None保護）"""
        cpu_freq = psutil.cpu_freq()
        return {
            'physical_cores': psutil.cpu_count(logical=False),
            'total_cores': psutil.cpu_count(logical=True),
            'current_frequency_mhz': cpu_freq.current if cpu_freq else None,
            'max_frequency_mhz': cpu_freq.max if cpu_freq else None,
            'min_frequency_mhz': cpu_freq.min if cpu_freq else None,
            'cpu_percent_per_core': psutil.cpu_percent(percpu=True, interval=cpu_interval),
            'total_cpu_percent': psutil.cpu_percent(interval=cpu_interval),
            'cpu_times': psutil.cpu_times()._asdict()
        }

    def _get_memory_info(self):
        """記憶體資訊"""
        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'virtual': {
                'total_gb': round(virtual.total / (1024**3), 2),
                'available_gb': round(virtual.available / (1024**3), 2),
                'used_gb': round(virtual.used / (1024**3), 2),
                'free_gb': round(virtual.free / (1024**3), 2),
                'percent': virtual.percent,
                'cached_gb': round(getattr(virtual, 'cached', 0) / (1024**3), 2)
            },
            'swap': {
                'total_gb': round(swap.total / (1024**3), 2),
                'used_gb': round(swap.used / (1024**3), 2),
                'free_gb': round(swap.free / (1024**3), 2),
                'percent': swap.percent
            }
        }

    def _get_disk_info(self):
        """磁碟資訊，跳過權限錯誤"""
        disk_info = {
            'partitions': [],
            'io_counters': None
        }
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info['partitions'].append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': usage.percent
                })
            except PermissionError:
                continue
        try:
            io = psutil.disk_io_counters()
            if io:
                disk_info['io_counters'] = {
                    'read_count': io.read_count,
                    'write_count': io.write_count,
                    'read_bytes_gb': round(io.read_bytes / (1024**3), 2),
                    'write_bytes_gb': round(io.write_bytes / (1024**3), 2),
                    'read_time': io.read_time,
                    'write_time': io.write_time
                }
        except Exception:
            pass
        return disk_info

    def _get_network_info(self):
        """網路資訊，識別IPv4 / IPv6"""
        net_io = psutil.net_io_counters()
        net_if_addrs = psutil.net_if_addrs()
        family_map = {2: "IPv4", 10: "IPv6"}
        interfaces = {}
        for name, addrs in net_if_addrs.items():
            interfaces[name] = []
            for addr in addrs:
                interfaces[name].append({
                    'family_code': addr.family,
                    'family_name': family_map.get(addr.family, str(addr.family)),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                })
        return {
            'io_counters': {
                'bytes_sent_mb': round(net_io.bytes_sent / (1024**2), 2),
                'bytes_recv_mb': round(net_io.bytes_recv / (1024**2), 2),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout
            },
            'interfaces': interfaces
        }

    def _get_boot_time(self):
        """系統啟動時間"""
        boot_timestamp = psutil.boot_time()
        boot_time = datetime.fromtimestamp(boot_timestamp)
        uptime = datetime.now() - boot_time
        return {
            'boot_time': boot_time.isoformat(),
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_readable': str(timedelta(seconds=int(uptime.total_seconds())))
        }

    def get_top_processes(self, top_n: int = 5):
        """取得資源消耗前N的程序"""
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                info = proc.info
                mem_mb = info['memory_info'].rss / (1024**2) if info['memory_info'] else 0
                procs.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'cpu_percent': info['cpu_percent'],
                    'rss_mb': round(mem_mb, 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda p: p['cpu_percent'], reverse=True)
        return procs[:top_n]

    def check_alerts(self, info=None, cpu_thresh=90, mem_thresh=90, disk_thresh=85):
        """資源門檻告警"""
        if info is None:
            info = self.get_system_info()
        alerts = []
        if info['cpu']['total_cpu_percent'] > cpu_thresh:
            alerts.append(f"⚠️ CPU 使用率過高: {info['cpu']['total_cpu_percent']}%")
        if info['memory']['virtual']['percent'] > mem_thresh:
            alerts.append(f"⚠️ 記憶體使用率過高: {info['memory']['virtual']['percent']}%")
        for part in info['disk']['partitions']:
            if part['percent'] > disk_thresh:
                alerts.append(f"⚠️ 磁碟 {part['mountpoint']} 使用率過高: {part['percent']}%")
        return alerts

    def print_system_report(self, info=None):
        """列印系統報告"""
        if info is None:
            info = self.get_system_info()
        print("=" * 70)
        print("系統監控報告")
        print("=" * 70)
        print(f"生成時間: {datetime.now().isoformat()}")
        print()
        print("【基本資訊】")
        for key, value in info['basic'].items():
            print(f"  {key}: {value}")
        print("\n【CPU 資訊】")
        cpu = info['cpu']
        print(f"  物理核心: {cpu['physical_cores']}")
        print(f"  邏輯核心: {cpu['total_cores']}")
        print(f"  當前頻率: {cpu['current_frequency_mhz'] or 'N/A'} MHz")
        print(f"  總使用率: {cpu['total_cpu_percent']}%")
        print(f"  各核心使用率: {cpu['cpu_percent_per_core']}")

        print("\n【記憶體資訊】")
        mem = info['memory']['virtual']
        print(f"  總計: {mem['total_gb']} GB")
        print(f"  可用: {mem['available_gb']} GB")
        print(f"  已用: {mem['used_gb']} GB ({mem['percent']}%)")

        print("\n【磁碟資訊】")
        if len(info['disk']['partitions']) == 0:
            print("  無法讀取任何磁碟分割區（權限限制）")
        for part in info['disk']['partitions']:
            print(f"  {part['device']} ({part['mountpoint']}):")
            print(f"    總計: {part['total_gb']} GB，已用: {part['used_gb']} GB ({part['percent']}%)")

        print("\n【網路資訊】")
        net = info['network']['io_counters']
        print(f"  發送: {net['bytes_sent_mb']} MB")
        print(f"  接收: {net['bytes_recv_mb']} MB")

        print("\n【運行時間】")
        print(f"  啟動時間: {info['boot_time']['boot_time']}")
        print(f"  運行時長: {info['boot_time']['uptime_readable']}")

        alerts = self.check_alerts(info)
        if alerts:
            print("\n【告警】")
            for a in alerts:
                print(f"  {a}")
        print("=" * 70)

    def save_system_report(self, filepath="system_report.json"):
        """保存系統報告 JSON"""
        info = self.get_system_info()
        info['generated_at'] = datetime.now().isoformat()
        info['alerts'] = self.check_alerts(info)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        print(f"系統報告已保存: {filepath}")
        return info

    def monitor_continuous(self, interval: int = 5, duration: int = 30):
        """持續監控，每隔interval秒採樣，持續duration秒"""
        print(f"開始持續監控，每 {interval}s 採樣，總共 {duration}s")
        end_time = time.time() + duration
        while time.time() < end_time:
            snap = self.get_system_info(cache_seconds=0)
            self.print_system_report(snap)
            time.sleep(interval)


# 使用示例
if __name__ == "__main__":
    monitor = SystemMonitor()
    # 一次性快照報告
    monitor.print_system_report()
    monitor.save_system_report("system_info.json")

    # 取得高資源程序
    top_procs = monitor.get_top_processes(top_n=5)
    print("\nTop 5 CPU 程序：")
    for p in top_procs:
        print(f"PID {p['pid']:6d} | {p['name']:15s} | CPU: {p['cpu_percent']:5.1f}% | RSS: {p['rss_mb']:.2f} MB")

    # 持續監控範例（取消註解執行）
    # monitor.monitor_continuous(interval=5, duration=20)
