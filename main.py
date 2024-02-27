import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import heic2jpg  # 处理HEIC到JPG转换的脚本
import sorter  # 图片分类器的脚本
import album  # 分类相册浏览的脚本
import find_similar_pic  # 查找相似图片的脚本
import del_similar_pic  # 手动选择并删除相似照片的脚本

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('图片分类、处理、查看工具')
        self.geometry('400x300')

        # 设置样式
        self.style = ttk.Style(self)
        self.style.theme_use('clam')  # 选择一个主题

        # 初始化UI
        self.init_ui()

    def init_ui(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(expand=True, fill=tk.BOTH)

        # 创建并配置按钮
        ttk.Button(frame, text='图片分类器', command=self.open_sorter).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text='分类浏览相册', command=self.open_album).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text='转换指定文件夹中的HEIC到JPG', command=self.convert_heic).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text='查找相似图片', command=self.open_find_similar_pic).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text='手动选择并删除相似照片', command=self.open_del_similar_pic).pack(pady=5, fill=tk.X)
        
        # 自定义按钮样式
        self.style.configure('TButton', font=('Helvetica', 12), borderwidth=1)
        self.style.map('TButton', foreground=[('active', 'blue')], background=[('active', 'lightgrey')])

    def hide_main_windows(self, kid):
        self.withdraw()
        def on_closing():
            # 重新显示主窗口
            self.deiconify()
            kid.destroy()
        kid.protocol("WM_DELETE_WINDOW", on_closing)

    def open_sorter(self):
        sorter_window = tk.Toplevel(self)
        self.hide_main_windows(sorter_window)
        sorter_window.title("图片分类器")
        app = sorter.PhotoClassifier(sorter_window)
        

    def open_album(self):
        album_window = tk.Toplevel(self)
        self.hide_main_windows(album_window)
        album_window.title("分类相册")
        app = album.ClassifiedPhotoAlbum(album_window, "jsondata/classifications.json")

    def convert_heic(self):
        folder_selected = tk.filedialog.askdirectory()
        if folder_selected:
            heic2jpg.convert_heic_to_jpg_and_remove_original(folder_selected)
            tk.messagebox.showinfo("完成", "所有HEIC文件已转换并删除原文件。")
        else:
            tk.messagebox.showinfo("提示", "没有选择目录。")

    def open_find_similar_pic(self):
        similar_pic_window = tk.Toplevel(self)
        self.hide_main_windows(similar_pic_window)
        similar_pic_window.title("查找相似图片")
        app = find_similar_pic.ImageHashGUI(similar_pic_window)

    def open_del_similar_pic(self):
        del_similar_pic_window = tk.Toplevel(self)
        self.hide_main_windows(del_similar_pic_window)
        del_similar_pic_window.title("手动选择并删除相似照片")
        app = del_similar_pic.ImageReviewer(del_similar_pic_window)

def main():
    app = MainApplication()
    app.mainloop()

if __name__ == '__main__':
    main()
