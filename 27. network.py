import requests
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from collections import deque
import threading
from typing import Optional, Dict, Any

class NetworkMonitor:
    """網絡監控與告警系統"""
    def __init__(self, check_interval=60):
        self.check_interval = check_interval
        self.targets = []
        self.history = {}
        self.alerts = []
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_target(self, name, url, expected_status=200,
                   timeout=10, alert_threshold=3, history_max=100, headers=None):
        """添加監控目標"""
        with self._lock:
            self.targets.append({
                'name': name,
                'url': url,
                'expected_status': expected_status,
                'timeout': timeout,
                'alert_threshold': alert_threshold,
                'failure_count': 0,
                'alert_fired': False,
                'headers': headers or {}
            })
            self.history[name] = deque(maxlen=history_max)
        print(f"已添加監控目標: {name} ({url})")

    def check_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """檢查單個目標"""
        start_time = time.time()
        try:
            response = requests.get(
                target['url'],
                timeout=target['timeout'],
                allow_redirects=False,
                headers=target['headers']
            )
            elapsed = time.time() - start_time
            result = {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'response_time': elapsed,
                'success': response.status_code == target['expected_status'],
                'error': None
            }
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            result = {
                'timestamp': datetime.now().isoformat(),
                'status_code': None,
                'response_time': elapsed,
                'success': False,
                'error': 'Timeout'
            }
        except requests.exceptions.ConnectionError:
            elapsed = time.time() - start_time
            result = {
                'timestamp': datetime.now().isoformat(),
                'status_code': None,
                'response_time': elapsed,
                'success': False,
                'error': 'Connection Error'
            }
        except Exception as e:
            elapsed = time.time() - start_time
            result = {
                'timestamp': datetime.now().isoformat(),
                'status_code': None,
                'response_time': elapsed,
                'success': False,
                'error': str(e)
            }

        with self._lock:
            self.history[target['name']].append(result)
            if not result['success']:
                target['failure_count'] += 1
                if target['failure_count'] >= target['alert_threshold'] and not target['alert_fired']:
                    self._trigger_alert(target, result)
                    target['alert_fired'] = True
            else:
                if target['alert_fired']:
                    self._trigger_recovery(target, result)
                    target['alert_fired'] = False
                target['failure_count'] = 0
        return result

    def _trigger_alert(self, target, result):
        """觸發故障告警"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': "DOWN",
            'target': target['name'],
            'url': target['url'],
            'error': result['error'],
            'status_code': result['status_code']
        }
        with self._lock:
            self.alerts.append(alert)
        print(f"\n⚠️ 【故障告警】")
        print(f"  目標: {target['name']}")
        print(f"  URL: {target['url']}")
        print(f"  錯誤: {result['error']}")
        print(f"  時間: {alert['timestamp']}")
        try:
            self._send_email_alert(alert)
        except Exception as e:
            print(f"郵件發送失敗: {str(e)}")

    def _trigger_recovery(self, target, result):
        """觸發恢復通知"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': "RECOVERY",
            'target': target['name'],
            'url': target['url'],
            'error': None,
            'status_code': result['status_code']
        }
        with self._lock:
            self.alerts.append(alert)
        print(f"\n✅【服務恢復】")
        print(f"  目標: {target['name']}")
        print(f"  URL: {target['url']}")
        print(f"  狀態碼: {result['status_code']}")
        print(f"  時間: {alert['timestamp']}")
        try:
            self._send_email_alert(alert)
        except Exception as e:
            print(f"恢復郵件發送失敗: {str(e)}")

    def _send_email_alert(self, alert):
        """發送郵件告警，自行填入SMTP資訊"""
        # msg = MIMEText(f"""
        # 監控告警
        # 類型: {alert['type']}
        # 目標: {alert['target']}
        # URL: {alert['url']}
        # 錯誤: {alert['error']}
        # 狀態碼: {alert['status_code']}
        # 時間: {alert['timestamp']}
        # """)
        # msg['Subject'] = f"[{alert['type']}] {alert['target']}"
        # msg['From'] = "monitor@example.com"
        # msg['To'] = "admin@example.com"
        # with smtplib.SMTP_SSL("smtp.example.com", 465) as server:
        #     server.login("user", "password")
        #     server.send_message(msg)
        pass

    def run_check(self):
        """執行一次檢查"""
        print(f"\n{'='*60}")
        print(f"監控檢查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        for target in self.targets:
            result = self.check_target(target)
            status = "✓" if result['success'] else "✗"
            print(f"{status} {target['name']}: "
                  f"狀態={result['status_code']}, "
                  f"耗時={result['response_time']:.3f}s")

    def start_monitoring(self):
        """開始持續監控"""
        self.running = True
        def monitor_loop():
            while self.running:
                self.run_check()
                time.sleep(self.check_interval)
        self.monitor_thread = threading.Thread(target=monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"監控已啟動，檢查間隔: {self.check_interval}秒")

    def stop_monitoring(self):
        """停止監控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("監控已停止")

    def get_uptime_report(self, target_name, hours=24):
        """生成可用性報告，按時間範圍過濾"""
        with self._lock:
            if target_name not in self.history:
                return None
            raw_history = list(self.history[target_name])
        if not raw_history:
            return None

        cutoff = datetime.now() - timedelta(hours=hours)
        history = []
        for item in raw_history:
            dt = datetime.fromisoformat(item['timestamp'])
            if dt >= cutoff:
                history.append(item)

        total_checks = len(history)
        if total_checks == 0:
            return {
                'target': target_name,
                'period_hours': hours,
                'total_checks': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'uptime_percent': 0.0,
                'avg_response_time': 0.0,
                'last_check': None
            }

        successful_checks = sum(1 for h in history if h['success'])
        uptime_percent = (successful_checks / total_checks * 100)
        response_times = [h['response_time'] for h in history if h['response_time'] is not None]
        avg_response_time = sum(response_times)/len(response_times) if response_times else 0

        return {
            'target': target_name,
            'period_hours': hours,
            'total_checks': total_checks,
            'successful_checks': successful_checks,
            'failed_checks': total_checks - successful_checks,
            'uptime_percent': round(uptime_percent, 2),
            'avg_response_time': round(avg_response_time, 3),
            'last_check': history[-1]['timestamp']
        }

# 使用示例
if __name__ == "__main__":
    monitor = NetworkMonitor(check_interval=30)
    # 添加監控目標
    monitor.add_target(
        name="公司官網",
        url="https://www.example.com",
        expected_status=200
    )
    monitor.add_target(
        name="API 服務",
        url="https://api.example.com/health",
        expected_status=200,
        timeout=5
    )
    monitor.add_target(
        name="測試環境",
        url="https://staging.example.com",
        expected_status=200
    )
    # 執行單次檢查
    monitor.run_check()
    # 開始持續監控（按 Ctrl+C 停止）
    # monitor.start_monitoring()
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     monitor.stop_monitoring()
    # 生成報告
    report = monitor.get_uptime_report("公司官網")
    if report:
        print(f"\n可用性報告:")
        print(f"  檢查次數: {report['total_checks']}")
        print(f"  成功率: {report['uptime_percent']}%")
        print(f"  平均響應: {report['avg_response_time']}s")
