
import json
import shutil
import os
import filecmp
import tkinter as tk
from tkinter import filedialog
from sys import stdout

# 创建TK界面用于选择文件夹
root = tk.Tk()
root.withdraw()  # 不显示主窗口
target_folder = filedialog.askdirectory(title="选择目标文件夹")

# 路径配置
json_file_path = 'jsondata/classifications.json'

# 加载JSON文件
with open(json_file_path, 'r', encoding='utf-8') as f:
    classifications = json.load(f)

updated_classifications = {}

def get_edited_version_path(original_path):
    """
    给定原图路径，构造苹果风格的编辑图路径，例如：
    IMG_1234.JPG → IMG_E1234.JPG
    """
    dir_path = os.path.dirname(original_path)
    filename = os.path.basename(original_path)
    base, ext = os.path.splitext(filename)

    # 插入 E（简单策略：在首个数字前插入 'E'）
    for i, ch in enumerate(base):
        if ch.isdigit():
            new_base = base[:i] + 'E' + base[i:]
            edited_filename = new_base + ext
            return os.path.join(dir_path, edited_filename)
    
    return None  # 无数字，不生成


def print_progress(progress):
    stdout.write("\r进度: {:.2f}%".format(progress))
    stdout.flush()

def move_and_update(original_path, tags, total_files, current_file):
    if not tags:
        print(f"\n标签为空，跳过文件：{original_path}")
        return

    normalized_path = original_path.replace('/', os.path.sep)
    filename = os.path.basename(normalized_path)
    base, extension = os.path.splitext(filename)
    new_path = os.path.normpath(os.path.join(target_folder, filename))

    # 检查文件是否已在目标路径
    if os.path.abspath(normalized_path).lower() == os.path.abspath(new_path).lower():
        print(f"\n文件已在目标文件夹中，跳过：{normalized_path}")
        updated_classifications[original_path] = tags
        return

    try:
        if not os.path.exists(normalized_path):
            print(f"\n找不到源文件：{normalized_path}")
            return

        # 构造扩展资源路径（可选）
        related_paths = [(normalized_path, new_path)]  # 主图

        if "Live" in tags:
            mov_orig = normalized_path.replace(extension, '.MOV')
            mov_target = new_path.replace(extension, '.MOV')
            if os.path.exists(mov_orig):
                related_paths.append((mov_orig, mov_target))

        if "已编辑" in tags:
            edited_orig = get_edited_version_path(normalized_path)
            if edited_orig and os.path.exists(edited_orig):
                edited_target = os.path.join(target_folder, os.path.basename(edited_orig))
                related_paths.append((edited_orig, edited_target))

        # 检查是否有任何目标路径冲突（重命名后缀 _n）
        conflict = any(os.path.exists(t) for _, t in related_paths)
        if conflict:
            related_paths_new = []
            for src, tgt in related_paths:
                b, e = os.path.splitext(os.path.basename(tgt))
                renamed = os.path.join(target_folder, f"{b}_n{e}")
                related_paths_new.append((src, renamed))
            related_paths = related_paths_new
            print(f"\n存在文件名冲突，统一重命名为 _n：\n{[t for _, t in related_paths]}")

        # 执行移动
        for src, tgt in related_paths:
            if os.path.exists(src):
                shutil.move(src, tgt)
                print(f"✅ 已移动：{src} → {tgt}")
            else:
                print(f"⚠️ 未找到源文件：{src}")

        # 只更新主图的新路径到 JSON
        if os.path.exists(related_paths[0][1]):  # related_paths[0] 是主图
            new_main_path = related_paths[0][1].replace('\\', '/')
            updated_classifications[new_main_path] = tags

        # 删除旧主图路径
        if original_path in updated_classifications:
            del updated_classifications[original_path]


    except Exception as e:
        print(f"\n处理文件 {original_path} 时发生错误：{e}")

    # 进度打印
    progress = (current_file / total_files) * 100
    print_progress(progress)

total_files = len(classifications)
current_file = 0

# 遍历并处理文件
for original_path, tags in classifications.items():
    current_file += 1
    move_and_update(original_path, tags, total_files, current_file)

# 将更新后的路径写回JSON文件
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(updated_classifications, f, indent=4, ensure_ascii=False)

print("\n所有文件处理完毕，JSON文件已更新。")
