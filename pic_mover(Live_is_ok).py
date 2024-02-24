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
json_file_path = 'classifications.json'

# 加载JSON文件
with open(json_file_path, 'r', encoding='utf-8') as f:
    classifications = json.load(f)

updated_classifications = {}

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
    new_path = os.path.join(target_folder, filename)

    # 检查文件是否已经在目标文件夹中
    if os.path.abspath(normalized_path).lower() == os.path.abspath(new_path).lower():
        print(f"\n文件已在目标文件夹中，跳过：{normalized_path}")
        updated_classifications[original_path] = tags  # 保持原始路径不变
        return

    try:
        # 确保源文件存在
        if not os.path.exists(normalized_path):
            print(f"\n找不到源文件：{normalized_path}")
            return

        # 检查目标文件夹中是否存在同名文件，如果存在且内容不一致，则重命名新文件
        if os.path.exists(new_path):
            if not filecmp.cmp(normalized_path, new_path, shallow=False):
                new_filename = f"{base}_new{extension}"
                new_path = os.path.join(target_folder, new_filename)
                print(f"\n文件冲突，重命名并移动：{original_path} -> {new_path}")
            else:
                # 如果内容一致，删除源文件
                os.remove(normalized_path)
                print(f"\n源文件与目标文件内容一致，已删除源文件：{normalized_path}")
                updated_classifications[new_path.replace('\\', '/')] = tags
                return

        shutil.move(normalized_path, new_path)
        print(f"\n成功移动文件：{original_path} -> {new_path}")

        # 检查并移动对应的.MOV文件（若存在）
        mov_path = normalized_path.replace(extension, '.MOV')
        if os.path.exists(mov_path):
            mov_new_path = new_path.replace(extension, '.MOV')
            if not os.path.exists(mov_new_path):
                shutil.move(mov_path, mov_new_path)
                print(f"\n同时移动了.MOV文件：{mov_path} -> {mov_new_path}")
            else:
                print(f"\n目标路径已存在MOV文件，操作取消：{mov_new_path}")
            if "Live" not in tags:
                tags.append("Live")

        # 成功移动后更新JSON
        updated_classifications[new_path.replace('\\', '/')] = tags

    except Exception as e:
        print(f"\n处理文件 {original_path} 时发生错误：{e}")

    # 打印进度
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
