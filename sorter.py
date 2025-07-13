from pathlib import Path
import subprocess
from tkinter import filedialog, messagebox, ttk, Frame
import cv2
import os, re
import numpy as np
from tkinter import *
from PIL import Image, ImageTk
import json
import imageio
import pillow_heif
import time
from collections import defaultdict

def is_video_file(file_path):
    video_extensions = ['.mp4', '.avi', '.mov']  # 视频文件扩展名列表
    lower_file_path = file_path.lower()  # 将文件路径转换为小写进行检查
    return any(lower_file_path.endswith(ext) for ext in video_extensions)

def is_gif_file(file_path):
    gif_extensions = ['.gif']  # GIF文件扩展名列表
    lower_file_path = file_path.lower()  # 将文件路径转换为小写进行检查
    return any(lower_file_path.endswith(ext) for ext in gif_extensions)

class PhotoClassifier:
    def __init__(self, master):
        self.master = master
        media_path = self.load_path()  # 加载路径
        rename_ext_to_uppercase_no_conflict(media_path)  # 重命名小写扩展名为大写，避免冲突
        self.labels_file = 'jsondata/labels.json'
        self.labels = self.load_labels()
        self.classifications = self.load_classifications()
        self.media_paths = find_medias(media_path)
        self.live_pics_paths = self.find_live_photos(self.media_paths)
        self.apple_edited_pic_paths = []
        self.apple_original_pic_paths = self.find_apple_edited_origins(self.media_paths)
        


        self.after_id = None
        self.cap = None
        self.video_length = 0
        self.current_media_index = -1
        self.label_buttons = []
        self.key_bindings = "`1234567890-=\\qwertyuiop[]asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+|QWERTYUIOP\{\}ASDFGHJKL:\"ZXCVBNM<>?"  # 按键绑定到分类标签

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

        self.media_path_label = Label(master, text="当前媒体路径：")
        self.media_path_label.pack()

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
        self.master.bind('<Return>', lambda event: self.next_media())
        self.master.bind('<BackSpace>', self.show_prev_media)
        self.master.focus_set()

        self.next_media()

        messagebox.showinfo("欢迎使用照片分类器", "教程内容：\n"
                             "- 使用“修改路径”按钮更改图片文件夹。\n"
                             "- 选择标签对图片进行分类，如风景、小动物、人物等。可以随意添加。\n"
                             "- 使用“下一张”(Enter)和“上一张”(Backspace)按钮在图片间导航。\n"
                             "- 可以通过按键（如 '`', '1', '2'...按照键盘顺序排列）快速选择标签。\n"
                             "- 点击空格可以复制上一张图片的标签。\n"
                             "- “保存并退出”按钮用于保存进度并退出程序。\n"
                             "- 会在当前目录创建jsondata文件夹以存储数据\n"
                             "- 请不要移动照片的位置和改名以确保数据准确。\n")

    def find_live_photos(self, media_paths):
        live_photos = []
        photo_exts = ['.JPG', '.JPEG', '.HEIC']
        
        # 1. 按目录分组文件路径
        folder_files = defaultdict(set)
        for path in media_paths:
            folder = os.path.normpath(os.path.dirname(path))
            filename = os.path.basename(path)
            folder_files[folder].add(filename)

        # 2. 遍历每个文件夹内部的 .mov 文件
        for folder, files in folder_files.items():
            for file in files:
                if file.upper().endswith('.MOV'):
                    name, _ = os.path.splitext(file)
                    for ext in photo_exts:
                        photo_name = name + ext
                        if photo_name in files:
                            photo_path = os.path.normpath(os.path.join(folder, photo_name))
                            mov_path = os.path.normpath(os.path.join(folder, file))
                            live_photos.append((photo_path, mov_path))
                            break  # 找到一个配对就不再尝试其他扩展名

        return live_photos

    def find_apple_edited_origins(self, media_paths):
        """
        在每个子文件夹中查找具有苹果风格编辑命名的图像（如 IMG_E1234.JPG），
        并确认是否有同文件夹内的原图（如 IMG_1234.JPG）存在。
        返回原图路径列表，并更新 self.apple_edited_pic_paths。
        """

        # 1. 按文件夹分组文件名
        folder_to_files = defaultdict(dict)
        for path in media_paths:
            folder = os.path.normpath(os.path.dirname(path))
            filename = os.path.basename(path)
            folder_to_files[folder][filename] = path

        origins = set()
        self.apple_edited_pic_paths = []  # 重置清空（如果是类变量）

        # 2. 遍历每个文件夹内的文件
        for folder, file_map in folder_to_files.items():
            for filename in file_map:
                name, ext = os.path.splitext(filename)

                # 检测是否为编辑图（如 IMG_E1234.JPG）
                match = re.match(r'^(.+?)E(\d.*)$', name)
                if match:
                    orig_name = match.group(1) + match.group(2) + ext
                    if orig_name in file_map:
                        origins.add(file_map[orig_name])  # 添加原图路径
                        self.apple_edited_pic_paths.append(file_map[filename])  # 添加编辑图路径

        return list(origins)

    def save_path(self, new_path):
        data = {'image_path': new_path}
        Path('jsondata/path.json').write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')

    def load_path(self):
        json_data_dir = Path('jsondata')
        path_file = json_data_dir / 'path.json'

        # 检查jsondata文件夹是否存在，如果不存在，则创建它
        if not json_data_dir.exists():
            json_data_dir.mkdir(parents=True, exist_ok=True)

        if path_file.exists():
            data = json.loads(path_file.read_text(encoding='utf-8'))
            return data.get('image_path')
        else:
            messagebox.showinfo("初次使用","请先选择照片存储的文件夹。\n如果已经分类过了，又看到此消息，则代表数据库被删除。请恢复！")
            new_path = filedialog.askdirectory(initialdir = '.')
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
        help_text = """
            保存成功！
            """
        messagebox.showinfo("提示", help_text)

    def next_media(self):
        self.master.focus_force()
        self.master.focus_set()
        self.stop_playing()
        # 保存当前图片的分类
        if self.current_media_index < len(self.media_paths):
            current_media_path = self.media_paths[self.current_media_index]
            selected_labels = [label for label, btn_var in self.label_buttons if btn_var.get()]

            auto_tags = {"Live", "已编辑"}

            # 自动标签判断
            if "Live" not in selected_labels and any(current_media_path == pic_path for pic_path, _ in self.live_pics_paths):
                selected_labels.append("Live")
            if "已编辑" not in selected_labels and any(current_media_path == path for path in self.apple_original_pic_paths):
                selected_labels.append("已编辑")

            # 判断是否包含非自动标签
            non_auto_labels = [label for label in selected_labels if label not in auto_tags]

            # 仅当存在非自动标签时才保存分类
            if non_auto_labels:
                self.classifications[current_media_path] = selected_labels
            else:
                self.classifications.pop(current_media_path, None)


            # 每10张图片保存一次分类结果和进度，或者在最后一张图片时保存
            if self.current_media_index % 10 == 0 or self.current_media_index == len(self.media_paths) - 1:
                self.save_classifications()

        # 尝试找到下一张未分类或空分类的图片
        while self.current_media_index < len(self.media_paths):
            self.current_media_index += 1  # 移动到下一张图片
            if self.current_media_index >= len(self.media_paths):
                messagebox.showinfo("提示","已到最后一张！将显示尚未分类的媒体。")
                self.save_classifications()  # Save at the end
                self.current_media_index = -1
                self.master.after(50,self.next_media)
                break

            next_media_path = self.media_paths[self.current_media_index]
            # 如果是Live照片的视频部分，则跳过
            if next_media_path.endswith('.MOV'):
                if any(next_media_path == mov_path for _, mov_path in self.live_pics_paths):
                    continue  # 跳过这个MOV文件

            # 如果是苹果编辑的照片，则跳过
            if next_media_path in self.apple_edited_pic_paths:
                continue
            Next_pic_selected_labels = self.classifications.get(next_media_path, [])
            # 自动标签判断
            if "Live" not in Next_pic_selected_labels and any(next_media_path == pic_path for pic_path, _ in self.live_pics_paths):
                Next_pic_selected_labels.append("Live")
            if "已编辑" not in Next_pic_selected_labels and any(next_media_path == path for path in self.apple_original_pic_paths):
                Next_pic_selected_labels.append("已编辑")
            self.classifications[next_media_path] = Next_pic_selected_labels

            non_auto_labels = [label for label in Next_pic_selected_labels if label not in auto_tags]
            # 检查下一张图片是否未分类或空分类
            if next_media_path not in self.classifications or not self.classifications[next_media_path] or non_auto_labels == []:
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
        self.update_label_buttons()  # 更新标签按钮的选中状态
        media_path = self.media_paths[self.current_media_index]
        self.media_path_label.config(text=f"当前媒体路径：{media_path}")  # 更新媒体路径标签
        self.display_media(media_path)
        self.update_progress_display()

    def show_prev_media(self, event = None):
        if self.current_media_index > 0:  # 确保有上一张图片可以显示
            if self.media_paths[self.current_media_index-1].endswith('.MOV'):
                if any(self.media_paths[self.current_media_index-1] == mov_path for _, mov_path in self.live_pics_paths):
                    self.current_media_index -= 1
                elif self.media_paths[self.current_media_index-1] in self.apple_edited_pic_paths:
                    self.current_media_index -= 1
            self.current_media_index -= 1
            self.show_media()
            self.update_label_buttons()  # 更新标签按钮的选中状态

    def display_media(self, file_path):
        if is_video_file(file_path):
            self.display_video(file_path)
        elif is_gif_file(file_path):
            self.display_gif(file_path)
        else:
            self.display_photo(file_path)

    def display_gif(self, file_path):
        self.stop_playing()  # 停止之前的播放

        # 使用 imageio 读取 gif 帧和元数据
        try:
            gif_reader = imageio.get_reader(str(file_path))
            gif_frames = [frame for frame in gif_reader]
            fps = gif_reader.get_meta_data().get('fps', 10) * 2  # 获取帧率，默认为10
        except Exception as e:
            print(f"Error reading gif: {e}")
            return

        if not gif_frames:
            print("No frames found in gif.")
            return

        # 转换为 OpenCV 格式（RGB → BGR）
        self.gif_frames = [cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) for frame in gif_frames]
        self.gif_index = 0
        self.gif_delay = int(1000 / fps)  # 计算每帧的延迟时间
        self.play_gif_frame()

    def play_gif_frame(self):
        if not hasattr(self, 'gif_frames') or not self.gif_frames:
            return

        frame = self.gif_frames[self.gif_index]
        h, w = frame.shape[:2]
        new_w, new_h = self.calculate_scale(h, w)

        resized = cv2.resize(frame, (new_w, new_h))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)

        self.media_label.configure(image=imgtk)
        self.media_label.image = imgtk  # 避免被垃圾回收

        self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
        self.after_id = self.master.after(self.gif_delay, self.play_gif_frame)  # 使用帧率计算的延迟时间

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
        frame_skip = int(fps/5)  # 定义跳过的帧数
        frame_skip = 0  # 定义跳过的帧数
        if self.cap:
            ret, frame = self.cap.read()
            h, w = frame.shape[:2]
        new_w,new_h=self.calculate_scale(h,w)
        self.update_frame(frame_skip, new_w,new_h)

    def display_video(self, file_path):
        # 使用系统默认播放器播放视频
        try:
            subprocess.Popen(['start', '', str(file_path)], shell=True)
        except Exception as e:
            messagebox.showerror("错误", f"调用系统播放器失败：{e}")

        self.display_photo('./playing.png')  # 显示一个占位图像，表示正在播放视频

    def calculate_scale(self,h,w):
            target_width = self.pic_target_w
            target_height = self.pic_target_h

                # 计算缩放比例并确保等比例缩放
            scale = min(target_width / w, target_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            return new_w,new_h

    def update_frame(self, frame_skip, new_w, new_h):
        if self.cap and self.cap.isOpened():
            # 跳过指定数量的帧，避免频繁 seek 导致卡顿
            for _ in range(frame_skip):
                self.cap.read()

            ret, frame = self.cap.read()
            if not ret:
                self.stop_playing()
                self.master.after(100, lambda: self.display_video(self.media_paths[self.current_media_index]))
                return

            # 转换颜色并缩放
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            img = Image.fromarray(frame)
            photo_image = ImageTk.PhotoImage(img)

            self.media_label.configure(image=photo_image)
            self.media_label.image = photo_image  # 避免被垃圾回收

            # 简洁稳定的延时策略，确保不卡顿也不频繁
            fps = self.cap.get(cv2.CAP_PROP_FPS) * 2
            delay = min(int(1000 / fps * (frame_skip + 1)), 30)
            self.after_id = self.master.after(delay, lambda: self.update_frame(frame_skip, new_w, new_h))
        else:
            self.display_video(self.media_paths[self.current_media_index])

    def display_photo(self, image_path):
        image_path = Path(image_path)
        ext = image_path.suffix.lower()
        with image_path.open("rb") as f:
            header = f.read(16)
    
        if b'ftypheic' in header or b'ftyphevc' in header:
            ext =  ".heic"
        try:
            if ext == ".heic":
                # 使用 pillow-heif 打开 HEIC 文件
                heif_file = pillow_heif.read_heif(str(image_path))
                img_pil = Image.frombytes(
                    heif_file.mode, 
                    heif_file.size, 
                    heif_file.data
                )
                img = np.array(img_pil)[..., ::-1]  # RGB → BGR for OpenCV compatibility
            else:
                img_data = image_path.read_bytes()
                img_array = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is None:
                    raise IOError("无法加载图片" + str(image_path))
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败：{e}")
            return

        h, w = img.shape[:2]
        new_w, new_h = self.calculate_scale(h, w)
        img = cv2.resize(img, (new_w, new_h))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        self.media_label.imgtk = img_tk
        self.media_label.configure(image=img_tk)


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
        keys_per_row = [14, 12, 11, 10, 14, 12, 11, 10]  # 根据实际情况调整
        row_offsets = [0, 1, 2, 2, 0, 1, 2, 2]  # 每行的偏置值
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
                column = position_in_cycle - total_keys_passed + row_offsets[row]
                # 计算实际的“虚拟”行数，并添加偏置
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

def find_medias(directory):
    supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".heic",
                        ".gif", ".mp4", ".avi", ".mov"}  # 用 set 更快

    media_paths = []

    for root, _, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_formats:
                full_path = os.path.join(root, file)
                media_paths.append(os.path.normpath(full_path))

    return media_paths


