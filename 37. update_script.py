#!/usr/bin/env python3
"""
自動化維護腳本範本
可用於定時任務（cron/TaskScheduler）
"""
import argparse
import logging
import sys
import traceback
import json
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd


class FileLock:
    """簡單 PID 檔鎖，防止任務並發重複執行"""
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path

    def acquire(self) -> bool:
        if self.lock_path.exists():
            try:
                pid = int(self.lock_path.read_text())
                # 檢查進程是否存在
                if sys.platform == "win32":
                    return False
                os.kill(pid, 0)
                return False
            except (OSError, ValueError):
                # PID 不存在，清理舊鎖
                self.lock_path.unlink(missing_ok=True)
        self.lock_path.write_text(str(os.getpid()))
        return True

    def release(self):
        self.lock_path.unlink(missing_ok=True)


class AutomationScript:
    """自動化腳本基類"""
    def __init__(self, name: str, config_file: Optional[str] = None, lock_file: Optional[str] = None):
        self.name = name
        self.start_time = datetime.now()
        self.config = self._load_config(config_file) if config_file else {}
        self.lock = FileLock(Path(lock_file)) if lock_file else None
        # 設置日誌
        self.logger = self._setup_logging()
        self.logger.info(f"腳本 '{name}' 開始執行")
        self.logger.info(f"開始時間: {self.start_time.isoformat()}")

    def _load_config(self, config_file: str) -> Dict:
        """載入配置文件"""
        path = Path(config_file)
        if not path.exists():
            self.logger.warning(f"配置文件不存在: {config_file}")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix == '.json':
                return json.load(f)
        return {}

    def _setup_logging(self) -> logging.Logger:
        """配置日誌"""
        log_dir = Path(self.config.get("log_dir", "logs"))
        log_dir.mkdir(exist_ok=True)
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"{self.name}_{timestamp}.log"
        # 創建 logger
        logger = logging.getLogger(f"{self.name}_{timestamp}")
        logger.setLevel(logging.INFO)
        # 避免重複添加 handler
        if logger.handlers:
            return logger
        # 檔案 handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        # 控制台 handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger

    def run(self):
        """主執行方法（子類需重寫）"""
        raise NotImplementedError("子類必須實現 run 方法")

    def cleanup(self):
        """清理資源"""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(f"腳本執行完成，耗時: {duration:.2f} 秒")
        # 關閉 handler
        for handler in self.logger.handlers:
            handler.close()
        # 釋放鎖
        if self.lock:
            self.lock.release()

    def execute(self):
        """執行腳本（包含異常處理 + 鎖檢查）"""
        if self.lock and not self.lock.acquire():
            self.logger.error("已有相同任務正在執行，退出")
            return 2
        exit_code = 0
        try:
            self.run()
            self.logger.info("腳本執行成功")
        except Exception as e:
            self.logger.error(f"執行出錯: {str(e)}")
            self.logger.error(traceback.format_exc())
            exit_code = 1
        finally:
            self.cleanup()
        return exit_code


