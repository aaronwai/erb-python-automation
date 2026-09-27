import schedule
import time
import threading
from datetime import datetime
from pathlib import Path
import json
from typing import Optional, Dict, Callable, Any
from functools import wraps

class TaskScheduler:
    """任務排程器，基於 schedule 庫，統一使用單一排程模型"""
    def __init__(self, config_file: Optional[str] = None):
        self.jobs: list[Dict[str, Any]] = []
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.config = self._load_config(config_file)
        self.logger = self._setup_logging()
        self._job_lock: Dict[str, threading.Lock] = dict()

    def _load_config(self, config_file: Optional[str]) -> Dict:
        """載入配置JSON"""
        if not config_file:
            return {}
        path = Path(config_file)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _setup_logging(self):
        """只取得logger，不在class內呼叫basicConfig"""
        import logging
        return logging.getLogger('TaskScheduler')

    def _safe_task_wrapper(self, task_func: Callable, job_id: str, *args, **kwargs):
        """包裝任務：異常捕獲 + 防重入鎖 + 記錄執行時間"""
        @wraps(task_func)
        def wrapper():
            lock = self._job_lock[job_id]
            if not lock.acquire(blocking=False):
                self.logger.warning(f"任務 {job_id} 上一輪尚未完成，跳過本次執行")
                return
            try:
                self.logger.info(f"開始執行任務: {job_id}")
                start = datetime.now()
                task_func(*args, **kwargs)
                end = datetime.now()
                self.logger.info(f"任務 {job_id} 執行完成，耗時: {(end-start).total_seconds():.2f}s")
            except Exception as e:
                self.logger.error(f"任務 {job_id} 執行異常", exc_info=True)
            finally:
                lock.release()
        return wrapper

    def add_cron_job(self,
                     task_func: Callable,
                     schedule_type: str,
                     time_str: str,
                     *args,
                     **kwargs):
        """
        添加定時任務
        Args:
            schedule_type: 'daily', 'hourly', 'weekly', 'interval'
            time_str:
                daily: '02:00'
                hourly: '10:30' (每小時第10分30秒)
                weekly: 'friday 17:00'
                interval: '30' (每30分鐘)
        """
        job_id = f"{task_func.__name__}_{datetime.now().timestamp()}"
        self._job_lock[job_id] = threading.Lock()
        wrapped_func = self._safe_task_wrapper(task_func, job_id, *args, **kwargs)

        if schedule_type == 'daily':
            job = schedule.every().day.at(time_str).do(wrapped_func)
        elif schedule_type == 'hourly':
            job = schedule.every().hour.at(time_str).do(wrapped_func)
        elif schedule_type == 'weekly':
            day, at_time = time_str.split()
            day_map = {
                'monday': schedule.every().monday,
                'tuesday': schedule.every().tuesday,
                'wednesday': schedule.every().wednesday,
                'thursday': schedule.every().thursday,
                'friday': schedule.every().friday,
                'saturday': schedule.every().saturday,
                'sunday': schedule.every().sunday
            }
            job = day_map[day.lower()].at(at_time).do(wrapped_func)
        elif schedule_type == 'interval':
            minutes = int(time_str.strip())
            job = schedule.every(minutes).minutes.do(wrapped_func)
        else:
            raise ValueError(f"不支援的排程類型: {schedule_type}")

        job_entry = {
            "job_id": job_id,
            "function": task_func.__name__,
            "schedule": f"{schedule_type} {time_str}",
            "job": job,
            "registered_at": datetime.now()
        }
        self.jobs.append(job_entry)
        self.logger.info(f"添加任務 [{job_id}] : {task_func.__name__} | {schedule_type} {time_str}")
        return job_entry

    def remove_job(self, job_id: str):
        """移除指定job"""
        for idx, entry in enumerate(self.jobs):
            if entry["job_id"] == job_id:
                schedule.cancel_job(entry["job"])
                del self._job_lock[job_id]
                self.jobs.pop(idx)
                self.logger.info(f"移除任務 {job_id}")
                return True
        self.logger.warning(f"找不到任務 {job_id}")
        return False

    def start(self, blocking: bool = False):
        """啟動排程器"""
        self.running = True
        if blocking:
            self.logger.info("排程器啟動【阻塞模式】")
            try:
                while self.running:
                    schedule.run_pending()
                    time.sleep(1)
            except Exception as e:
                self.logger.error("排程主循環異常", exc_info=True)
        else:
            self.logger.info("排程器啟動【非阻塞模式】")
            def run_scheduler():
                while self.running:
                    schedule.run_pending()
                    time.sleep(1)
            self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            self.scheduler_thread.start()

    def stop(self):
        """停止排程器，清空所有任務"""
        self.logger.info("正在停止排程器...")
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        self.jobs.clear()
        self._job_lock.clear()
        self.logger.info("排程器已停止，所有任務清除")

    def list_jobs(self) -> list[Dict[str, Any]]:
        """返回結構化任務清單，同時print"""
        print("\n===== 已排程任務 =====")
        for i, job in enumerate(self.jobs, 1):
            print(f"{i}. ID:{job['job_id']} | Func:{job['function']} | Schedule:{job['schedule']}")
        return self.jobs


# 示例任務函數
def daily_backup_task():
    """每日備份任務"""
    print(f"[{datetime.now()}] 執行每日備份...")

def hourly_health_check():
    """每小時健康檢查"""
    print(f"[{datetime.now()}] 執行健康檢查...")

def weekly_report_task():
    """每週報告任務"""
    print(f"[{datetime.now()}] 生成週報...")


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scheduler = TaskScheduler()
    # 添加定時任務
    scheduler.add_cron_job(
        daily_backup_task,
        'daily',
        '02:00'  # 每天凌晨 2 點
    )
    scheduler.add_cron_job(
        hourly_health_check,
        'interval',
        '30'  # 每30分鐘
    )
    scheduler.add_cron_job(
        weekly_report_task,
        'weekly',
        'friday 17:00'  # 每週五下午 5 點
    )

    # 列出任務
    scheduler.list_jobs()

    # 啟動排程器
    try:
        scheduler.start(blocking=True)
    except KeyboardInterrupt:
        print("\n收到 Ctrl+C 中斷信號，準備停止排程器")
        scheduler.stop()
