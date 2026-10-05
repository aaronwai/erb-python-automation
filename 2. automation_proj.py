from datetime import datetime

class AutomationProject:
    """
    自動化項目標準工作流程（增強版，支援狀態、備註、匯出報告）
    This class models a 6-stage lifecycle for building Python automation projects.
    It tracks workflow steps, timestamps, custom notes, supports rollback and JSON report export.
    Fluent method chaining is enabled so methods can be chained one after another.
    """
    def __init__(self, project_name):
        """
        Constructor: Initialize a new automation project
        :param project_name: Name of your automation project
        """
        self.name = project_name          # Project name
        self.created_at = datetime.now().isoformat()  # Project creation timestamp (ISO format)
        self.records = []                 # Store full log of each executed step
        self.current_step_index = 0       # Track which workflow step we are currently on

    def _add_step_record(self, step_name, description, notes=""):
        """
        Private helper method: create and append one step log entry
        :param step_name: Name of this workflow stage
        :param description: Short description of the stage
        :param notes: Custom free-text notes for this step
        """
        record = {
            "step_name": step_name,
            "desc": description,
            "notes": notes,
            "exec_time": datetime.now().isoformat()
        }
        self.records.append(record)

    def analyze_requirements(self, notes=""):
        """
        Step 1: Requirement Analysis
        Identify repetitive tasks, check automation feasibility and estimate benefits.
        :param notes: Optional custom notes for this stage
        :return: self (enable fluent chaining)
        """
        print(f"\n[1/6] 分析自動化需求...")
        print("  - 識別重複性任務")
        print("  - 評估自動化可行性")
        print("  - 計算預期效益")
        self._add_step_record("需求分析", "識別重複任務、可行性評估、效益估算", notes)
        self.current_step_index = 1
        return self

    def design_solution(self, notes=""):
        """
        Step 2: Solution Design
        Select tools, design workflow/data flow and exception handling strategy.
        :param notes: Optional custom notes for this stage
        :return: self (enable fluent chaining)
        """
        print(f"\n[2/6] 設計自動化解決方案...")
        print("  - 選擇適當的工具和技術")
        print("  - 設計流程圖和數據流")
        print("  - 制定異常處理策略")
        self._add_step_record("方案設計", "選用技術、流程與數據流、異常策略", notes)
        self.current_step_index = 2
        return self

    def develop_script(self, notes=""):
        """
        Step 3: Script Development
        Write core automation logic, error handling and logging.
        :param notes: Optional custom notes for this stage
        :return: self (enable fluent chaining)
        """
        print(f"\n[3/6] 開發自動化腳本...")
        print("  - 編寫核心功能代碼")
        print("  - 實現錯誤處理機制")
        print("  - 添加日誌記錄功能")
        self._add_step_record("腳本開發", "核心程式、錯誤處理、日誌", notes)
        self.current_step_index = 3
        return self

    def test_automation(self, notes=""):
        """
        Step 4: Test & Validation
        Run unit test, integration test and stress test for edge cases.
        :param notes: Optional custom notes for this stage
        :return: self (enable fluent chaining)
        """
        print(f"\n[4/6] 執行自動化測試...")
        print("  - 單元測試各個模組")
        print("  - 整合測試完整流程")
        print("  - 壓力測試極端情況")
        self._add_step_record("測試驗證", "單元/整合/壓力測試", notes)
        self.current_step_index = 4
        return self

    def deploy_solution(self, notes=""):
        """
        Step 5: Deploy to production
        Configure runtime environment, schedule tasks and setup monitoring alerts.
        :param notes: Optional custom notes for this stage
        :return: self (enable fluent chaining)
        """
        print(f"\n[5/6] 部署自動化解決方案...")
        print("  - 配置執行環境")
        print("  - 設置定時任務")
        print("  - 建立監控告警")
        self._add_step_record("部署上線", "環境配置、排程、監控告警", notes)
        self.current_step_index = 5
        return self

    def monitor_maintain(self, notes=""):
        """
        Step 6: Monitor & Maintain
        Review logs, optimize performance and iterate based on new requirements.
        :param notes: Optional custom notes for this stage
        :return: self (enable fluent chaining)
        """
        print(f"\n[6/6] 持續監控與維護...")
        print("  - 定期檢查執行日誌")
        print("  - 優化性能和穩定性")
        print("  - 根據需求迭代更新")
        self._add_step_record("監控維護", "日誌檢查、效能優化、迭代更新", notes)
        self.current_step_index = 6
        return self

    def rollback_to(self, step_idx:int):
        """
        Roll back project progress marker to specified step index.
        Keep all historical records intact; only change current step pointer.
        :param step_idx: target step number (0~6)
        :return: self (enable fluent chaining)
        """
        valid_idx = [0,1,2,3,4,5,6]
        if step_idx not in valid_idx:
            print("無效步驟索引，無法回滾")
            return self
        self.current_step_index = step_idx
        print(f"\n🔄 專案回滾至步驟 {step_idx}")
        return self

    def summary(self):
        """
        Print human-readable project summary to terminal.
        Show project name, creation time and list all completed workflow records.
        :return: self (enable fluent chaining)
        """
        print(f"\n{'='*60}")
        print(f"項目 '{self.name}' 完成！")
        print(f"建立時間: {self.created_at}")
        print(f"已執行步驟：")
        for idx, rec in enumerate(self.records, 1):
            print(f"  {idx}. {rec['step_name']} | {rec['exec_time']}")
        print(f"{'='*60}")
        return self

    def export_report(self, filepath="automation_project_report.json"):
        """
        Export full project log into JSON file for audit / documentation.
        :param filepath: output JSON file path, default = automation_project_report.json
        :return: self (enable fluent chaining)
        """
        import json
        payload = {
            "project": self.name,
            "created": self.created_at,
            "records": self.records
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n📄 專案報告已匯出至 {filepath}")
        return self


# ===================== Demo execution =====================
# Create an automation project instance: Financial Report Automation
project = AutomationProject("財務報表自動化")
(project
    .analyze_requirements(notes="輸入：每月Excel財務資料；輸出：合併報表")
    .design_solution(notes="使用Pandas+Openpyxl；排程用cron")
    .develop_script()
    .test_automation(notes="測試邊界：空檔、數值異常")
    .deploy_solution()
    .monitor_maintain()
    .summary()
    .export_report())


"""
Python 自動化應用場景分類（補充對應工具）
Reference cheat sheet: common automation categories, use cases and recommended Python libraries
"""
scenarios = [
    ("網頁自動化", [
        "自動化測試（功能測試、回歸測試）",
        "網頁數據抓取與監控",
        "表單自動填寫與提交",
        "批量操作後台管理系統"
    ], "Playwright, Selenium, BeautifulSoup, Scrapy"),
    ("文件與數據處理", [
        "Excel/CSV 報表自動生成",
        "PDF 文件批量處理",
        "數據清洗與格式轉換",
        "文件自動分類與歸檔"
    ], "Pandas, Openpyxl, PyPDF2, python-docx"),
    ("系統管理", [
        "伺服器監控與告警",
        "日誌分析與清理",
        "備份任務自動化",
        "環境配置與部署"
    ], "psutil, subprocess, fabric, schedule"),
    ("通訊自動化", [
        "電子郵件批量發送",
        "即時訊息自動通知",
        "API 接口自動調用",
        "社交媒體內容發布"
    ], "smtplib, requests, webhook")
]

print("\n" + "=" * 60)
print("Python 自動化應用場景 & 推薦工具")
print("=" * 60)
for category, items, tools in scenarios:
    print(f"\n【{category}】 | 工具：{tools}")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")