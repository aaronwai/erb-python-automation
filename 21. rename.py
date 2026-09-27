import os
import re
import shutil # Shell Utilities
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import mimetypes

class AIFileOrganizer:
    """AI 智能文件整理類"""

    def __init__(self):
        self.patterns = {
            'date': r'(\d{4}[-_]?(\d{2})[-_]?(\d{2}))',
            'invoice': r'(INV|invoice)[-_]?(\d+)',
            'project': r'(PRJ|project)[-_]?(\w+)',
            'email': r'[\w\.-]+@[\w\.-]+\.\w+'
        }

        self.category_keywords = {
            '財務': ['invoice', 'receipt', 'payment', '發票', '收據', '付款'],
            '項目': ['project', 'proposal', 'plan', '項目', '提案', '計劃'],
            '報告': ['report', 'summary', 'analysis', '報告', '摘要', '分析'],
            '合約': ['contract', 'agreement', 'nda', '合約', '協議', '保密'],
            '人事': ['resume', 'cv', 'application', '簡歷', '履歷', '申請']
        }

    def intelligent_rename(self, directory, naming_pattern=None, preview=True):
        """
        智能重命名文件

        根據文件內容、日期、類型自動生成有意義的名稱
        """
        target = Path(directory)
        rename_plan = []

        for file_path in target.iterdir():
            if not file_path.is_file():
                continue

            # 分析文件名
            new_name = self._generate_name(file_path, naming_pattern)

            if new_name and new_name != file_path.name:
                rename_plan.append({
                    'old': file_path,
                    'new': file_path.with_name(new_name)
                })

        if preview:
            print("\n重命名預覽:")
            for item in rename_plan:
                print(f"  {item['old'].name}")
                print(f"    -> {item['new'].name}")

            response = input(f"\n確認執行? (y/N): ")
            if response.lower() != 'y':
                print("已取消")
                return []

        # 執行重命名
        executed = []
        for item in rename_plan:
            try:
                item['old'].rename(item['new'])
                executed.append(item)
                print(f"已重命名: {item['old'].name} -> {item['new'].name}")
            except Exception as e:
                print(f"重命名失敗 {item['old']}: {str(e)}")

        return executed

    def _generate_name(self, file_path, pattern):
        """生成新文件名"""
        original = file_path.stem
        suffix = file_path.suffix

        # 提取日期
        date_match = re.search(self.patterns['date'], original)
        if date_match:
            date_str = date_match.group(1).replace('_', '-')
            raw_date = date_str.replace('-', '')
            # 標準化日期格式
            if len(raw_date) == 8:
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        else:
            # 使用文件修改日期
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            date_str = mtime.strftime("%Y-%m-%d")

        # 提取類型標識
        doc_type = self._detect_document_type(file_path)

        # 提取項目/客戶名稱
        project_match = re.search(self.patterns['project'], original, re.IGNORECASE)
        project = project_match.group(2) if project_match else ""

        # 生成新名稱
        if pattern:
            new_name = pattern.format(
                date=date_str,
                type=doc_type,
                project=project,
                original=original,
                index=0
            )
        else:
            components = [date_str]
            if project:
                components.append(project)
            components.append(doc_type)
            new_name = "_".join(components) + suffix

        # 清理文件名
        new_name = re.sub(r'[^\w\-\.]', '_', new_name)
        new_name = re.sub(r'_+', '_', new_name)

        # 處理重名
        counter = 1
        final_name = new_name
        while (file_path.parent / final_name).exists():
            stem = Path(new_name).stem
            final_name = f"{stem}_{counter}{suffix}"
            counter += 1

        return final_name

    def _detect_document_type(self, file_path):
        """檢測文件類型"""
        name_lower = file_path.name.lower()

        # 根據關鍵詞檢測
        for doc_type, keywords in self.category_keywords.items():
            if any(kw in name_lower for kw in keywords):
                return doc_type

        # 根據 MIME 類型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            main_type = mime_type.split('/')[0]
            type_map = {
                'image': '圖片',
                'video': '視頻',
                'audio': '音頻',
                'application': '文檔'
            }
            return type_map.get(main_type, '文件')

        # 根據副檔名
        ext_map = {
            '.pdf': 'PDF文檔',
            '.doc': 'Word文檔',
            '.docx': 'Word文檔',
            '.xls': 'Excel表格',
            '.xlsx': 'Excel表格',
            '.ppt': '演示文稿',
            '.pptx': '演示文稿',
            '.txt': '文本',
            '.zip': '壓縮包',
            '.rar': '壓縮包'
        }

        return ext_map.get(file_path.suffix.lower(), '文件')

    def auto_organize_by_type(self, source_dir, target_base_dir, copy=False):
        """
        按類型自動整理文件

        Args:
            copy: True 為複製，False 為移動
        """
        source = Path(source_dir)
        target_base = Path(target_base_dir)

        if not source.exists():
            raise FileNotFoundError(f"源目錄不存在: {source}")

        # 按類型分類
        type_folders = defaultdict(list)

        for file_path in source.iterdir():
            if file_path.is_file():
                doc_type = self._detect_document_type(file_path)
                type_folders[doc_type].append(file_path)

        # 移動/複製到對應文件夾
        operation = shutil.copy2 if copy else shutil.move

        for doc_type, files in type_folders.items():
            folder_name = self._sanitize_folder_name(doc_type)
            target_folder = target_base / folder_name
            target_folder.mkdir(parents=True, exist_ok=True)

            for file_path in files:
                target = target_folder / file_path.name

                # 處理重名
                counter = 1
                original_target = target
                while target.exists():
                    stem = original_target.stem
                    target = target_folder / f"{stem}_{counter}{original_target.suffix}"
                    counter += 1

                try:
                    operation(str(file_path), str(target))
                    action = "已複製" if copy else "已移動"
                    print(f"{action}: {file_path.name} -> {folder_name}/")
                except Exception as e:
                    print(f"操作失敗 {file_path}: {str(e)}")

    def _sanitize_folder_name(self, name):
        """清理文件夾名稱"""
        # 替換非法字符
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        # 移除前後空格
        name = name.strip()
        # 限制長度
        return name[:50]

    def organize_by_date(self, source_dir, target_base_dir,
                        date_format="%Y-%m", copy=False):
        """
        按日期自動整理文件

        Args:
            date_format: 日期文件夾格式，如 "%Y-%m" 為 2024-01
        """
        source = Path(source_dir)
        target_base = Path(target_base_dir)

        operation = shutil.copy2 if copy else shutil.move

        for file_path in source.iterdir():
            if file_path.is_file():
                # 獲取文件日期（優先創建時間，後修改時間）
                stat = file_path.stat()
                try:
                    file_date = datetime.fromtimestamp(stat.st_birthtime)
                except AttributeError:
                    file_date = datetime.fromtimestamp(stat.st_mtime)

                folder_name = file_date.strftime(date_format)
                target_folder = target_base / folder_name
                target_folder.mkdir(parents=True, exist_ok=True)

                target = target_folder / file_path.name

                try:
                    operation(str(file_path), str(target))
                    action = "已複製" if copy else "已移動"
                    print(f"{action}: {file_path.name} -> {folder_name}/")
                except Exception as e:
                    print(f"操作失敗 {file_path}: {str(e)}")

    def find_and_rename_duplicates(self, directory):
        """查找並標注重複文件"""
        import hashlib

        target = Path(directory)
        file_hashes = {}
        duplicates = []

        for file_path in target.rglob("*"):
            if file_path.is_file():
                file_hash = self._calculate_md5(file_path)

                if file_hash in file_hashes:
                    # 標注重複文件
                    new_name = f"DUPLICATE_{file_path.name}"
                    new_path = file_path.with_name(new_name)
                    file_path.rename(new_path)
                    duplicates.append({
                        'original': file_hashes[file_hash],
                        'duplicate': new_path
                    })
                    print(f"標注重複: {file_path.name} -> {new_name}")
                else:
                    file_hashes[file_hash] = file_path

        return duplicates

    def _calculate_md5(self, file_path):
        """計算文件 MD5"""
        import hashlib

        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

# 使用示例
if __name__ == "__main__":
    organizer = AIFileOrganizer()

    # 智能重命名
    organizer.intelligent_rename(
        "downloads",
        naming_pattern="{date}_{type}_{project}",
        preview=True
    )

    # 按類型自動整理
    organizer.auto_organize_by_type(
        "downloads",
        "organized_files",
        copy=False  # 設為 True 則改為複製
    )

    # 按日期整理照片
    organizer.organize_by_date(
        "photos",
        "photos_by_date",
        date_format="%Y/%Y-%m",
        copy=True
    )