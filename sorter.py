from pathlib import Path
from tkinter import filedialog, messagebox, ttk, Frame
import cv2
import os
import numpy as np
from tkinter import *
from PIL import Image, ImageTk
import json
import time

def is_video_file(file_path):
    video_extensions = ['.mp4', '.avi', '.mov']  # 视频文件扩展名列表
    lower_file_path = file_path.lower()  # 将文件路径转换为小写进行检查
    return any(lower_file_path.endswith(ext) for ext in video_extensions)

class PhotoClassifier:
    def __init__(self, master):
        self.master = master
        self.labels_file = 'jsondata/labels.json'
        self.labels = self.load_labels()
        self.classifications = self.load_classifications()
        media_path = self.load_path()  # 加载路径
        self.media_paths = find_medias(media_path)
        self.live_pics_paths = self.find_live_photos(self.media_paths)


        self.after_id = None
        self.cap = None
        self.video_length = 0
        self.label_buttons = []
        self.progress_file = 'jsondata/progress.json'
        self.key_bindings = "`1234567890-=\\qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOPASDFGHJKLZXCVBNM"  # 按键绑定到分类标签

        # 获取屏幕分辨率
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        self.pic_target_w = self.screen_width
        self.pic_target_h = self.screen_height*0.6
        self.master.title("照片分类器")
        master.state('zoomed')

        # 创建一个Frame作为容器
        self.path_frame = Frame(master)
        self.path_frame.pack()

        # 将Entry放入Frame
        self.path_entry = Entry(self.path_frame)
        self.path_entry.grid(row=0, column=0)  # 使用grid布局管理器
        self.path_entry.insert(0, self.load_path())  # 显示当前路径

        # 将Button也放入同一个Frame
        self.change_path_button = Button(self.path_frame, text="修改路径", command=self.change_path)
        self.change_path_button.grid(row=0, column=1)  # 放置在Entry旁边

        self.media_label = Label(master)
        self.media_label.pack()

        #标签frame
        self.buttons_frame = Frame(master)
        self.buttons_frame.pack()

        self.init_label_buttons()

        self.add_lable_frame = Frame(master)
        self.add_lable_frame.pack()

        self.new_label_entry = Entry(self.add_lable_frame)
        self.new_label_entry.grid(row=0, column=0)

        self.add_label_button = Button(self.add_lable_frame, text="<-添加新分类", command=self.add_new_label)
        self.add_label_button.grid(row=0, column=1)

        self.progress_label = Label(master, text="进度：0/0")
        self.progress_label.pack()

        self.button_frame = Frame(master)
        self.button_frame.pack()

        self.prev_button = Button(self.button_frame, text="上一张(Backspace)", command=self.show_prev_media)
        self.prev_button.grid(row=0, column=0, padx=(0, 5))  # 添加空位

        self.save_all_button = Button(self.button_frame, text="保存进度", command=self.save_all)
        self.save_all_button.grid(row=0, column=1, padx=5)  # 在保存进度和下一张按钮之间添加空位

        self.next_button = Button(self.button_frame, text="下一张(Enter)", command=self.next_media)
        self.next_button.grid(row=0, column=2)

        self.master.bind('<space>', self.copy_last_classification)
        self.master.bind('<Return>', self.next_media)
        self.master.bind('<BackSpace>', self.show_prev_media)

        self.load_progress()
        self.show_media()

        messagebox.showinfo("欢迎使用照片分类器", "教程内容：\n"
                             "- 使用“修改路径”按钮更改图片文件夹。\n"
                             "- 选择标签对图片进行分类，如风景、小动物、人物等。可以随意添加。\n"
                             "- 使用“下一张”(Enter)和“上一张”(Backspace)按钮在图片间导航。\n"
                             "- 可以通过按键（如 '`', '1', '2'...按照键盘顺序排列）快速选择标签。\n"
                             "- 点击空格可以复制上一张图片的标签。\n"
                             "- “保存并退出”按钮用于保存进度并退出程序。\n"
                             "- 会在当前目录创建jsondata文件夹以存储数据\n"
                             "- 请不要移动照片的位置和改名以确保数据准确。\n")

    def find_live_photos(self,media_paths):
        live_photos = []  # 存储找到的Live照片对
        photo_exts = ['.jpg', '.jpeg', '.png', '.heic']  # 常见的图片文件扩展名列表

        for mov_path in media_paths:
            # 只处理.MOV文件
            if mov_path.lower().endswith(".mov"):
                base_path, _ = os.path.splitext(mov_path)

                # 尝试找到与.MOV文件同名的照片文件
                for ext in photo_exts:
                    photo_path = base_path + ext
                    # 检查构造的照片文件路径是否存在于媒体文件列表中
                    # 这里需要确保大小写匹配，因为文件系统可能区分大小写
                    if any(photo_path.lower() == p.lower() for p in media_paths):
                        live_photos.append((photo_path, mov_path))  # 将找到的文件对添加到结果列表中
                        break  # 找到匹配的照片文件后不再继续查找其他扩展名

        return live_photos

    def save_path(self, new_path):
        data = {'image_path': new_path}
        Path('jsondata/path.json').write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

    def load_path(self):
        path_file = Path('jsondata/path.json')
        if path_file.exists():
            data = json.loads(path_file.read_text(encoding='utf-8'))
            return data.get('image_path')
        else:
            new_path = filedialog.askdirectory()
            if new_path:
                self.save_path(new_path)
                return new_path
            else:
                messagebox.showerror("错误", "未选择路径，程序将退出")
                self.master.quit()
                return None

    def change_path(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.save_path(new_path)  # 保存新路径到path.json
            self.path_entry.delete(0, END)
            self.path_entry.insert(0, new_path)  # 更新文本框显示
            self.media_paths = find_medias(new_path)  # 更新图片路径列表
            self.show_media()  # 显示新路径下的第一张图片

    def init_label_buttons(self):
        for i, label in enumerate(self.labels):
            display_text = f"{self.key_bindings[i]}: {label}" if i < len(self.key_bindings) else label
            # 使用默认参数锁定每次循环中lambda表达式的变量值
            self.master.bind(self.key_bindings[i], lambda event, l=label, i=i: self.toggle_label_via_key(l) if i < len(self.key_bindings) else None)
            
            # 使用calculate_row_column_for_new_label来计算行和列
            row, column = self.calculate_row_column_for_new_label(i)
            
            self.add_label_button_gui(label, display_text, row, column)

    def add_label_button_gui(self, label, display_text, row, column):
        btn_var = BooleanVar()
        button = Checkbutton(self.buttons_frame, text=display_text, var=btn_var, command=lambda l=label, bv=btn_var: self.toggle_label(l, bv))
        # 使用grid布局并指定行和列
        button.grid(row=row, column=column, sticky='w')
        self.label_buttons.append((label, btn_var))

    def toggle_label_via_key(self, label):
        for lbl, btn_var in self.label_buttons:
            if lbl == label:
                btn_var.set(not btn_var.get())
                self.toggle_label(label, btn_var)
                break

    def copy_last_classification(self, event):
        if self.current_media_index > 1:  # Ensure there is a last media
            last_media_path = self.media_paths[self.current_media_index - 1]
            last_classification = self.classifications.get(last_media_path, [])
            for label, btn_var in self.label_buttons:
                btn_var.set(label in last_classification)

    def save_all(self):
        self.save_classifications()
        self.save_progress()
        help_text = """
            保存成功！
            """
        messagebox.showinfo("提示", help_text)
        # self.master.destroy()

    def next_media(self):
        # 保存当前图片的分类
        if self.current_media_index < len(self.media_paths):
            current_media_path = self.media_paths[self.current_media_index]
            selected_labels = [label for label, btn_var in self.label_buttons if btn_var.get()]

            # 检查当前照片是否为Live照片，如果是，则自动添加"Live"标签
            if any(current_media_path in pair for pair in self.live_pics_paths):
                selected_labels.append("Live")  # 添加"Live"标签

            # 仅当有选中的标签时，才保存当前图片的分类
            if selected_labels:  # 检查selected_labels非空
                self.classifications[current_media_path] = selected_labels
            else:
                # 如果没有选中的标签，则确保不保存当前图片路径
                self.classifications.pop(current_media_path, None)

            # 每10张图片保存一次分类结果和进度，或者在最后一张图片时保存
            if self.current_media_index % 10 == 0 or self.current_media_index == len(self.media_paths) - 1:
                self.save_classifications()
                self.save_progress()

        # 尝试找到下一张未分类或空分类的图片
        while self.current_media_index < len(self.media_paths):
            self.current_media_index += 1  # 移动到下一张图片
            if self.current_media_index >= len(self.media_paths):
                print("从新开始分类")
                self.save_classifications()  # Save at the end
                self.save_progress(final=True)
                self.current_media_index = 0
                self.show_media()
                break

            next_media_path = self.media_paths[self.current_media_index]
            # 如果是Live照片的视频部分，则跳过
            if any(next_media_path == mov_path for _, mov_path in self.live_pics_paths):
                continue  # 跳过这个MOV文件

            # 检查下一张图片是否未分类或空分类
            if next_media_path not in self.classifications or not self.classifications[next_media_path]:
                self.show_media()
                break

    def update_progress_display(self):
        progress_text = f"进度：{self.current_media_index + 1}/{len(self.media_paths)}"
        self.progress_label.config(text=progress_text)

    def show_media(self):
        # 在显示新图片之前重置所有标签按钮的选中状态
        self.stop_playing()
        for _, btn_var in self.label_buttons:
            btn_var.set(False)
        media_path = self.media_paths[self.current_media_index]
        self.display_media(media_path)
        self.update_progress_display()

    def show_prev_media(self, event = None):
        if self.current_media_index > 0:  # 确保有上一张图片可以显示
            self.current_media_index -= 1
            self.show_media()
            self.update_label_buttons()  # 更新标签按钮的选中状态

    def display_media(self, file_path):
        if is_video_file(file_path):
            self.display_video(file_path)
        else:
            self.display_photo(file_path)

    def stop_playing(self):
        if self.after_id:
            self.master.after_cancel(self.after_id)
            self.after_id = None  # 清除标识符
        if self.cap:
            self.cap.release()  # 释放视频捕获对象
            self.cap = None

    def display_video(self, file_path):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            print("Error opening video stream or file")
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_skip = int(fps/3)  # 定义跳过的帧数
        new_w,new_h=self.calculate_scale()
        self.update_frame(frame_skip, new_w,new_h)

    def calculate_scale(self):
            target_width = self.pic_target_w
            target_height = self.pic_target_h
            if self.cap:
                ret, frame = self.cap.read()
                h, w = frame.shape[:2]
                # 计算缩放比例并确保等比例缩放
                scale = min(target_width / w, target_height / h)
                new_w, new_h = int(w * scale), int(h * scale)
                return new_w,new_h

    def update_frame(self, frame_skip, new_w, new_h):
        if self.cap and self.cap.isOpened():

            start_time = time.time()  # 获取开始时间

            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取视频总帧数
            current_frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))  # 获取当前帧号
            new_frame_number = current_frame_number + frame_skip  # 计算新的帧号

            # 检查计算得出的新帧号是否超出视频总帧数
            if new_frame_number >= total_frames:
                # 如果超出，重置到视频的开始
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                # 否则，设置到计算得出的新帧号
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame_number)

            ret, frame = self.cap.read()  # 尝试读取下一帧
            if not ret:  # 检查是否成功读取到帧
                self.stop_playing()  # 如果没有帧可读，则停止播放
                self.master.after(100, lambda: self.display_video(self.media_paths[self.current_media_index]))
                return

            resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            img = Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB))
            photo_image = ImageTk.PhotoImage(image=img)
            self.media_label.configure(image=photo_image)
            self.media_label.image = photo_image  # 避免垃圾回收

            end_time = time.time()  # 获取结束时间
            
            time2delay = max(((1/self.cap.get(cv2.CAP_PROP_FPS))*(frame_skip+1)-(end_time-start_time))*500,5)
            # print(str({end_time-start_time})+ str({time2delay}))
            # if time2delay < 6:
            #     frame_skip = 0
            # 设置定时器以继续读取下一帧
            self.master.focus_set()  # 将焦点设置到主窗口   
            self.after_id = self.master.after(int(time2delay), lambda: self.update_frame(frame_skip,new_w,new_h))
        else:
            self.display_video(self.media_paths[self.current_media_index])

    def display_photo(self, image_path):
        # 尝试使用pathlib处理路径，以提高兼容性
        image_path = Path(image_path)
        
        # 读取图片文件的二进制数据
        try:
            img_data = image_path.read_bytes()  # 读取图片数据
            img_array = np.frombuffer(img_data, np.uint8)  # 将数据转换为numpy数组
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)  # 用OpenCV解码图片数据
            if img is None:
                raise IOError("无法加载图片"+str(image_path))
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败：{e}")
            return
        w,h = self.calculate_scale()
        # 接下来是图片处理和显示的代码
        img = cv2.resize(img, (w, h))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 将BGR转换为RGB
        img_pil = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        self.image_label.imgtk = img_tk
        self.image_label.configure(image=img_tk)

    def add_new_label(self):
        new_label = self.new_label_entry.get().strip()
        if new_label and new_label not in self.labels:
            self.labels.append(new_label)
            self.save_labels()  # 保存新的标签列表到文件

            # 为新标签计算按键绑定（如果可用）
            key_binding_index = len(self.labels) - 1  # 新标签的索引
            if key_binding_index < len(self.key_bindings):
                display_text = f"{self.key_bindings[key_binding_index]}: {new_label}"
                # 绑定按键事件
                self.master.bind(self.key_bindings[key_binding_index], lambda event, l=new_label: self.toggle_label_via_key(l))
            else:
                display_text = new_label  # 没有可用的按键绑定

            # 计算新标签应该放在哪一行哪一列
            row, column = self.calculate_row_column_for_new_label(key_binding_index)

            # 添加新的标签按钮
            self.add_label_button_gui(new_label, display_text, row, column)
            self.new_label_entry.delete(0, 'end')  # 清空输入框

            # 将焦点移到主窗口
            self.master.focus_set()

    def calculate_row_column_for_new_label(self, key_binding_index):
        # 定义每行最多放置的按键数量
        keys_per_row = [14, 12, 11, 10]  # 根据实际情况调整
        total_keys = sum(keys_per_row)

        # 计算key_binding_index所在的“虚拟”总行数和列数
        # 首先，找出key_binding_index属于第几个完整的键盘布局循环
        cycle_index = key_binding_index // total_keys
        # 然后，找出在当前循环中的具体位置
        position_in_cycle = key_binding_index % total_keys

        total_keys_passed = 0
        # 使用与原始方法相同的逻辑，但是应用于“虚拟”的位置
        for row, keys_count in enumerate(keys_per_row):
            if position_in_cycle < total_keys_passed + keys_count:
                # 计算列位置
                column = position_in_cycle - total_keys_passed
                # 计算实际的“虚拟”行数
                actual_row = row + len(keys_per_row) * cycle_index
                return actual_row, column
            total_keys_passed += keys_count

        # 理论上，由于循环的设计，这个返回应该永远不会被执行
        return len(keys_per_row) - 1, position_in_cycle - total_keys_passed

    def update_label_buttons(self):
        if self.current_media_index < len(self.media_paths):
            current_media_path = self.media_paths[self.current_media_index]
            selected_labels = self.classifications.get(current_media_path, [])
            for label, btn_var in self.label_buttons:
                btn_var.set(label in selected_labels)

    def toggle_label(self, label, btn_var):
        print(f"分类 {label} 被 {'选定' if btn_var.get() else '取消选定'}。")

    def save_classifications(self):
        with open('jsondata/classifications.json', 'w', encoding='utf-8') as json_file:
            json.dump(self.classifications, json_file, ensure_ascii=False, indent=4)
        print("分类结果已保存到 jsondata/classifications.json")

    def load_classifications(self):
        try:
            with open('jsondata/classifications.json', 'r', encoding='utf-8') as json_file:  # 指定文件编码为utf-8
                return json.load(json_file)
        except FileNotFoundError:
            return {}

    def save_labels(self):
        with open(self.labels_file, 'w', encoding='utf-8') as json_file:
            json.dump(self.labels, json_file, ensure_ascii=False, indent=4)

    def load_labels(self):
        try:
            with open(self.labels_file, 'r', encoding='utf-8') as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            return []

    def save_progress(self, final=False):
        progress = {'current_media_index': 0 if final else self.current_media_index}
        with open(self.progress_file, 'w') as json_file:
            json.dump(progress, json_file)

    def load_progress(self):
        try:
            with open(self.progress_file, 'r') as json_file:
                progress = json.load(json_file)
                self.current_media_index = progress.get('current_media_index', 0)
        except FileNotFoundError:
            self.current_media_index = 0

def find_medias(directory):
    # supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".jp2"]
    supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".jp2", ".mp4", ".avi", ".mov"]  # 添加视频格式
    media_paths = [os.path.join(dp, f) for dp, dn, filenames in os.walk(directory) for f in filenames if os.path.splitext(f)[1].lower() in supported_formats]
    return media_paths

def main():
    root = Tk()
    app = PhotoClassifier(root)  # 不再需要在这里传递media_paths
    root.mainloop()

if __name__ == "__main__":
    # cv2.ocl.setUseOpenCL(True)
    main()
    
