# -*- coding: utf-8 -*-
"""
TMD Controller PyInstaller 打包脚本

用法:
    python build_exe.py          # 打包成单个exe文件
    python build_exe.py --clean  # 清理后重新打包
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build_dirs(root_dir: Path) -> None:
    """清理构建目录"""
    dirs_to_clean = [root_dir / "build", root_dir / "dist" / "exe"]
    for path in dirs_to_clean:
        if path.exists():
            if path.is_dir():
                print(f"清理目录: {path}")
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    print(f"警告: 无法删除目录 {path}: {e}")
            else:
                print(f"删除文件: {path}")
                try:
                    path.unlink()
                except Exception as e:
                    print(f"警告: 无法删除文件 {path}: {e}")

    # 清理 dist 目录中的 tmdc*.exe
    dist_dir = root_dir / "dist"
    if dist_dir.exists():
        for exe_file in dist_dir.glob("tmdc*.exe"):
            print(f"删除旧文件: {exe_file}")
            try:
                exe_file.unlink()
            except Exception as e:
                print(f"警告: 无法删除 {exe_file}: {e}")


def find_tmd_exe(root_dir: Path) -> Path | None:
    """查找 tmd.exe 文件位置

    查找顺序:
        1. tmdc/tmd.exe
        2. tmd.exe (项目根目录)

    Returns:
        tmd.exe 的路径，如果未找到返回 None
    """
    # 1. 检查 tmdc 子目录
    tmd_in_pkg = root_dir / "tmdc" / "tmd.exe"
    if tmd_in_pkg.exists():
        return tmd_in_pkg

    # 2. 检查项目根目录
    tmd_in_root = root_dir / "tmd.exe"
    if tmd_in_root.exists():
        return tmd_in_root

    return None


def build_with_spec(root_dir: Path, spec_path: Path, output_name: str) -> bool:
    """使用指定的 spec 文件打包"""
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(spec_path),
        "--clean",
        "--noconfirm",
    ]

    print(f"\n📦 正在打包: {output_name}")
    print(f"执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
    except Exception as e:
        print(f"❌ 执行 PyInstaller 失败: {e}")
        return False

    if result.returncode != 0:
        print(f"❌ 打包失败: {output_name} (返回码: {result.returncode})")
        return False

    # 检查输出文件
    dist_exe = root_dir / "dist" / "tmdc.exe"
    if not dist_exe.exists():
        print(f"❌ 未找到输出文件: {dist_exe}")
        return False

    # 重命名并移动到 dist/exe 目录
    exe_dist_dir = root_dir / "dist" / "exe"
    try:
        exe_dist_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ 无法创建目录 {exe_dist_dir}: {e}")
        return False

    final_path = exe_dist_dir / output_name

    # 如果目标文件已存在，先删除
    if final_path.exists():
        try:
            final_path.unlink()
        except Exception as e:
            print(f"❌ 无法删除旧文件 {final_path}: {e}")
            return False

    try:
        shutil.move(str(dist_exe), str(final_path))
    except Exception as e:
        print(f"❌ 无法移动文件到 {final_path}: {e}")
        return False

    # 显示文件信息
    try:
        size_mb = final_path.stat().st_size / (1024 * 1024)
        print(f"✅ 打包成功: {final_path}")
        print(f"📊 文件大小: {size_mb:.2f} MB")
    except Exception as e:
        print(f"✅ 打包成功: {final_path}")
        print(f"⚠️  无法获取文件大小: {e}")

    return True


def build_exe(root_dir: Path) -> int:
    """执行 PyInstaller 打包"""
    # 确保 PyInstaller 已安装
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # 查找 tmd.exe
    tmd_exe_path = find_tmd_exe(root_dir)
    has_tmd = tmd_exe_path is not None

    # 使用项目中的 tmdc.spec 文件
    spec_file = root_dir / "tmdc.spec"
    if not spec_file.exists():
        print(f"❌ 未找到 spec 文件: {spec_file}")
        return 1

    if has_tmd:
        # 存在 tmd.exe，生成两个版本
        print(f"\n🔍 检测到 tmd.exe: {tmd_exe_path}")
        print(f"   文件大小: {tmd_exe_path.stat().st_size / 1024 / 1024:.2f} MB")
        print("将生成两个版本: full 和 lite\n")

        # 打包完整版（使用 tmdc.spec，它会自动检测 tmd.exe）
        if not build_with_spec(root_dir, spec_file, "tmdc-full.exe"):
            return 1

        # 打包轻量版（需要临时移动 tmd.exe）
        print("\n📦 准备打包 lite 版本...")
        temp_tmd = tmd_exe_path.with_suffix(tmd_exe_path.suffix + ".tmp")
        try:
            # 临时重命名 tmd.exe，让 spec 检测不到
            tmd_exe_path.rename(temp_tmd)
            if not build_with_spec(root_dir, spec_file, "tmdc-lite.exe"):
                # 恢复 tmd.exe
                temp_tmd.rename(tmd_exe_path)
                return 1
            # 恢复 tmd.exe
            temp_tmd.rename(tmd_exe_path)
        except Exception as e:
            # 确保恢复
            if temp_tmd.exists():
                temp_tmd.rename(tmd_exe_path)
            print(f"❌ 打包 lite 版本时出错: {e}")
            return 1

        print("\n" + "=" * 50)
        print("✅ 两个版本打包完成!")
        print("=" * 50)
    else:
        # 不存在 tmd.exe，只生成 lite 版本
        print("\n⚠️  未检测到 tmd.exe")
        print("   查找位置:")
        print(f"   - {root_dir / 'tmdc' / 'tmd.exe'}")
        print(f"   - {root_dir / 'tmd.exe'}")
        print("将生成 lite 版本（需用户自备 tmd.exe）\n")

        if not build_with_spec(root_dir, spec_file, "tmdc-lite.exe"):
            return 1

        print("\n" + "=" * 50)
        print("✅ Lite 版本打包完成!")
        print("=" * 50)

    return 0


def main() -> int:
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)

    parser = argparse.ArgumentParser(description="TMD Controller 打包工具")
    parser.add_argument("--clean", action="store_true", help="清理后重新打包")
    args = parser.parse_args()

    root_dir = script_dir

    if args.clean:
        clean_build_dirs(root_dir)

    return build_exe(root_dir)


if __name__ == "__main__":
    sys.exit(main())