class BackupScript(AutomationScript):
    """自動備份腳本"""
    def __init__(self, source: str, destination: str,
                 retention_days: int = 30,
                 dry_run: bool = False,
                 **kwargs):
        super().__init__("backup", kwargs.get('config_file'), kwargs.get('lock_file'))
        self.source = Path(source)
        self.destination = Path(destination)
        self.retention_days = retention_days
        self.dry_run = dry_run

    def run(self):
        """執行備份"""
        if not self.source.exists():
            raise FileNotFoundError(f"源目錄不存在: {self.source}")
        self.destination.mkdir(parents=True, exist_ok=True)
        # 創建帶時間戳的備份目錄
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.destination / backup_name

        if self.dry_run:
            self.logger.info(f"【DryRun】準備備份 {self.source} -> {backup_path}")
        else:
            # 執行複製
            if self.source.is_file():
                shutil.copy2(self.source, backup_path)
                self.logger.info(f"檔案備份: {self.source} -> {backup_path}")
            else:
                shutil.copytree(self.source, backup_path,
                              ignore=shutil.ignore_patterns('*.tmp', '*.log'), symlinks=False)
                self.logger.info(f"目錄備份: {self.source} -> {backup_path}")
            # 驗證備份
            if backup_path.exists():
                self.logger.info("備份驗證通過")
            else:
                raise RuntimeError("備份驗證失敗")
        # 清理舊備份
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        """清理舊備份"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        for backup_dir in self.destination.glob("backup_*"):
            try:
                # 從名稱解析日期
                date_str = backup_dir.name.replace('backup_', '')
                backup_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                if backup_date < cutoff:
                    if self.dry_run:
                        self.logger.info(f"【DryRun】將刪除舊備份: {backup_dir.name}")
                    else:
                        if backup_dir.is_file():
                            backup_dir.unlink()
                        else:
                            shutil.rmtree(backup_dir)
                        deleted_count += 1
                        self.logger.info(f"刪除舊備份: {backup_dir.name}")
            except (ValueError, OSError) as e:
                self.logger.warning(f"處理備份時出錯 {backup_dir}: {str(e)}")
        self.logger.info(f"清理完成: 刪除 {deleted_count} 個舊備份")


class DataSyncScript(AutomationScript):
    """數據同步腳本"""
    def __init__(self, source_db: str, target_db: str,
                 tables: Optional[list] = None,
                 dry_run: bool = False,
                 **kwargs):
        super().__init__("data_sync", kwargs.get('config_file'), kwargs.get('lock_file'))
        self.source_db = source_db
        self.target_db = target_db
        self.tables = tables or []
        self.dry_run = dry_run

    def run(self):
        """執行數據同步"""
        import sqlite3
        # 連接資料庫
        src_conn = sqlite3.connect(self.source_db)
        dst_conn = sqlite3.connect(self.target_db)
        try:
            for table in self.tables:
                self.logger.info(f"同步表: {table}")
                # 讀取源數據
                df = pd.read_sql(f"SELECT * FROM {table}", src_conn)
                self.logger.info(f"  讀取 {len(df)} 行")
                if not self.dry_run:
                    # 寫入目標（覆蓋模式）
                    df.to_sql(table, dst_conn, if_exists='replace', index=False)
                    self.logger.info(f"  寫入目標庫完成")
            if not self.dry_run:
                dst_conn.commit()
            self.logger.info("數據同步完成")
        finally:
            src_conn.close()
            dst_conn.close()


class ReportGenerationScript(AutomationScript):
    """報告生成腳本"""
    def __init__(self, data_source: str, output_dir: str = ".", output_format: str = 'html',
                 template: Optional[str] = None,
                 **kwargs):
        super().__init__("report_generation", kwargs.get('config_file'), kwargs.get('lock_file'))
        self.data_source = data_source
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.output_format = output_format
        self.template = template

    def run(self):
        """生成報告"""
        # 讀取數據
        if self.data_source.endswith('.csv'):
            df = pd.read_csv(self.data_source, encoding='utf-8-sig')
        elif self.data_source.endswith('.xlsx'):
            df = pd.read_excel(self.data_source)
        elif self.data_source.endswith('.json'):
            df = pd.read_json(self.data_source)
        else:
            raise ValueError(f"不支援的數據格式: {self.data_source}")
        # 生成報告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = str(self.output_dir / f"report_{timestamp}.{self.output_format}")
        if self.output_format == 'html':
            self._generate_html_report(df, output_file)
        elif self.output_format == 'excel':
            self._generate_excel_report(df, output_file)
        elif self.output_format == 'pdf':
            self._generate_pdf_report(df, output_file)
        elif self.output_format == 'md':
            self._generate_markdown_report(df, output_file)
        else:
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
        self.logger.info(f"報告已生成: {output_file}")

    def _generate_html_report(self, df, output_file):
        """生成 HTML 報告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>自動化報告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>數據報告</h1>
            <p>生成時間: {datetime.now().isoformat()}</p>
            <p>數據筆數: {len(df)}</p>
            <p>⚠️ 僅顯示前100筆</p>
            {df.head(100).to_html(index=False)}
        </body>
        </html>
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_markdown_report(self, df, output_file):
        """生成 Markdown 報告（和你的分析pipeline對接）"""
        md = f"""# 自動化數據報告
生成時間: {datetime.now().isoformat()}
總行數: {len(df)}

## 資料摘要
{df.describe().to_markdown()}

## 樣本數據（前50行）
{df.head(50).to_markdown(index=False)}
"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md)

    def _generate_excel_report(self, df, output_file):
        """生成 Excel 報告"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            # 添加統計摘要
            summary = df.describe()
            summary.to_excel(writer, sheet_name='Summary')

    def _generate_pdf_report(self, df, output_file):
        """生成 PDF 報告（需要安裝額外套件）"""
        try:
            from weasyprint import HTML
            html_content = f"""
            <h1>數據報告</h1>
            <p>筆數: {len(df)}</p>
            <p>⚠️ 僅顯示前50筆</p>
            {df.head(50).to_html()}
            """
            HTML(string=html_content).write_pdf(output_file)
        except ImportError:
            self.logger.warning("weasyprint 未安裝，改用 Markdown 格式")
            self._generate_markdown_report(df, output_file.replace('.pdf', '.md'))


