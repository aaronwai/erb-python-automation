import re
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json
from typing import List, Dict, Optional, Iterator


class LogAnalyzer:
    """日誌分析類"""
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.patterns = {
            # 使用 [^"]* 避免引號破壞匹配
            'apache': r'(\S+) \S+ \S+ \[(.*?)\] "([^"]*)" (\d{3}) (\S+) "([^"]*)" "([^"]*)"',
            'nginx': r'(\S+) - - \[(.*?)\] "([^"]*)" (\d{3}) (\S+) "([^"]*)" "([^"]*)"',
            'error': r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (.*)',
            'custom': r'\[(.*?)\] \[(\w+)\] (.*)'
        }

    def _detect_log_type(self, path: Path) -> str:
        """啟發式檔名偵測 + 樣本行測試"""
        name = path.name.lower()
        # 先按檔名粗篩
        guess = "custom"
        if 'apache' in name or 'access' in name:
            guess = 'apache'
        elif 'nginx' in name:
            guess = 'nginx'
        elif 'error' in name:
            guess = 'error'

        # 讀前3行做驗證，修正猜測
        opener = gzip.open if path.suffix == ".gz" else open
        mode = "rt"
        try:
            with opener(path, mode, encoding='utf-8', errors='ignore') as f:
                sample_lines = [f.readline() for _ in range(3)]
        except Exception:
            return guess

        candidates = ["apache", "nginx", "error"]
        for t in candidates:
            pat = re.compile(self.patterns[t])
            hit = sum(1 for line in sample_lines if pat.match(line.strip()))
            if hit >= 1:
                return t
        return guess

    def parse_log_file(self, filepath, log_type='auto') -> List[Dict]:
        """解析日誌檔案，一次性載入所有結果"""
        path = Path(filepath)
        if log_type == 'auto':
            log_type = self._detect_log_type(path)

        opener = gzip.open if path.suffix == '.gz' else open
        mode = 'rt'

        entries: List[Dict] = []
        total_lines = 0
        pattern = re.compile(self.patterns.get(log_type, self.patterns['custom']))

        with opener(path, mode, encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                total_lines += 1
                line = line.strip()
                if not line:
                    continue
                match = pattern.match(line)
                if match:
                    entry = self._parse_match(match, log_type)
                    entry['line_number'] = line_num
                    entry['raw'] = line
                    entries.append(entry)
        matched = len(entries)
        failed = total_lines - matched
        print(f"解析完成: 總行 {total_lines}, 成功 {matched}, 失敗 {failed}")
        return entries

    def parse_log_iter(self, filepath, log_type='auto') -> Iterator[Dict]:
        """迭代器版本，逐行yield，適合超大日誌不佔記憶體"""
        path = Path(filepath)
        if log_type == 'auto':
            log_type = self._detect_log_type(path)
        opener = gzip.open if path.suffix == '.gz' else open
        mode = 'rt'
        pattern = re.compile(self.patterns.get(log_type, self.patterns['custom']))
        with opener(path, mode, encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                match = pattern.match(line)
                if match:
                    entry = self._parse_match(match, log_type)
                    entry['line_number'] = line_num
                    entry['raw'] = line
                    yield entry

    def _parse_match(self, match, log_type: str) -> Dict:
        groups = match.groups()
        if log_type in ['apache', 'nginx']:
            size_str = groups[4]
            size = int(size_str) if size_str.isdigit() else 0
            return {
                'ip': groups[0],
                'timestamp': groups[1],
                'request': groups[2],
                'status_code': int(groups[3]) if groups[3].isdigit() else 0,
                'size': size,
                'referer': groups[5],
                'user_agent': groups[6]
            }
        elif log_type == 'error':
            return {
                'timestamp': groups[0],
                'level': groups[1],
                'message': groups[2]
            }
        else:
            return {
                'timestamp': groups[0] if len(groups) > 0 else '',
                'level': groups[1] if len(groups) > 1 else 'INFO',
                'message': groups[2] if len(groups) > 2 else groups[-1]
            }

    def analyze_access_log(self, entries: List[Dict], top_n: int = 10) -> Dict:
        """分析訪問日誌，限制topN節省記憶體"""
        analysis = {
            'total_requests': len(entries),
            'unique_ips': set(),
            'status_distribution': Counter(),
            'hourly_distribution': Counter(),
            'top_ips': Counter(),
            'top_paths': Counter(),
            'user_agents': Counter(),
            'error_requests': []
        }
        for entry in entries:
            ip = entry.get('ip', 'unknown')
            analysis['unique_ips'].add(ip)
            analysis['top_ips'][ip] += 1

            status = entry.get('status_code', 0)
            analysis['status_distribution'][status] += 1
            if status >= 400:
                analysis['error_requests'].append(entry)

            ts = entry.get('timestamp', '')
            hour = self._extract_hour(ts)
            if hour is not None:
                analysis['hourly_distribution'][hour] += 1

            req = entry.get('request', '')
            path = self._extract_path(req)
            if path:
                analysis['top_paths'][path] += 1

            ua = entry.get('user_agent', '')
            analysis['user_agents'][ua] += 1

        analysis['unique_ips'] = len(analysis['unique_ips'])
        total = max(len(entries), 1)
        analysis['error_rate'] = len(analysis['error_requests']) / total
        analysis['avg_requests_per_ip'] = len(entries) / max(analysis['unique_ips'], 1)
        analysis['top_n'] = top_n
        return analysis

    def _extract_hour(self, timestamp: str) -> Optional[int]:
        """提取小時，分開處理不同格式，方便偵錯"""
        if not timestamp:
            return None
        # Apache access log format: 02/Jan/2025:14:30:00 +0800
        try:
            dt = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S %z')
            return dt.hour
        except ValueError:
            pass
        # Error log format: 2025-05-20 10:22:11
        try:
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return dt.hour
        except ValueError:
            return None

    def _extract_path(self, request: str) -> str:
        parts = request.split()
        if len(parts) >= 2:
            return parts[1]
        return request

    def generate_access_report(self, analysis: Dict, output_file: str = "access_report.html"):
        top_n = analysis.get("top_n", 10)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>訪問日誌分析報告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px;
                          background: #f0f0f0; border-radius: 5px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
                .metric-label {{ font-size: 14px; color: #666; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background: #f2f2f2; }}
                .error {{ color: #f44336; }}
            </style>
        </head>
        <body>
            <h1>訪問日誌分析報告</h1>
            <p>生成時間: {datetime.now().isoformat()}</p>
            <h2>關鍵指標</h2>
            <div class="metric">
                <div class="metric-value">{analysis['total_requests']}</div>
                <div class="metric-label">總請求數</div>
            </div>
            <div class="metric">
                <div class="metric-value">{analysis['unique_ips']}</div>
                <div class="metric-label">獨立 IP</div>
            </div>
            <div class="metric">
                <div class="metric-value">{analysis['error_rate']:.2%}</div>
                <div class="metric-label">錯誤率</div>
            </div>
            <h2>狀態碼分佈</h2>
            <table>
                <tr><th>狀態碼</th><th>數量</th><th>佔比</th></tr>
        """
        total_req = max(analysis['total_requests'],1)
        for status, count in analysis['status_distribution'].most_common():
            pct = count / total_req * 100
            html += f"<tr><td>{status}</td><td>{count}</td><td>{pct:.2f}%</td></tr>"

        html += """
            </table>
            <h2>熱門 IP</h2>
            <table>
                <tr><th>IP 地址</th><th>請求數</th></tr>
        """
        for ip, cnt in analysis['top_ips'].most_common(top_n):
            html += f"<tr><td>{ip}</td><td>{cnt}</td></tr>"

        html += """
            </table>
            <h2>熱門請求路徑</h2>
            <table>
                <tr><th>路徑</th><th>請求數</th></tr>
        """
        for path, cnt in analysis['top_paths'].most_common(top_n):
            html += f"<tr><td>{path}</td><td>{cnt}</td></tr>"

        html += """
            </table>
            <h2>每小時請求分佈</h2>
            <table>
                <tr><th>小時</th><th>請求數</th></tr>
        """
        for hour, cnt in sorted(analysis['hourly_distribution'].items()):
            html += f"<tr><td>{hour}</td><td>{cnt}</td></tr>"

        html += """
            </table>
        </body>
        </html>
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML報告已生成: {output_file}")

    def export_json(self, analysis:Dict, output_file="log_analysis.json"):
        """匯出JSON格式分析結果"""
        serializable = {
            "total_requests": analysis["total_requests"],
            "unique_ips": analysis["unique_ips"],
            "error_rate": analysis["error_rate"],
            "status_distribution": dict(analysis["status_distribution"]),
            "hourly_distribution": dict(analysis["hourly_distribution"]),
            "top_ips": dict(analysis["top_ips"].most_common(analysis.get("top_n",10))),
            "top_paths": dict(analysis["top_paths"].most_common(analysis.get("top_n",10)))
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
        print(f"JSON分析結果已匯出: {output_file}")

    def clean_old_logs(self, days: int = 30, dry_run: bool = True) -> List[Path]:
        """清理舊日誌（依檔案修改時間）"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted: List[Path] = []
        for log_file in self.log_dir.rglob("*"):
            if not log_file.is_file():
                continue
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                if dry_run:
                    print(f"[預覽刪除] {log_file} | mtime={mtime}")
                else:
                    try:
                        log_file.unlink()
                        deleted.append(log_file)
                        print(f"已刪除: {log_file}")
                    except Exception as e:
                        print(f"刪除失敗 {log_file}: {str(e)}")
        return deleted


# 使用示例
if __name__ == "__main__":
    analyzer = LogAnalyzer("logs")
    entries = analyzer.parse_log_file("access.log", log_type='apache')
    analysis = analyzer.analyze_access_log(entries, top_n=10)

    print(f"\n分析結果:")
    print(f"  總請求: {analysis['total_requests']}")
    print(f"  獨立 IP: {analysis['unique_ips']}")
    print(f"  錯誤率: {analysis['error_rate']:.2%}")
    print(f"  熱門路徑: {analysis['top_paths'].most_common(5)}")

    analyzer.generate_access_report(analysis, "report.html")
    analyzer.export_json(analysis, "log_analysis.json")
    analyzer.clean_old_logs(days=30, dry_run=True)
