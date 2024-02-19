import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from PIL import Image, ImageTk
import json
import os

class PhotoViewer(tk.Toplevel):
    def __init__(self, master, photo_path, all_categories, photo_categories, update_callback):
        super().__init__(master)
        self.photo_path = photo_path
        self.all_categories = all_categories
        self.photo_categories = photo_categories
        self.update_callback = update_callback

        self.title(os.path.basename(photo_path))
        self.geometry("800x650")

        self.original_img = Image.open(photo_path)
        self.scale = 1.0  # 初始化缩放比例
        self.img_width, self.img_height = self.original_img.size
        self.calculate_initial_scale()  # 计算初始缩放比例

        self.canvas = tk.Canvas(self, width=800, height=600)
        self.canvas.pack()

        # 初始化图像位置为中心
        self.image_position_x = (800 - self.img_width * self.scale) / 2
        self.image_position_y = (600 - self.img_height * self.scale) / 2

        self.display_image()

        categories_str = ", ".join(self.photo_categories)
        self.info_label = tk.Label(self, text=f"当前分类: {categories_str}")
        self.info_label.pack()

        self.change_category_button = tk.Button(self, text="修改分类", command=self.change_category)
        self.change_category_button.pack()

        # 绑定滚轮事件用于缩放
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        # 绑定鼠标事件用于平移
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan_image)

    def calculate_initial_scale(self):
        scale_x = 800 / self.img_width
        scale_y = 600 / self.img_height
        self.scale = min(scale_x, scale_y)

    def zoom_image(self, event):
        x = event.x - self.canvas.canvasx(0)
        y = event.y - self.canvas.canvasy(0)
        old_scale = self.scale
        scale_change = 1.1 if event.delta > 0 else 0.9
        self.scale *= scale_change

        # 调整图像位置，以鼠标位置为缩放中心
        self.image_position_x = x - (x - self.image_position_x) * (self.scale / old_scale)
        self.image_position_y = y - (y - self.image_position_y) * (self.scale / old_scale)

        self.display_image()

    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan_image(self, event):
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        self.image_position_x += dx
        self.image_position_y += dy

        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.display_image()

    def display_image(self):
        img_resized = self.original_img.resize(
            (int(self.img_width * self.scale), int(self.img_height * self.scale)),
            Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(img_resized)
        self.canvas.delete("all")  # 清除之前的图像
        self.canvas.create_image(self.image_position_x, self.image_position_y, anchor="nw", image=self.photo_image)

    def change_category(self):
        initial_category = ", ".join(self.photo_categories)
        new_category = simpledialog.askstring("修改分类", "输入新的分类名(多个分类用逗号分隔):", initialvalue=initial_category, parent=self)
        if new_category is not None:
            new_categories = [c.strip() for c in new_category.split(',')]
            if set(new_categories) != set(self.photo_categories):
                self.photo_categories = new_categories
                categories_str = ", ".join(new_categories)
                self.info_label.config(text=f"当前分类: {categories_str}")
                self.update_callback(self.photo_path, new_categories)

class ClassifiedPhotoAlbum:
    def __init__(self, master, classifications_file):
        self.master = master
        self.classifications_file = classifications_file
        self.photos = self.load_classifications()
        self.photo_images = []

        self.rows = 3
        self.columns = 6
        self.photos_per_page = self.rows * self.columns
        self.current_page = 0

        self.category_combobox = ttk.Combobox(master, state="readonly")
        self.photos_frame = tk.Frame(master)
        self.navigation_frame = tk.Frame(master)
        self.prev_page_button = tk.Button(self.navigation_frame, text="上一页", command=self.show_prev_page)
        self.next_page_button = tk.Button(self.navigation_frame, text="下一页", command=self.show_next_page)

        self.all_categories = self.get_all_categories()
        self.category_combobox['values'] = list(self.all_categories)
        self.category_combobox.bind("<<ComboboxSelected>>", self.category_selected)
        self.category_combobox.pack()

        self.photos_frame.pack()
        self.navigation_frame.pack()
        self.prev_page_button.pack(side=tk.LEFT)
        self.next_page_button.pack(side=tk.RIGHT)

        self.current_category_photos = []

    def load_classifications(self):
        with open(self.classifications_file, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_all_categories(self):
        categories = set()
        for labels in self.photos.values():
            categories.update(labels)
        return list(categories)

    def category_selected(self, event):
        self.current_category = self.category_combobox.get()
        self.current_category_photos = [photo for photo, labels in self.photos.items() if self.current_category in labels]
        self.current_page = 0
        self.display_photos()

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
            img = Image.open(photo_path)
            img.thumbnail((300, 300))
            photo_image = ImageTk.PhotoImage(img)
            self.photo_images.append(photo_image)
            button = tk.Button(self.photos_frame, image=photo_image, command=lambda p=photo_path: self.open_photo_viewer(p))
            button.grid(row=row, column=column, padx=5, pady=5)

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
    app = ClassifiedPhotoAlbum(root, "classifications.json")
    root.mainloop()

if __name__ == "__main__":
    main()