# 命令行接口
def main():
    parser = argparse.ArgumentParser(description='自動化維護腳本')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    # 備份命令
    backup_parser = subparsers.add_parser('backup', help='執行備份')
    backup_parser.add_argument('--source', required=True, help='源路徑')
    backup_parser.add_argument('--dest', required=True, help='目標路徑')
    backup_parser.add_argument('--retention', type=int, default=30,
                              help='保留天數')
    backup_parser.add_argument('--config', help='配置文件')
    backup_parser.add_argument('--lock', help='Lock檔路徑，防止重複執行')
    backup_parser.add_argument('--dry-run', action='store_true', help='模擬執行，不修改檔案')

    # 同步命令
    sync_parser = subparsers.add_parser('sync', help='執行數據同步')
    sync_parser.add_argument('--source-db', required=True, help='源資料庫')
    sync_parser.add_argument('--target-db', required=True, help='目標資料庫')
    sync_parser.add_argument('--tables', nargs='+', required=True,
                            help='要同步的表')
    sync_parser.add_argument('--config', help='配置文件')
    sync_parser.add_argument('--lock', help='Lock檔路徑')
    sync_parser.add_argument('--dry-run', action='store_true', help='模擬執行')

    # 報告命令
    report_parser = subparsers.add_parser('report', help='生成報告')
    report_parser.add_argument('--source', required=True, help='數據源')
    report_parser.add_argument('--output-dir', default='.', help='報告輸出目錄')
    report_parser.add_argument('--format', default='html',
                              choices=['html', 'excel', 'pdf', 'csv', 'md'],
                              help='輸出格式')
    report_parser.add_argument('--config', help='配置文件')
    report_parser.add_argument('--lock', help='Lock檔路徑')

    args = parser.parse_args()
    if args.command == 'backup':
        script = BackupScript(
            source=args.source,
            destination=args.dest,
            retention_days=args.retention,
            dry_run=args.dry_run,
            config_file=args.config,
            lock_file=args.lock
        )
    elif args.command == 'sync':
        script = DataSyncScript(
            source_db=args.source_db,
            target_db=args.target_db,
            tables=args.tables,
            dry_run=args.dry_run,
            config_file=args.config,
            lock_file=args.lock
        )
    elif args.command == 'report':
        script = ReportGenerationScript(
            data_source=args.source,
            output_dir=args.output_dir,
            output_format=args.format,
            config_file=args.config,
            lock_file=args.lock
        )
    else:
        parser.print_help()
        sys.exit(1)
    exit_code = script.execute()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
