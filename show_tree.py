import os
from pathlib import Path
import sys

def print_tree(directory: str, prefix: str = "", ignore_dirs: set = None):
    """
    印出目錄的樹狀結構
    
    Args:
        directory: 要顯示的目錄路徑
        prefix: 用於縮排的前綴字元
        ignore_dirs: 要忽略的目錄名稱集合
    """
    if ignore_dirs is None:
        ignore_dirs = {
            '__pycache__', 
            'venv', 
            '.git', 
            '.idea', 
            '.vscode',
            'build',
            'dist',
            '*.egg-info'
        }
    
    # 取得目錄內容
    path = Path(directory)
    
    # 取得所有檔案和目錄
    entries = sorted(list(path.iterdir()))
    
    # 過濾掉要忽略的目錄
    entries = [
        entry for entry in entries 
        if not any(ignore in str(entry) for ignore in ignore_dirs)
    ]
    
    # 印出每個項目
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        
        # 決定要使用的符號
        marker = "└── " if is_last else "├── "
        
        # 印出當前項目
        print(f"{prefix}{marker}{entry.name}")
        
        # 如果是目錄，遞迴處理
        if entry.is_dir():
            # 決定下一層的前綴
            extension = "    " if is_last else "│   "
            print_tree(str(entry), prefix + extension, ignore_dirs)

if __name__ == "__main__":
    # 取得要顯示的目錄路徑（預設為當前目錄）
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"\n專案目錄結構:")
    print("=" * 50)
    print_tree(directory)
    print("=" * 50)