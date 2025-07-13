import threading
import time
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk, UnidentifiedImageError, ImageDraw, ImageFont, ImageSequence
import pillow_heif  # 加载 pillow-heif 插件
import numpy as np
import cv2
import json
from pypinyin import lazy_pinyin  # Import lazy_pinyin for pinyin sorting
import os, re  # 用于文件路径处理和正则表达式匹配
import shutil  # 用于文件复制

class PhotoViewer(tk.Toplevel):
    def __init__(self, master, photo_path, all_categories, photo_categories, update_callback):
        super().__init__(master)
        self.photo_path = photo_path
        self.all_categories = all_categories
        self.photo_categories = photo_categories
        self.update_callback = update_callback

        self.title(os.path.basename(photo_path))
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        self.pic_target_w = self.screen_width * 0.6  # Adjusted width to 60% of screen width
        self.pic_target_h = self.screen_height * 0.85  # Adjusted height to 85% of screen height
        self.geometry(f"{int(self.pic_target_w)}x{int(self.pic_target_h)+100}")  # Dynamically set window size

        # 使用open以二进制方式读取图片数据
        with open(photo_path, 'rb') as file:
            img_data = file.read()
            img_array = np.asarray(bytearray(img_data), dtype=np.uint8)
            self.cv_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)  # 使用cv2.IMREAD_COLOR确保图像是以彩色模式读取

        # 确保图像非空
        if self.cv_img is not None:
            # 只需要进行一次颜色空间转换
            self.cv_img = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
            self.img_height, self.img_width = self.cv_img.shape[:2]

        # 初始化图像缩放比例和位置
        self.scale = 1.0
        self.calculate_initial_scale()
        self.image_position_x = (self.pic_target_w - self.img_width * self.scale) / 2
        self.image_position_y = (self.pic_target_h - self.img_height * self.scale) / 2

        self.canvas = tk.Canvas(self, width=self.pic_target_w, height=self.pic_target_h, bg='black')
        self.canvas.pack()

        # 绑定滚轮事件用于缩放
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        # 绑定鼠标事件用于平移
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan_image)
        self.canvas.bind("<ButtonPress-3>", self.show_edited_image)
        self.canvas.bind("<ButtonRelease-3>", self.restore_original_image)



        self.display_image()

        categories_str = ", ".join(self.photo_categories)
        self.info_label = tk.Label(self, text=f"当前分类: {categories_str}")
        self.info_label.pack()

        self.change_category_button = tk.Button(self, text="修改分类", command=self.change_category)
        self.change_category_button.pack()

    def show_edited_image(self, event):
        fname = os.path.basename(self.photo_path)
        name, ext = os.path.splitext(fname)

        match = re.match(r'^(.+?)(\d+)$', name)
        if not match:
            return  # 当前不是原图命名，不操作

        edited_name = match.group(1) + 'E' + match.group(2) + ext
        edited_path = os.path.join(os.path.dirname(self.photo_path), edited_name)

        if os.path.exists(edited_path):
            with open(edited_path, 'rb') as file:
                img_data = file.read()
                img_array = np.asarray(bytearray(img_data), dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self.display_temp_image(img)

    def restore_original_image(self, event):
        self.display_temp_image(self.cv_img)

    def display_temp_image(self, img_array):
        img_height, img_width = img_array.shape[:2]
        resized_img = cv2.resize(img_array, (int(img_width * self.scale), int(img_height * self.scale)), interpolation=cv2.INTER_LINEAR)
        pil_img = Image.fromarray(resized_img)
        self.photo_image = ImageTk.PhotoImage(image=pil_img)

        self.canvas.delete("all")
        self.canvas.create_image(self.image_position_x, self.image_position_y, anchor="nw", image=self.photo_image)

    def calculate_initial_scale(self):
        # 根据窗口大小计算初始缩放比例
        scale_x = self.pic_target_w / self.img_width
        scale_y = self.pic_target_h / self.img_height
        self.scale = min(scale_x, scale_y)

    def zoom_image(self, event):
        # 计算缩放比例并更新图像位置，以鼠标位置为缩放中心
        x = event.x - self.image_position_x
        y = event.y - self.image_position_y
        old_scale = self.scale
        scale_change = 1.1 if event.delta > 0 else 0.9
        self.scale *= scale_change

        self.image_position_x = event.x - x * scale_change
        self.image_position_y = event.y - y * scale_change

        self.display_image()

    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan_image(self, event):
        self.image_position_x += event.x - self.pan_start_x
        self.image_position_y += event.y - self.pan_start_y

        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.display_image()

    def display_image(self):
        resized_img = cv2.resize(self.cv_img, (int(self.img_width * self.scale), int(self.img_height * self.scale)), interpolation=cv2.INTER_LINEAR)
        pil_img = Image.fromarray(resized_img)
        self.photo_image = ImageTk.PhotoImage(image=pil_img)

        self.canvas.delete("all")
        self.canvas.create_image(self.image_position_x, self.image_position_y, anchor="nw", image=self.photo_image)

    def change_category(self):
        initial_category = ", ".join(self.photo_categories)
        new_category = simpledialog.askstring("修改分类", "输入新的分类名(多个分类用逗号分隔):", initialvalue=initial_category, parent=self)
        if new_category is not None:
            # 自动替换中英文逗号
            new_category = new_category.replace('，', ',')
            # 检查非法符号
            illegal_chars = set("!@#$%^&*()_+=[]{};:'\"\\|<>/?")
            if any(char in illegal_chars for char in new_category):
                messagebox.showerror("错误", "分类名中包含非法字符，请重新输入。")
                return
            # 分割并去除空格
            new_categories = [c.strip() for c in new_category.split(',')]
            # 检查是否所有分类都存在
            if not all(c in self.all_categories or c == "" for c in new_categories):
                messagebox.showerror("错误", "输入了不存在的分类，请检查后重新输入。")
                return
            if set(new_categories) != set(self.photo_categories):
                self.photo_categories = new_categories
                self.update_callback(self.photo_path, new_categories)
                self.info_label.config(text=f"当前分类: {', '.join(new_categories)}")

class ClassifiedPhotoAlbum:
    def __init__(self, master, classifications_file):
        self.master = master
        self.classifications_file = classifications_file
        self.photos = self.load_classifications()
        self.all_categories = self.get_all_categories()
        self.stop_video_flag = threading.Event()
        self.photo_images = []
        self.current_category_photos = []  # 初始化为空列表
        self.currently_playing_widget = None  # 追踪当前播放视频的widget

        # 获取屏幕分辨率
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        self.rows = 3
        self.columns = 6
        self.target_thumb_size = int((self.screen_width-100)/6),int((self.screen_height*0.85)/3)
        self.photos_per_page = self.rows * self.columns
        self.current_page = 0

        self.master.state('zoomed')

        # 筛选条件UI设置
        filter_frame = tk.Frame(master)
        filter_frame.pack(fill=tk.X)

        tk.Label(filter_frame, text="分类1:").pack(side=tk.LEFT, padx=5)
        self.category_combobox1 = ttk.Combobox(filter_frame, state="readonly", postcommand=self.update_comboboxes)
        tk.Label(filter_frame, text="条件:").pack(side=tk.LEFT, padx=5)
        self.filter_type_combobox = ttk.Combobox(filter_frame, state="readonly", values=["照片中既有又有", "照片中有任一", "只有前面没有后面", "无"])
        tk.Label(filter_frame, text="分类2:").pack(side=tk.LEFT, padx=5)
        self.category_combobox2 = ttk.Combobox(filter_frame, state="readonly")

        self.category_combobox1.pack(side=tk.LEFT, padx=5)
        self.filter_type_combobox.pack(side=tk.LEFT, padx=5)
        self.filter_type_combobox.bind("<<ComboboxSelected>>", self.filter_type_selected)
        self.category_combobox2.pack(side=tk.LEFT, padx=5)

        self.export_button = tk.Button(filter_frame, text="导出结果", command=self.export_results)
        self.export_button.pack(side=tk.RIGHT, padx=5)

        # 分页和跳转UI设置
        navigation_frame = tk.Frame(master)
        navigation_frame.pack(fill=tk.X)

        self.prev_page_button = tk.Button(navigation_frame, text="上一页", command=self.show_prev_page)
        self.prev_page_button.pack(side=tk.LEFT, padx=5)

        self.page_info_label = tk.Label(navigation_frame, text="页码: 1/1")
        self.page_info_label.pack(side=tk.LEFT, padx=5)

        self.next_page_button = tk.Button(navigation_frame, text="下一页", command=self.show_next_page)
        self.next_page_button.pack(side=tk.LEFT, padx=5)

        self.goto_page_entry = ttk.Entry(navigation_frame, width=5)
        self.goto_page_entry.pack(side=tk.LEFT, padx=5)

        self.goto_page_button = tk.Button(navigation_frame, text="跳转", command=self.goto_page)
        self.goto_page_button.pack(side=tk.LEFT, padx=5)

        # 在 __init__ 方法中创建 photos_frame
        self.photos_frame = tk.Frame(self.master)
        self.photos_frame.pack(expand=True, fill=tk.BOTH)

        # 更新所有下拉框的选项
        self.update_comboboxes()

        messagebox.showinfo("使用说明", "欢迎使用分类相册应用！\n\n"
                                "1. 从左上角下拉框来选择想看的图片。\n"
                                "2. 点击图片可以查看大图。\n"
                                "3. 大图界面使用滚轮缩放图片。\n"
                                "4. 大图界面拖动鼠标平移图片。\n"
                                "5. 大图界面点击'修改分类'按钮来更新图片分类。\n"
                                "6. 将鼠标悬停在带有'Live'标签的图片上可以预览视频。\n"
                                "7. 使用导出结果按钮来导出当前筛选的图片。\n\n"
                                "请尽情探索更多功能！")

    def category_selected(self, event=None):
        filter_type = self.filter_type_combobox.get()
        category1 = self.category_combobox1.get()
        category2 = self.category_combobox2.get()

        if filter_type == "无":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels]
        elif filter_type == "照片中既有又有":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels and category2 in labels]
        elif filter_type == "照片中有任一":
            if category2 == "无":  # 如果第二个分类是"无"，则仅根据第一个分类筛选
                self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels]
            else:  # 否则，检查照片是否含有任一分类
                self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels or category2 in labels]
        elif filter_type == "只有前面没有后面":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels and category2 not in labels]

        self.current_page = 0
        self.display_photos()

    def update_comboboxes(self):
        all_categories = ["无"] + self.get_all_categories()
        self.category_combobox1['values'] = all_categories
        self.category_combobox2['values'] = all_categories
        self.category_combobox1.bind("<<ComboboxSelected>>", self.category_selected)
        self.category_combobox2.bind("<<ComboboxSelected>>", self.category_selected)
        self.filter_type_combobox.bind("<<ComboboxSelected>>", self.filter_type_selected)

    def filter_type_selected(self, event=None):
        self.category_selected()
        if self.filter_type_combobox.get() == "无":
            self.category_combobox2.set("无")
            self.category_combobox2['state'] = 'disabled'
        else:
            self.category_combobox2['state'] = 'readonly'

    def export_results(self):
        export_folder = filedialog.askdirectory()
        if export_folder:
            # 加载分类信息
            self.photos = self.load_classifications()

            for photo_path in self.current_category_photos:
                # 复制照片
                shutil.copy(photo_path, os.path.join(export_folder, os.path.basename(photo_path)))

                # 检查是否有'Live'属性
                photo_tags = self.photos.get(photo_path)
                if photo_tags and "Live" in photo_tags:
                    # 构建同名.MOV文件的路径
                    base, ext = os.path.splitext(photo_path)
                    mov_path = f"{base}.MOV"

                    # 检查.MOV文件是否存在
                    if os.path.exists(mov_path):
                        # 复制.MOV文件
                        shutil.copy(mov_path, os.path.join(export_folder, os.path.basename(mov_path)))

            messagebox.showinfo("导出完成", f"已导出到{export_folder}")

    def update_pagination_info(self):
        total_pages = max(1, (len(self.current_category_photos) - 1) // self.photos_per_page + 1)
        self.page_info_label.config(text=f"页码: {self.current_page + 1}/{total_pages}")

    def goto_page(self):
        try:
            page = int(self.goto_page_entry.get()) - 1
            if 0 <= page < (len(self.current_category_photos) // self.photos_per_page + 1):
                self.current_page = page
                self.display_photos()
            else:
                messagebox.showerror("错误", "无效的页码")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的页码数字")

    def load_classifications(self):
        with open(self.classifications_file, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_all_categories(self):
        categories = {}
        for labels in self.photos.values():
            for label in labels:
                categories[label] = None  # 使用 None 作为值，因为我们只关心键的顺序
        return sorted(categories.keys(), key=lambda x: lazy_pinyin(x))

    def display_photos(self):
        for widget in self.photos_frame.winfo_children():
            widget.destroy()
        self.photo_images.clear()

        start = self.current_page * self.photos_per_page
        end = start + self.photos_per_page
        photos_to_display = self.current_category_photos[start:end]

        for index, photo_path in enumerate(photos_to_display):
            row = index // self.columns
            column = index % self.columns
            file_extension = os.path.splitext(photo_path)[1].lower()
            photo_tags = self.photos.get(photo_path, [])


            if file_extension in ['.jpg', '.jpeg', '.png', '.heic']:  # 增加 HEIC 支持
                try:
                    if file_extension == '.heic':
                        heif_file = pillow_heif.read_heif(photo_path)
                        img = Image.frombytes(
                            heif_file.mode,
                            heif_file.size,
                            heif_file.data
                        )
                    else:
                        img = Image.open(photo_path)

                    img.thumbnail(self.target_thumb_size)

                    # 处理标签
                    
                    draw = ImageDraw.Draw(img, "RGBA")

                    if "Live" in photo_tags:
                        font = ImageFont.truetype("arial.ttf", 20)
                        text = "Live"
                        _, _, textwidth, textheight = font.getbbox(text)
                        draw.rectangle([(5, 5), (5 + textwidth + 10, 5 + textheight + 10)], fill=(255, 255, 255, 128))
                        draw.text((10, 10), text, fill=(255, 0, 0, 255), font=font)

                    if "已编辑" in photo_tags:
                        font = ImageFont.truetype("arial.ttf", 20)
                        text = "Edited"
                        _, _, textwidth, textheight = font.getbbox(text)
                        draw.rectangle([(70, 5), (70 + textwidth + 10, 5 + textheight + 10)], fill=(255, 255, 255, 128))
                        draw.text((75, 10), text, fill=(0, 255, 0, 255), font=font)

                    photo_image = ImageTk.PhotoImage(img)
                    self.photo_images.append(photo_image)

                except (FileNotFoundError, UnidentifiedImageError) as e:
                    img = Image.new('RGB', self.target_thumb_size, color='gray')
                    photo_image = ImageTk.PhotoImage(img)
                    self.photo_images.append(photo_image)
                    print(f"❌ Error loading image: {photo_path} | {e}")

            elif file_extension == '.gif':
                try:
                    img = Image.open(photo_path)
                    img.seek(0)  # 确保定位到第一帧
                    img = img.convert("RGB")  # 转换为 RGB 模式（避免 palette）
                    img.thumbnail(self.target_thumb_size)

                except Exception as e:
                    print(f"GIF 加载失败: {e}")
                    img = Image.new('RGB', self.target_thumb_size, color='black')
                    draw = ImageDraw.Draw(img)
                    draw.text((10, 10), "Error loading gif", fill="white")

                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial.ttf", 20)
                text = "GIF"
                textwidth, textheight = draw.textbbox((0, 0), text, font=font)[2:4]
                draw.rectangle([(5, 5), (5 + textwidth + 10, 5 + textheight + 10)], fill=(255,255,255,128))
                draw.text((10, 10), text, fill=(0,255,255,255), font=font)
                photo_image = ImageTk.PhotoImage(img)
                self.photo_images.append(photo_image)


            elif file_extension in ['.mp4', '.mov']:  # 视频文件
                cap = cv2.VideoCapture(photo_path)
                ret, frame = cap.read()  # 读取第一帧
                if ret:
                    # 将第一帧转换为PIL图像并缩略
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img.thumbnail(self.target_thumb_size)
                else:
                    # 如果无法读取视频，显示一个黑色的占位符
                    img = Image.new('RGB', self.target_thumb_size, color='black')
                    draw = ImageDraw.Draw(img)
                    draw.text((10, 10), "Error loading video", fill="white")
                cap.release()
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial.ttf", 20)  # 指定字体和大小
                text = "Video"
                textwidth, textheight = draw.textbbox((0, 0), text, font=font)[2:4]  # 获取文本宽高
                # 在图片上绘制半透明矩形作为文本背景
                draw.rectangle([(5, 5), (5 + textwidth + 10, 5 + textheight + 10)], fill=(255,255,255,128))
                # 在半透明矩形上绘制文本
                draw.text((10, 10), text, fill=(0,255,0,255), font=font)
                photo_image = ImageTk.PhotoImage(img)
                self.photo_images.append(photo_image)

            button = tk.Button(self.photos_frame, image=photo_image, command=lambda p=photo_path: self.open_photo_viewer(p))
            button.grid(row=row, column=column, padx=5, pady=5)

            if "Live" in photo_tags or file_extension in ['.mp4', '.mov', '.gif']:
                button.bind("<Enter>", lambda event, path=photo_path: self.start_live_video(event, path))
                button.bind("<Leave>", lambda event: self.stop_live_video())

        self.update_pagination_info()

    def start_live_video(self, event, file_path):
        # 如果有视频正在播放，先停止它
        if self.currently_playing_widget:
            self.stop_live_video()

        self.stop_video_flag.clear()  # 清除停止标志以开始播放

        # 检查文件类型
        base, extension = os.path.splitext(file_path)
        if extension.lower() in ['.jpg', '.jpeg', '.png']:
            # 如果是图片文件，查找对应的MOV视频文件
            video_path = f"{base}.MOV"
        elif extension.lower() in ['.mp4', '.mov', '.gif']:
            # 如果直接是MP4视频文件
            video_path = file_path
        else:
            # 如果不是支持的文件类型，则不进行操作
            return

        # 确认视频文件存在
        if not os.path.exists(video_path):
            print("Video file does not exist:", video_path)
            return

        # 记录当前播放视频的widget
        self.currently_playing_widget = event.widget
        # 使用传入的视频文件路径启动视频播放线程
        video_thread = threading.Thread(target=self.play_video, args=(video_path, event.widget,))
        video_thread.start()

    def stop_live_video(self):
        if self.currently_playing_widget:
            self.stop_video_flag.set()  # 设置停止标志以停止视频播放
            # 等待视频播放线程结束，或者设置一定超时时间
            if hasattr(self, 'video_thread') and self.video_thread.is_alive():
                self.video_thread.join(timeout=0.1)  # 等最多 0.5s 让其退出
            # 恢复原始图片
            original_image = self.currently_playing_widget.cget("image")
            self.currently_playing_widget.config(image=original_image)
            self.currently_playing_widget.image = original_image
            self.currently_playing_widget = None

    def play_video(self, video_path, widget):

            original_image = widget.cget("image")
            ext = os.path.splitext(video_path)[1].lower()

            if ext == ".gif":
                try:
                    gif = Image.open(video_path)
                    frames = []
                    durations = []

                    # 预取所有帧
                    for frame in ImageSequence.Iterator(gif):
                        frames.append(frame.convert("RGB"))
                        durations.append(frame.info.get('duration', 100))  # 毫秒

                    idx = 0
                    while not self.stop_video_flag.is_set():
                        frame = frames[idx % len(frames)]
                        frame.thumbnail(self.target_thumb_size)
                        photo_image = ImageTk.PhotoImage(frame)
                        widget.config(image=photo_image)
                        widget.image = photo_image
                        time.sleep(durations[idx % len(durations)] / 800.0)
                        idx += 1

                except Exception as e:
                    print(f"播放 GIF 时出错: {e}")

            else:
                # 普通视频处理
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    print(f"❌ 无法打开视频：{video_path}")
                    return
                fps = cap.get(cv2.CAP_PROP_FPS)
                wait_time = max(1, int(800 / (fps if fps > 0 else 25)))

                while not self.stop_video_flag.is_set():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img.thumbnail(self.target_thumb_size)
                    photo_image = ImageTk.PhotoImage(img)
                    widget.config(image=photo_image)
                    widget.image = photo_image
                    time.sleep(wait_time / 800.0)

                cap.release()

            # 播放结束，恢复静态图
            widget.config(image=original_image)
            widget.image = original_image
            self.stop_video_flag.set()

    def open_photo_viewer(self, photo_path):
        PhotoViewer(self.master, photo_path, self.all_categories, self.photos.get(photo_path, []), self.update_photo_classification)

    def update_photo_classification(self, photo_path, new_categories):
        self.photos[photo_path] = new_categories
        with open(self.classifications_file, 'w', encoding='utf-8') as file:
            json.dump(self.photos, file, ensure_ascii=False, indent=4)
        messagebox.showinfo("更新成功", "图片分类已更新")
        self.category_selected(None)  # Refresh the current view

    def show_next_page(self):
        if (self.current_page + 1) * self.photos_per_page < len(self.current_category_photos):
            self.current_page += 1
            self.display_photos()
            
    def show_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_photos()

def main():
    root = tk.Tk()
    root.title("分类相册")
    app = ClassifiedPhotoAlbum(root, "jsondata/classifications.json")
    root.mainloop()

if __name__ == "__main__":
    main()
