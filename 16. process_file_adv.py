import json
import csv
from pathlib import Path
from datetime import datetime

class TextFileAutomation:
    """文本文件自動化處理類"""

    def __init__(self, base_dir="automated_files"):
        self.base_path = Path(base_dir)
        self.base_path.mkdir(exist_ok=True)

    def create_log_file(self, content, prefix="log"):
        """創建帶時間戳的日誌文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.txt"
        file_path = self.base_path / filename

        # 添加時間戳到內容
        log_content = f"[{datetime.now().isoformat()}]\n{content}\n"
        log_content += f"{'='*50}\n"

        file_path.write_text(log_content, encoding="utf-8")
        print(f"日誌已保存: {file_path}")
        return file_path

    def batch_process_txt(self, input_dir, process_func):
        """批量處理文本文件"""
        input_path = Path(input_dir)
        results = []

        for txt_file in input_path.glob("*.txt"):
            print(f"處理: {txt_file.name}")

            content = txt_file.read_text(encoding="utf-8")
            processed = process_func(content)

            # 保存處理結果
            output_file = self.base_path / f"processed_{txt_file.name}"
            output_file.write_text(processed, encoding="utf-8")
            results.append(output_file)

        return results

    def merge_text_files(self, file_list, output_name):
        """合併多個文本文件"""
        output_path = self.base_path / output_name

        merged_content = []
        for file_path in file_list:
            content = Path(file_path).read_text(encoding="utf-8")
            merged_content.append(f"=== {file_path.name} ===\n")
            merged_content.append(content)
            merged_content.append("\n\n")

        output_path.write_text("".join(merged_content), encoding="utf-8")
        print(f"文件已合併: {output_path}")
        return output_path

# 使用示例
if __name__ == "__main__":
    automation = TextFileAutomation()

    # 創建日誌
    automation.create_log_file("系統自動化任務執行成功", "system")

    # 批量處理示例：轉換為大寫
    def to_uppercase(text):
        return text.upper()

    # automation.batch_process_txt("source_files", to_uppercase)