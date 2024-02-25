
import tkinter as tk
from tkinter import ttk, messagebox
import heic2jpg  # 处理HEIC到JPG转换的脚本
import sorter  # 图片分类器的脚本
import album  # 分类相册浏览的脚本

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('图片处理工具')
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
        # ttk.Button(frame, text='移动已分类的图片到指定文件夹', command=self.open_pic_mover).pack(pady=5, fill=tk.X)

        # 自定义按钮样式
        self.style.configure('TButton', font=('Helvetica', 12), borderwidth=1)
        self.style.map('TButton', foreground=[('active', 'blue')], background=[('active', 'lightgrey')])

    def open_sorter(self):
        # 创建一个新的Toplevel窗口
        sorter_window = tk.Toplevel(self)
        sorter_window.title("图片分类器")
        # 调用sorter.py中的PhotoClassifier，使用新的Toplevel窗口作为其父窗口
        app = sorter.PhotoClassifier(sorter_window)

    def open_album(self):
        # 创建一个新的Toplevel窗口
        album_window = tk.Toplevel(self)
        album_window.title("分类相册")
        # 初始化ClassifiedPhotoAlbum类的实例，使用新的Toplevel窗口作为其父窗口
        app = album.ClassifiedPhotoAlbum(album_window, "classifications.json")

    def convert_heic(self):
        # 使用tkinter的filedialog让用户选择目录
        folder_selected = tk.filedialog.askdirectory()
        
        if folder_selected:
            # 调用转换函数
            heic2jpg.convert_heic_to_jpg_and_remove_original(folder_selected)
            
            # 弹出消息框通知用户转换完成
            tk.messagebox.showinfo("完成", "所有HEIC文件已转换并删除原文件。")
        else:
            tk.messagebox.showinfo("提示", "没有选择目录。")

    def open_pic_mover(self):
        folder_selected = tk.filedialog.askdirectory()
        if folder_selected:
            # 调用move函数
            #heic2jpg.convert_heic_to_jpg_and_remove_original(folder_selected)
            
            # 弹出消息框通知用户转换完成
            tk.messagebox.showinfo("完成", "所有文件已移动完成。")
        else:
            tk.messagebox.showinfo("提示", "没有选择目录。")


def main():
    app = MainApplication()
    app.mainloop()

if __name__ == '__main__':
    main()
