import os
import random
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import time
class SlideshowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("幻灯片放映器")
        self.root.configure(background='black')

        self.folder_path = self.get_folder_path()
        self.image_files = self.get_image_files(self.folder_path)
        random.shuffle(self.image_files)
        self.current_index = 0
        self.slide_interval = 3  # 切换间隔时间（秒）
        self.target_width = root.winfo_screenwidth()
        self.target_height = root.winfo_screenheight()
        self.scale_factor = 1.0
        self.prepared_pic = []
        self.next_id = None
        root.state('zoomed')

        self.image_label = tk.Label(self.root)
        self.image_label.pack(expand=True, fill="both")

        self.root.bind("<Up>", self.increase_interval)
        self.root.bind("<Down>", self.decrease_interval)
        self.root.bind("<Right>", lambda event: self.display_next_image())
        self.root.bind("<Left>", lambda event: self.display_prev_image())
        self.root.bind("<MouseWheel>", self.on_mouse_wheel)
        self.root.bind("<BackSpace>", self.delete_current_image)
        self.root.bind("<Return>", self.delete_current_image)

        self.display_next_image()

    def on_mouse_wheel(self, event):
        if event.delta > 0:  # 滚轮向上滚动
            self.increase_scale(event)
        elif event.delta < 0:  # 滚轮向下滚动
            self.decrease_scale(event)

    def get_folder_path(self):
        folder_path = filedialog.askdirectory(initialdir = '.',title="选择图片文件夹")
        return folder_path

    def get_image_files(self, folder_path):
        image_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_files.append(os.path.join(root, file))
        return image_files

    def prepare_image(self, image_path):
        try:
            image = Image.open(image_path)
            image.thumbnail((self.target_width * self.scale_factor, self.target_height * self.scale_factor))

            draw = ImageDraw.Draw(image)
            text = f"{self.slide_interval:.1f}s"
            font = ImageFont.truetype("arial.ttf", 60)
            text_position = (10, 10)
            text_color = (0, 0, 0)  # 白色文字

            # 计算文字背景的大小
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            background_position = (text_position[0], text_position[1], text_position[0] + text_width, text_position[1] + text_height)

            # 绘制文字背景
            background_color = (150, 150, 150)
            draw.rectangle(background_position, fill=background_color)

            # 在背景上绘制文字
            draw.text(text_position, text, fill=text_color, font=font)

            self.prepared_pic = ImageTk.PhotoImage(image)
        except:
            self.prepared_pic = []

    def display_image(self, image_path):
        if self.next_id:
            self.root.after_cancel(self.next_id)
        if self.prepared_pic:
            self.image_label.configure(image=self.prepared_pic)
            self.image_label.image = self.prepared_pic
            print("准备成功")
            return True
        try:
            print("准备失败")
            image = Image.open(image_path)
            image.thumbnail((self.target_width * self.scale_factor, self.target_height * self.scale_factor))

            draw = ImageDraw.Draw(image)
            text = f"{self.slide_interval:.1f}s"
            font = ImageFont.truetype("arial.ttf", 60)
            text_position = (10, 10)
            text_color = (0, 0, 0)  # 白色文字

            # 计算文字背景的大小
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            background_position = (text_position[0], text_position[1], text_position[0] + text_width, text_position[1] + text_height)

            # 绘制文字背景
            background_color = (150, 150, 150)
            draw.rectangle(background_position, fill=background_color)

            # 在背景上绘制文字
            draw.text(text_position, text, fill=text_color, font=font)

            image = ImageTk.PhotoImage(image)
            self.image_label.configure(image=image)
            self.image_label.image = image

        except Exception as e:
            print(f"Error displaying image: {e}")
            return False
        return True

    def display_prev_image(self):
        self.root.focus_force()
        self.root.focus_set()
        self.prepared_pic = []
        while self.current_index < len(self.image_files):
            self.current_index -= 1
            image_path = self.image_files[self.current_index]
            if self.display_image(image_path):
                self.next_id = self.root.after(int(self.slide_interval * 1000), self.display_next_image)
                self.prepare_image(self.image_files[self.current_index+1])
                break
        else:
            self.current_index = 0

    def display_next_image(self):
        self.root.focus_force()
        self.root.focus_set()
        while self.current_index < len(self.image_files):
            self.current_index += 1
            image_path = self.image_files[self.current_index]
            if self.display_image(image_path):
                self.next_id = self.root.after(int(self.slide_interval * 1000), self.display_next_image)
                self.prepare_image(self.image_files[self.current_index+1])
                break
        else:
            self.current_index = 0

    def reload_pic(self):
        self.root.after_cancel(self.next_id)
        self.prepared_pic = []
        self.display_image(self.image_files[self.current_index])
        self.next_id = self.root.after(int(self.slide_interval * 1000), self.display_next_image)

    def increase_interval(self, event):
        self.slide_interval += 0.2
        self.reload_pic()

    def decrease_interval(self, event):
        if self.slide_interval > 0.3:
            self.slide_interval -= 0.2
            self.reload_pic()

    def increase_scale(self, event):
        self.scale_factor += 0.1
        self.reload_pic()

    def decrease_scale(self, event):
        if self.scale_factor > 0.1:
            self.scale_factor -= 0.1
            self.reload_pic()

    def delete_current_image(self, event):
        if self.current_index > 0:
            self.root.after_cancel(self.next_id)
            current_image_path = self.image_files[self.current_index]
            print(current_image_path)
            os.remove(current_image_path)
            img = Image.new('RGB', (1000,300), color='gray')
            draw = ImageDraw.Draw(img)
            text = f"Deleted"
            font = ImageFont.truetype("arial.ttf", 300)
            text_position = (0, 0)
            text_color = (255, 0, 0) 
            draw.text(text=text,font=font,fill=text_color,xy=text_position)
            image = ImageTk.PhotoImage(img)
            self.image_label.configure(image=image)
            self.image_label.image = image
            self.prepare_image(self.image_files[self.current_index+1])
            # time.sleep(0.1)
            # self.display_next_image()
            self.next_id = self.root.after(100, self.display_next_image)



if __name__ == "__main__":
    root = tk.Tk()
    app = SlideshowApp(root)
    root.mainloop()