def rename_ext_to_uppercase_no_conflict(target_dir):
    """
    遍历目标目录及其子目录，将所有拓展名为小写的文件重命名为大写，
    前提是整个目录树中不会因此产生路径冲突。
    """
    if not os.path.isdir(target_dir):
        print("❌ 无效的目录路径")
        return

    # 1. 收集所有文件路径（规范化）
    all_files = set()
    for root, _, files in os.walk(target_dir):
        for f in files:
            full_path = os.path.normpath(os.path.join(root, f))
            all_files.add(full_path)

    # 2. 生成重命名计划
    rename_map = {}  # 原路径 -> 新路径
    new_paths_set = set()

    for old_path in all_files:
        dir_name, file_name = os.path.split(old_path)
        name, ext = os.path.splitext(file_name)

        if ext and ext[1:].islower():  # 拓展名为小写
            new_file_name = name + ext.upper()
            new_path = os.path.normpath(os.path.join(dir_name, new_file_name))

            # 全局冲突检测
            if new_path in all_files or new_path in new_paths_set:
                print(f"⚠️ 冲突：{old_path} → {new_path} 已存在，跳过")
                continue  # 冲突则跳过

            rename_map[old_path] = new_path
            new_paths_set.add(new_path)

    # 3. 执行重命名
    for old_path, new_path in rename_map.items():
        os.rename(old_path, new_path)
        print(f"✅ {old_path} → {new_path}")

    print(f"\n🎉 共重命名了 {len(rename_map)} 个文件（不含冲突跳过项）")


def main():
    root = Tk()
    app = PhotoClassifier(root)  # 不再需要在这里传递media_paths
    root.mainloop()

if __name__ == "__main__":
    # cv2.ocl.setUseOpenCL(True)
    main()
    
