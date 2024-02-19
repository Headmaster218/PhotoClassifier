import cv2
import os
import numpy as np
from tkinter import *
from PIL import Image, ImageTk
import json

class PhotoClassifier:
    def __init__(self, master, image_paths):
        self.master = master
        self.image_paths = image_paths
        self.labels_file = 'labels.json'
        self.labels = self.load_labels()
        self.classifications = self.load_classifications()
        self.label_buttons = []
        self.progress_file = 'progress.json'
        self.key_bindings = "`1234567890-=\\qwertyuiop[]"  # 按键绑定到分类标签

        self.master.title("照片分类器")

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

        self.prev_button = Button(master, text="上一张", command=self.show_prev_image)
        self.prev_button.pack(side=LEFT)


        self.save_and_exit_button = Button(master, text="保存并退出", command=self.save_and_exit)
        self.save_and_exit_button.pack()

        self.master.bind('<c>', self.copy_last_classification)
        self.master.bind('<Return>', lambda event: self.next_image())

        self.load_progress()
        self.show_image()

    def init_label_buttons(self):
        first_row_keys = "`1234567890-=\\"
        second_row_keys = "qwertyuiop[]"
        # 对于每个标签，计算其应该放在哪一行哪一列
        for i, label in enumerate(self.labels):
            display_text = f"{self.key_bindings[i]}: {label}" if i < len(self.key_bindings) else label
            # 使用默认参数锁定每次循环中lambda表达式的变量值
            self.master.bind(self.key_bindings[i], lambda event, l=label: self.toggle_label_via_key(l) if i < len(self.key_bindings) else None)
            row = 0 if i < len(first_row_keys) else 1
            column = i if row == 0 else i - len(first_row_keys)
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
        if self.current_image_index < len(self.image_paths):
            current_image_path = self.image_paths[self.current_image_index]
            selected_labels = [label for label, btn_var in self.label_buttons if btn_var.get()]
            self.classifications[current_image_path] = selected_labels
            self.current_image_index += 1  # 确保这里正确地增加了索引
            for _, btn_var in self.label_buttons:
                btn_var.set(False)  # Reset the button state for the next image

            if self.current_image_index % 10 == 0 or self.current_image_index == len(self.image_paths):
                self.save_classifications()
                self.save_progress()

            if self.current_image_index < len(self.image_paths):
                self.show_image()
            else:
                print("没有更多图片了")
                self.save_classifications()  # Save at the end
                self.save_progress(final=True)

    def show_image(self):
        # 在显示新图片之前重置所有标签按钮的选中状态
        for _, btn_var in self.label_buttons:
            btn_var.set(False)
        if self.current_image_index < len(self.image_paths):
            image_path = self.image_paths[self.current_image_index]
            self.display_image(image_path)
        else:
            print("没有更多图片了")

    def show_prev_image(self):
        if self.current_image_index > 1:  # 确保有上一张图片可以显示
            self.current_image_index -= 1
            self.show_image()
            self.update_label_buttons()  # 更新标签按钮的选中状态


    def display_image(self, image_path):
        img = cv2.imread(image_path)
        img = cv2.resize(img, (640, 480))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        self.image_label.imgtk = imgtk
        self.image_label.configure(image=imgtk)

    def add_new_label(self):
        new_label = self.new_label_entry.get().strip()
        if new_label and new_label not in self.labels:
            self.labels.append(new_label)
            self.save_labels()
            
            # 计算新标签的索引
            label_index = len(self.labels) - 1
            first_row_keys = "`1234567890-=\\"
            second_row_keys = "qwertyuiop[]"
            
            # 确定新标签应该放在哪一行哪一列
            if label_index < len(first_row_keys):
                row = 0
                column = label_index  # 第一行直接使用索引作为列号
            elif label_index < len(first_row_keys) + len(second_row_keys):
                row = 1
                column = label_index - len(first_row_keys)  # 第二行需要减去第一行的长度
            else:
                # 如果有更多行，继续按照这种方式计算行和列
                row = 2  # 这里只是示例，具体行号需要根据实际情况计算
                column = label_index - (len(first_row_keys) + len(second_row_keys))
            
            # 生成显示文本
            display_text = f"{self.key_bindings[label_index]}: {new_label}" if label_index < len(self.key_bindings) else new_label
            self.add_label_button_gui(new_label, display_text, row, column)
            self.new_label_entry.delete(0, END)
            self.master.focus_set()

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
    supported_formats = [".jpg", ".jpeg", ".png", ".bmp"]
    image_paths = [os.path.join(dp, f) for dp, dn, filenames in os.walk(directory) for f in filenames if os.path.splitext(f)[1].lower() in supported_formats]
    return image_paths

def main():
    root = Tk()
    image_paths = find_images("Z:/Backup/DCIM")
    app = PhotoClassifier(root, image_paths)
    root.mainloop()

if __name__ == "__main__":
    main()
