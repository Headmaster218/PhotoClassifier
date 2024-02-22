import tkinter as tk
from tkinter import filedialog
import os
import subprocess

def convert_heic_to_jpg_and_remove_original(root_dir):
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(".heic"):
                full_path = os.path.join(subdir, file)
                base_name = os.path.splitext(full_path)[0]
                jpg_path = base_name + ".jpg"
                
                # 使用ImageMagick转换文件
                cmd = f'magick convert "{full_path}" "{jpg_path}"'
                try:
                    subprocess.run(cmd, check=True, shell=True)
                    print(f"转换完成并准备删除原文件：{full_path}")
                    # 成功转换后删除原.heic文件
                    os.remove(full_path)
                    print(f"已删除原文件：{full_path}")
                except subprocess.CalledProcessError as e:
                    print(f"转换失败：{full_path}, 错误：{e}")

def select_folder_and_convert():
    root = tk.Tk()
    root.withdraw() # 不显示Tkinter主窗口
    folder_selected = filedialog.askdirectory() # 让用户选择目录
    if folder_selected:
        convert_heic_to_jpg_and_remove_original(folder_selected)
        print("所有HEIC文件已转换并删除原文件。")
    else:
        print("没有选择目录。")

if __name__ == "__main__":
    select_folder_and_convert()
