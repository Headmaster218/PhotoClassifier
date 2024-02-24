from pathlib import Path
from tkinter import filedialog, messagebox
import cv2
import os
import numpy as np
from tkinter import *
from PIL import Image, ImageTk
import json

class PhotoClassifier:
    def __init__(self, master):
        self.master = master
        image_path = self.load_path()  # 加载路径
        self.image_paths = find_images(image_path)
        self.labels_file = 'labels.json'
        self.labels = self.load_labels()
        self.classifications = self.load_classifications()
        self.label_buttons = []
        self.progress_file = 'progress.json'
        self.key_bindings = "`1234567890-=\\qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOPASDFGHJKLZXCVBNM"  # 按键绑定到分类标签

        self.master.title("照片分类器")

        self.path_entry = Entry(master)
        self.path_entry.pack()
        self.path_entry.insert(0, self.load_path())  # 显示当前路径

        self.change_path_button = Button(master, text="修改路径", command=self.change_path)
        self.change_path_button.pack()

        self.image_label = Label(master)
        self.image_label.pack()

        self.buttons_frame = Frame(master)
        self.buttons_frame.pack()

        self.init_label_buttons()

        self.new_label_entry = Entry(master)
        self.new_label_entry.pack()

        self.add_label_button = Button(master, text="添加新分类", command=self.add_new_label)
        self.add_label_button.pack()

        self.next_button = Button(master, text="下一张 (Enter)", command=self.next_image)
        self.next_button.pack()

        self.progress_label = Label(master, text="进度：0/0")
        self.progress_label.pack()

        self.prev_button = Button(master, text="上一张", command=self.show_prev_image)
        self.prev_button.pack(side=LEFT)


        self.save_and_exit_button = Button(master, text="保存并退出", command=self.save_and_exit)
        self.save_and_exit_button.pack()

        self.master.bind('<space>', self.copy_last_classification)
        self.master.bind('<Return>', lambda event: self.next_image())
        self.master.bind('<BackSpace>', self.show_prev_image)


        self.load_progress()
        self.show_image()

    def save_path(self, new_path):
        data = {'image_path': new_path}
        Path('path.json').write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')


    def load_path(self):
        path_file = Path('path.json')
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
            self.image_paths = find_images(new_path)  # 更新图片路径列表
            self.show_image()  # 显示新路径下的第一张图片

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
        if self.current_image_index > 1:  # Ensure there is a last image
            last_image_path = self.image_paths[self.current_image_index - 1]
            last_classification = self.classifications.get(last_image_path, [])
            for label, btn_var in self.label_buttons:
                btn_var.set(label in last_classification)

    def save_and_exit(self):
        self.save_classifications()
        self.save_progress()
        self.master.quit()

    def next_image(self):
        # 保存当前图片的分类
        if self.current_image_index < len(self.image_paths):
            current_image_path = self.image_paths[self.current_image_index]
            selected_labels = [label for label, btn_var in self.label_buttons if btn_var.get()]

            # 仅当有选中的标签时，才保存当前图片的分类
            if selected_labels:  # 检查selected_labels非空
                self.classifications[current_image_path] = selected_labels
            else:
                # 如果没有选中的标签，则确保不保存当前图片路径
                self.classifications.pop(current_image_path, None)

            # 每10张图片保存一次分类结果和进度，或者在最后一张图片时保存
            if self.current_image_index % 10 == 0 or self.current_image_index == len(self.image_paths) - 1:
                self.save_classifications()
                self.save_progress()

        # 尝试找到下一张未分类或空分类的图片
        while self.current_image_index < len(self.image_paths):
            self.current_image_index += 1  # 移动到下一张图片
            if self.current_image_index >= len(self.image_paths):
                print("没有更多图片了")
                self.save_classifications()  # Save at the end
                self.save_progress(final=True)
                break

            next_image_path = self.image_paths[self.current_image_index]
            # 检查下一张图片是否未分类或空分类
            if next_image_path not in self.classifications or not self.classifications[next_image_path]:
                for _, btn_var in self.label_buttons:
                    btn_var.set(False)  # Reset the button state for the next image
                self.show_image()
                break


    def update_progress_display(self):
        progress_text = f"进度：{self.current_image_index + 1}/{len(self.image_paths)}"
        self.progress_label.config(text=progress_text)


    def show_image(self):
        # 在显示新图片之前重置所有标签按钮的选中状态
        for _, btn_var in self.label_buttons:
            btn_var.set(False)
        if self.current_image_index < len(self.image_paths):
            image_path = self.image_paths[self.current_image_index]
            self.display_image(image_path)
        else:
            print("没有更多图片了")
        self.update_progress_display()

    def show_prev_image(self, event = None):
        if self.current_image_index > 1:  # 确保有上一张图片可以显示
            self.current_image_index -= 1
            self.show_image()
            self.update_label_buttons()  # 更新标签按钮的选中状态


    def display_image(self, image_path):
        # 尝试使用pathlib处理路径，以提高兼容性
        image_path = Path(image_path)
        
        # 读取图片文件的二进制数据
        try:
            img_data = image_path.read_bytes()  # 读取图片数据
            img_array = np.frombuffer(img_data, np.uint8)  # 将数据转换为numpy数组
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)  # 用OpenCV解码图片数据
            if img is None:
                raise IOError("无法加载图片")
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败：{e}")
            return
        
        # 接下来是图片处理和显示的代码
        img = cv2.resize(img, (960, 720))
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
        if self.current_image_index < len(self.image_paths):
            current_image_path = self.image_paths[self.current_image_index]
            selected_labels = self.classifications.get(current_image_path, [])
            for label, btn_var in self.label_buttons:
                btn_var.set(label in selected_labels)

    def toggle_label(self, label, btn_var):
        print(f"分类 {label} 被 {'选定' if btn_var.get() else '取消选定'}。")

    def save_classifications(self):
        with open('classifications.json', 'w', encoding='utf-8') as json_file:
            json.dump(self.classifications, json_file, ensure_ascii=False, indent=4)
        print("分类结果已保存到 classifications.json")

    def load_classifications(self):
        try:
            with open('classifications.json', 'r', encoding='utf-8') as json_file:  # 指定文件编码为utf-8
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
        progress = {'current_image_index': 0 if final else self.current_image_index}
        with open(self.progress_file, 'w') as json_file:
            json.dump(progress, json_file)

    def load_progress(self):
        try:
            with open(self.progress_file, 'r') as json_file:
                progress = json.load(json_file)
                self.current_image_index = progress.get('current_image_index', 0)
        except FileNotFoundError:
            self.current_image_index = 0

def find_images(directory):
    supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".jp2"]
    image_paths = [os.path.join(dp, f) for dp, dn, filenames in os.walk(directory) for f in filenames if os.path.splitext(f)[1].lower() in supported_formats]
    return image_paths

def main():
    root = Tk()
    app = PhotoClassifier(root)  # 不再需要在这里传递image_paths
    root.mainloop()

if __name__ == "__main__":
    main()
