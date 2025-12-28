import shutil
import os
import stat

def remove_readonly(func, path, _):
    """
    错误回调函数：如果是 '拒绝访问' 错误，尝试修改文件权限为可写，然后重试。
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"Failed to fix permission for {path}: {e}")

cache_path = ".pytest_cache"

if os.path.exists(cache_path):
    print(f"Found {cache_path}, attempting to remove...")
    try:
        shutil.rmtree(cache_path, onerror=remove_readonly)
        print("✅ Successfully removed .pytest_cache")
    except Exception as e:
        print(f"❌ Critical failure removing .pytest_cache: {e}")
        print("Suggestion: Please RESTART VS Code or your Computer to release file locks.")
else:
    print(f"ℹ️ {cache_path} not found. Nothing to clean.")