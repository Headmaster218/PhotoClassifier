import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import json 
import os
import shutil  # 用于文件复制

class PhotoViewer(tk.Toplevel):
    def __init__(self, master, photo_path, all_categories, photo_categories, update_callback):
        super().__init__(master)
        self.photo_path = photo_path
        self.all_categories = all_categories
        self.photo_categories = photo_categories
        self.update_callback = update_callback

        self.title(os.path.basename(photo_path))
        self.geometry("800x650")

        # 使用OpenCV加载和转换图像
        self.cv_img = cv2.imread(photo_path)
        self.cv_img = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
        self.img_height, self.img_width = self.cv_img.shape[:2]

        # 初始化图像缩放比例和位置
        self.scale = 1.0
        self.calculate_initial_scale()
        self.image_position_x = (800 - self.img_width * self.scale) / 2
        self.image_position_y = (600 - self.img_height * self.scale) / 2

        self.canvas = tk.Canvas(self, width=800, height=600, bg='black')
        self.canvas.pack()

        # 绑定滚轮事件用于缩放
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        # 绑定鼠标事件用于平移
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan_image)

        self.display_image()

        categories_str = ", ".join(self.photo_categories)
        self.info_label = tk.Label(self, text=f"当前分类: {categories_str}")
        self.info_label.pack()

        self.change_category_button = tk.Button(self, text="修改分类", command=self.change_category)
        self.change_category_button.pack()

    def calculate_initial_scale(self):
        # 根据窗口大小计算初始缩放比例
        scale_x = 800 / self.img_width
        scale_y = 600 / self.img_height
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
            new_categories = [c.strip() for c in new_category.split(',')]
            if set(new_categories) != set(self.photo_categories):
                self.photo_categories = new_categories
                self.update_callback(self.photo_path, new_categories)
                self.info_label.config(text=f"当前分类: {', '.join(new_categories)}")


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

        self.master.state('zoomed')

        # 筛选条件UI设置
        filter_frame = tk.Frame(master)
        filter_frame.pack(fill=tk.X)

        tk.Label(filter_frame, text="分类1:").pack(side=tk.LEFT, padx=5)
        self.category_combobox1 = ttk.Combobox(filter_frame, state="readonly", postcommand=self.update_comboboxes)
        tk.Label(filter_frame, text="条件:").pack(side=tk.LEFT, padx=5)
        self.filter_type_combobox = ttk.Combobox(filter_frame, state="readonly", values=["且", "或", "除了", "无"])
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

        self.page_info_label = tk.Label(navigation_frame, text="页码: 1/1")
        self.page_info_label.pack(side=tk.LEFT, padx=5)

        self.goto_page_entry = ttk.Entry(navigation_frame, width=5)
        self.goto_page_entry.pack(side=tk.LEFT, padx=5)

        self.goto_page_button = tk.Button(navigation_frame, text="跳转", command=self.goto_page)
        self.goto_page_button.pack(side=tk.LEFT, padx=5)

        self.photos_frame = tk.Frame(master)
        self.photos_frame.pack(expand=True, fill=tk.BOTH)

        # 更新所有下拉框的选项
        self.update_comboboxes()


    def update_display(self, event=None):
        selected_category1 = self.category_combobox1.get()
        selected_category2 = self.category_combobox2.get()
        filter_type = self.filter_type_combobox.get()

        if selected_category1 == "无":
            self.current_category_photos = list(self.photos.keys())
        elif filter_type == "且":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if selected_category1 in labels and selected_category2 in labels]
        elif filter_type == "或":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if selected_category1 in labels or selected_category2 in labels and selected_category2 != "无"]
        elif filter_type == "除了":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if selected_category1 in labels and selected_category2 not in labels]

        self.current_page = 0
        self.update_pagination_info()
        self.display_photos()

    def update_comboboxes(self):
        all_categories = ["无"] + self.get_all_categories()
        self.category_combobox1['values'] = all_categories
        self.category_combobox2['values'] = all_categories
        self.category_combobox1.bind("<<ComboboxSelected>>", self.category_selected)
        self.category_combobox2.bind("<<ComboboxSelected>>", self.category_selected)

    def filter_type_selected(self, event=None):
        if self.filter_type_combobox.get() == "无":
            self.category_combobox2.set("无")
            self.category_combobox2['state'] = 'disabled'
        else:
            self.category_combobox2['state'] = 'readonly'


    def export_results(self):
        export_folder = filedialog.askdirectory()
        if export_folder:
            for photo_path in self.current_category_photos:
                shutil.copy(photo_path, os.path.join(export_folder, os.path.basename(photo_path)))
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
        categories = set()
        for labels in self.photos.values():
            categories.update(labels)
        return list(categories)

    # 确保当"无"被选中时，第二个下拉框被禁用
    def filter_type_selected(self, event=None):
        super().filter_type_selected(event)
        if self.filter_type_combobox.get() == "无":
            self.category_combobox2.set("无")
            self.category_combobox2['state'] = 'disabled'
        else:
            self.category_combobox2['state'] = 'readonly'

    def category_selected(self, event=None):
        filter_type = self.filter_type_combobox.get()
        category1 = self.category_combobox1.get()
        category2 = self.category_combobox2.get()

        if filter_type == "无":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels or category1 == "无"]
        elif filter_type == "且":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels and category2 in labels]
        elif filter_type == "或":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels or category2 in labels]
        elif filter_type == "除了":
            self.current_category_photos = [photo for photo, labels in self.photos.items() if category1 in labels and category2 not in labels]

        self.current_page = 0
        self.update_pagination_info()
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
