from pathlib import Path
import shutil

# ============================================
# 使用傳統方式操作文件
# ============================================

# 寫入文本文件
with open("example.txt", "w", encoding="utf-8") as f:
    f.write("這是第一行\n")
    f.write("這是第二行\n")

# 讀取文本文件
with open("example.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content)

# 逐行讀取
with open("example.txt", "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        print(f"第 {line_num} 行: {line.strip()}")

# 追加模式
with open("example.txt", "a", encoding="utf-8") as f:
    f.write("這是追加的內容\n")

# ============================================
# 使用 pathlib（推薦）
# ============================================

file_path = Path("data") / "report.txt"

# 自動創建目錄
file_path.parent.mkdir(parents=True, exist_ok=True)

# 寫入文件
file_path.write_text("自動化報告內容", encoding="utf-8")

# 讀取文件
content = file_path.read_text(encoding="utf-8")

# 檢查文件屬性
print(f"文件存在: {file_path.exists()}")
print(f"文件大小: {file_path.stat().st_size} bytes")
print(f"最後修改: {file_path.stat().st_mtime}")