import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import tempfile

class FileSystemAutomation:
    """文件系統自動化管理類"""

    def __init__(self, base_path="."):
        self.base_path = Path(base_path)

    # ============================================
    # 目錄操作
    # ============================================

    def create_directory_structure(self, structure):
        """
        根據結構字典創建目錄

        Args:
            structure: 目錄結構字典，例如：
            {
                "project": {
                    "src": {"components": {}, "utils": {}},
                    "tests": {},
                    "docs": {}
                }
            }
        """
        def create_recursive(base, struct):
            for name, content in struct.items():
                path = base / name
                if isinstance(content, dict):
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"創建目錄: {path}")
                    create_recursive(path, content)
                else:
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"創建目錄: {path}")

        create_recursive(self.base_path, structure)
        print("目錄結構創建完成")

    def list_directory(self, path=None, pattern="*", recursive=False):
        """列出目錄內容"""
        target = Path(path) if path else self.base_path

        items = {
            'directories': [],
            'files': []
        }

        iterator = target.rglob(pattern) if recursive else target.glob(pattern)

        for item in iterator:
            info = {
                'name': item.name,
                'size': item.stat().st_size if item.is_file() else None,
                'modified': datetime.fromtimestamp(item.stat().st_mtime),
                'path': str(item),
                'extension': item.suffix if item.is_file() else None
            }

            if item.is_dir():
                items['directories'].append(info)
            else:
                items['files'].append(info)

        return items

    def get_directory_tree(self, path=None, prefix=""):
        """獲取目錄樹狀結構"""
        target = Path(path) if path else self.base_path
        tree = []

        for item in sorted(target.iterdir()):
            if item.is_dir():
                tree.append(f"{prefix}[DIR]  {item.name}/")
                tree.extend(self.get_directory_tree(item, prefix + "  "))
            else:
                size = self._format_size(item.stat().st_size)
                tree.append(f"{prefix}[FILE] {item.name} ({size})")

        return tree

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    # ============================================
    # 文件操作
    # ============================================

    def copy_file(self, source, destination, overwrite=False, preserve_metadata=True):
        """複製文件"""
        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        if dst.exists() and not overwrite:
            print(f"目標已存在，跳過: {dst}")
            return False

        dst.parent.mkdir(parents=True, exist_ok=True)

        if preserve_metadata:
            shutil.copy2(src, dst)  # 保留元數據（修改時間等）
        else:
            shutil.copy(src, dst)

        print(f"已複製: {src} -> {dst}")
        return True

    def move_file(self, source, destination):
        """移動文件"""
        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"已移動: {src} -> {dst}")

    def delete_file(self, filepath, safe=True, backup_dir=None):
        """安全刪除文件"""
        path = Path(filepath)

        if not path.exists():
            print(f"文件不存在: {path}")
            return False

        if safe:
            # 移動到備份目錄
            if backup_dir is None:
                backup_dir = self.base_path / ".deleted"

            backup_dir = Path(backup_dir)
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{timestamp}_{path.name}"
            backup_path = backup_dir / backup_name

            shutil.move(str(path), str(backup_path))
            print(f"已移至備份: {backup_path}")
        else:
            path.unlink()
            print(f"已刪除: {path}")

        return True

    def rename_file(self, source, new_name):
        """重命名文件"""
        src = Path(source)
        dst = src.with_name(new_name)
        src.rename(dst)
        print(f"已重命名: {src.name} -> {new_name}")
        return dst

    # ============================================
    # 批量操作
    # ============================================

    def batch_copy(self, source_pattern, destination_dir, overwrite=False):
        """批量複製符合條件的文件"""
        dest = Path(destination_dir)
        dest.mkdir(parents=True, exist_ok=True)

        copied = []
        for file_path in self.base_path.glob(source_pattern):
            if file_path.is_file():
                dst = dest / file_path.name
                try:
                    if self.copy_file(file_path, dst, overwrite):
                        copied.append(dst)
                except Exception as e:
                    print(f"複製失敗 {file_path}: {str(e)}")

        print(f"批量複製完成: {len(copied)} 個文件")
        return copied

    def batch_move(self, source_pattern, destination_dir):
        """批量移動文件"""
        dest = Path(destination_dir)
        dest.mkdir(parents=True, exist_ok=True)

        moved = []
        for file_path in self.base_path.glob(source_pattern):
            if file_path.is_file():
                dst = dest / file_path.name
                try:
                    self.move_file(file_path, dst)
                    moved.append(dst)
                except Exception as e:
                    print(f"移動失敗 {file_path}: {str(e)}")

        print(f"批量移動完成: {len(moved)} 個文件")
        return moved

    def batch_delete(self, pattern, safe=True, confirm=True):
        """批量刪除文件"""
        files = list(self.base_path.glob(pattern))

        if not files:
            print(f"沒有匹配的文件: {pattern}")
            return []

        if confirm:
            print(f"即將刪除以下 {len(files)} 個文件:")
            for f in files:
                print(f"  - {f}")
            response = input("確認刪除? (y/N): ")
            if response.lower() != 'y':
                print("已取消")
                return []

        deleted = []
        for file_path in files:
            try:
                if self.delete_file(file_path, safe=safe):
                    deleted.append(file_path)
            except Exception as e:
                print(f"刪除失敗 {file_path}: {str(e)}")

        return deleted

    def sync_directories(self, source_dir, target_dir, delete_extra=False, dry_run=False):
        """
        同步兩個目錄

        Args:
            delete_extra: 是否刪除目標目錄多餘文件
            dry_run: 僅預覽，不實際執行
        """
        src = Path(source_dir)
        dst = Path(target_dir)

        if not src.exists():
            raise FileNotFoundError(f"源目錄不存在: {src}")

        dst.mkdir(parents=True, exist_ok=True)

        operations = []

        # 複製新增和修改的文件
        for src_file in src.rglob("*"):
            if src_file.is_file():
                rel_path = src_file.relative_to(src)
                dst_file = dst / rel_path

                need_update = False

                if not dst_file.exists():
                    need_update = True
                    operations.append(('copy', src_file, dst_file))
                elif src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    need_update = True
                    operations.append(('update', src_file, dst_file))

                if need_update and not dry_run:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    print(f"已同步: {rel_path}")

        # 刪除目標目錄多餘文件
        if delete_extra:
            for dst_file in dst.rglob("*"):
                if dst_file.is_file():
                    rel_path = dst_file.relative_to(dst)
                    src_file = src / rel_path

                    if not src_file.exists():
                        operations.append(('delete', dst_file, None))
                        if not dry_run:
                            dst_file.unlink()
                            print(f"已刪除多餘文件: {rel_path}")

        if dry_run:
            print(f"\n預覽模式 - 將執行以下操作:")
            for op, src, dst in operations:
                if dst:
                    print(f"  [{op.upper()}] {src} -> {dst}")
                else:
                    print(f"  [{op.upper()}] {src}")

        return operations

    # ============================================
    # 清理與維護
    # ============================================

    def clean_old_files(self, directory, days=30, pattern="*"):
        """清理指定天數前的文件"""
        cutoff = datetime.now() - timedelta(days=days)
        target = Path(directory)

        if not target.exists():
            print(f"目錄不存在: {target}")
            return []

        deleted = []
        for file_path in target.rglob(pattern):
            if file_path.is_file():
                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                if modified < cutoff:
                    try:
                        file_path.unlink()
                        deleted.append(file_path)
                        print(f"已刪除過期文件: {file_path}")
                    except Exception as e:
                        print(f"刪除失敗 {file_path}: {str(e)}")

        print(f"已清理 {len(deleted)} 個過期文件")
        return deleted

    def get_directory_size(self, directory):
        """計算目錄總大小"""
        total = 0
        target = Path(directory)

        if not target.exists():
            return "0 B"

        for file_path in target.rglob("*"):
            if file_path.is_file():
                total += file_path.stat().st_size

        return self._format_size(total)

    def find_duplicate_files(self, directory):
        """查找重複文件"""
        import hashlib

        target = Path(directory)
        file_hashes = {}
        duplicates = []

        for file_path in target.rglob("*"):
            if file_path.is_file():
                file_hash = self._calculate_hash(file_path)

                if file_hash in file_hashes:
                    duplicates.append({
                        'hash': file_hash,
                        'original': file_hashes[file_hash],
                        'duplicate': file_path
                    })
                else:
                    file_hashes[file_hash] = file_path

        return duplicates

    def _calculate_hash(self, file_path, algorithm='md5'):
        """計算文件哈希值"""
        import hashlib

        hasher = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)

        return hasher.hexdigest()

# 使用示例
if __name__ == "__main__":
    fs = FileSystemAutomation("my_project")

    # 創建標準項目結構
    project_structure = {
        "src": {
            "modules": {},
            "utils": {},
            "tests": {}
        },
        "docs": {
            "api": {},
            "guides": {}
        },
        "data": {
            "raw": {},
            "processed": {},
            "output": {}
        },
        "config": {},
        "scripts": {}
    }

    fs.create_directory_structure(project_structure)

    # 顯示目錄樹
    print("\n目錄結構:")
    for line in fs.get_directory_tree():
        print(line)

    # 批量複製特定類型文件
    # fs.batch_copy("*.py", "backup/python_files")

    # 同步目錄
    # fs.sync_directories("source_folder", "backup_folder", delete_extra=True)

    # 清理 30 天前的日誌
    # fs.clean_old_files("logs", days=30, pattern="*.log")

    # 查找重複文件
    # duplicates = fs.find_duplicate_files("downloads")
    # print(f"找到 {len(duplicates)} 個重複文件")