import tkinter as tk
from tkinter import filedialog
import os

def is_folder_empty(path):
    # 检查文件夹是否为空
    if os.path.exists(path) and os.path.isdir(path):
        if not os.listdir(path):  # 空文件夹
            return True
    return False

def remove_empty_folders(path, remove_root=True):
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if is_folder_empty(dir_path):
                os.rmdir(dir_path)
                print(f"删除空文件夹：{dir_path}")
                # 检查并递归删除空的上级文件夹
                if remove_root:
                    parent_path = os.path.dirname(dir_path)
                    while parent_path != path and is_folder_empty(parent_path):
                        os.rmdir(parent_path)
                        print(f"递归删除上级空文件夹：{parent_path}")
                        parent_path = os.path.dirname(parent_path)

def select_folder_and_clean():
    root = tk.Tk()
    root.withdraw()  # 不显示主窗口
    folder_selected = filedialog.askdirectory()  # 让用户选择文件夹
    if folder_selected:  # 如果用户选择了文件夹
        remove_empty_folders(folder_selected, remove_root=False)
        print("空文件夹清理完成。")
    else:
        print("没有选择文件夹。")

if __name__ == "__main__":
    select_folder_and_clean()
