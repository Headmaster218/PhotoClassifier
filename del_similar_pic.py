import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import ImageFont, ImageDraw, Image, ImageTk
import json
import os
import numpy as np

def read_image(path):
    try:
        with open(path, 'rb') as file:
            img_data = np.frombuffer(file.read(), dtype=np.uint8)
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        if img is None:  # 检查是否成功解码图像
            raise IOError("Cannot load image")
        return img
    except Exception as e:
        # 创建一个包含错误消息的图像
        error_message = "Fail"
        # 创建一个空白图像，您可以根据需要调整图像的大小
        img = np.zeros((200, 300, 3), dtype=np.uint8)
        img.fill(200)  # 使背景为白色
        # 将OpenCV图像转换为PIL图像，以便使用PIL添加文本
        pil_img = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_img)
        font = ImageFont.truetype("arial.ttf", 80)
        # 获取文本大小
        text_size = draw.textsize(error_message, font=font)
        # 计算文本位置
        text_x = (pil_img.width - text_size[0]) / 2
        text_y = (pil_img.height - text_size[1]) / 2
        # 将文本绘制到图像上
        draw.text((text_x, text_y), error_message, fill=(0, 0, 0), font=font)
        # 将PIL图像转换回OpenCV图像
        return np.array(pil_img)

def resize_image(img, target_width=300, target_height=300, keep_ratio=True):
    if keep_ratio:
        h, w = img.shape[:2]
        scale = min(target_width/w, target_height/h)
        new_size = (int(w * scale), int(h * scale))
    else:
        new_size = (target_width, target_height)
    resized_img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
    return resized_img

def open_image_in_window(root, img_paths, current_index):
    def update_image(index):
        # 确保index在有效范围内
        index = max(0, min(index, len(img_paths) - 1))
        new_img_path = img_paths[index]
        img = read_image(new_img_path)  # 重新使用read_image函数读取图片
        img_resized = resize_image(img, target_width=screen_width, target_height=screen_height, keep_ratio=True)
        img_resized = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_resized)

        # 在这里叠加图片序号
        draw = ImageDraw.Draw(img_pil)
        text = f"{index + 1}/{len(img_paths)}"
        font = ImageFont.truetype("arial.ttf", 60)
        text_position = (10, 10)
        text_color = (255, 255, 255)  # 白色文字

        # 计算文字背景的大小
        text_width, text_height = draw.textsize(text, font=font)
        background_position = (text_position[0], text_position[1], text_position[0] + text_width, text_position[1] + text_height)

        # 绘制文字背景
        background_color = (0, 0, 0)  # 黑色背景
        draw.rectangle(background_position, fill=background_color)

        # 在背景上绘制文字
        draw.text(text_position, text, fill=text_color, font=font)

        img_tk = ImageTk.PhotoImage(image=img_pil)
        img_label.configure(image=img_tk)
        img_label.image = img_tk  # 防止垃圾回收

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    new_window = tk.Toplevel(root)
    new_window.title("查看大图，按左右键可切换图片")
    img_label = ttk.Label(new_window)
    img_label.pack()

    def on_key_press(event):
        nonlocal current_index, img_paths
        if event.keysym == 'Right' and current_index < len(img_paths) - 1:
            current_index += 1
            update_image(current_index)
        elif event.keysym == 'Left' and current_index > 0:
            current_index -= 1
            update_image(current_index)

    # 绑定键盘事件
    new_window.bind("<Left>", on_key_press)
    new_window.bind("<Right>", on_key_press)
    # new_window.bind("<space>", on_key_press)

    new_window.focus_set()  # 窗口获得焦点
    new_window.grab_set()  # 使新窗口获得所有事件

    # 使用update_image来初始化第一张图片的显示
    update_image(current_index)

class ImageReviewer:
    def __init__(self, root):
        self.root = root
        self.root.title("相似图片查看删除器")
        self.root.geometry("800x650")
        self.file_path = None
        
        ttk.Button(self.root, text="第一步：选择相似图片组JSON文件", command=self.load_json).pack(pady=20)
        
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(pady=20)
        
        self.delete_buttons_frame = ttk.Frame(self.root)
        self.delete_buttons_frame.pack(pady=10)
        
        self.confirm_delete_button = ttk.Button(self.root, text="确认删除选中的图片", state=tk.DISABLED, command=self.confirm_delete)
        self.confirm_delete_button.pack(pady=10)
        
        # 创建一个新的框架来容纳“下一组”和“上一组”按钮
        self.navigation_frame = ttk.Frame(self.root)
        self.navigation_frame.pack(pady=10)
        
        self.previous_button = ttk.Button(self.navigation_frame, text="上一组", state=tk.DISABLED, command=self.previous_group)
        self.previous_button.pack(side="left", padx=5)
        
        self.next_button = ttk.Button(self.navigation_frame, text="下一组", state=tk.DISABLED, command=self.next_group)
        self.next_button.pack(side="left", padx=5)
        
        self.root.bind("<Return>", lambda event: self.confirm_delete())
        self.similar_images = []
        self.current_group_index = 0
        self.selected_for_deletion = []

        help_text = """
                    使用指南:
                    - 点击“第一步”按钮来加载前面找到的相似照片。
                    - 点击小图片可以查看大图。
                    - 大图下使用左右箭头键在图片组内切换对比图片。
                    - 选中图片，点击“确认删除”来删除所有选中的图片。
                    - “下一组”和“上一组”按钮可以用来在图片组间导航。
                    
                    注意：删除操作是不可逆的，请谨慎操作。
                    """
        messagebox.showinfo("使用帮助", help_text)

    def load_json(self):
        initial_directory = './jsondata/'  # 设置初始目录路径
        self.file_path = filedialog.askopenfilename(initialdir=initial_directory)
        if not self.file_path:
            return
        
        with open(self.file_path, 'r', encoding='utf-8') as file:
            self.similar_images = json.load(file)
        
        self.current_group_index = 0
        if self.similar_images:
            self.show_group(self.similar_images[self.current_group_index])
            self.next_button['state'] = tk.NORMAL
        else:
            messagebox.showinfo("信息", "没有找到相似的图片组。")

    def show_group(self, group):
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        for widget in self.delete_buttons_frame.winfo_children():
            widget.destroy()
        
        self.selected_for_deletion = []
        for img_path in group:
            self.show_image(img_path, group)
        self.confirm_delete_button['state'] = tk.NORMAL

            # 更新按钮状态
        if self.current_group_index > 0:
            self.previous_button['state'] = tk.NORMAL
        else:
            self.previous_button['state'] = tk.DISABLED

        if self.current_group_index < len(self.similar_images):
            self.next_button['state'] = tk.NORMAL
        else:
            self.next_button['state'] = tk.DISABLED

    def show_image(self, img_path, group):
        img_frame = ttk.Frame(self.image_frame)  # 为图片和删除按钮创建一个新的框架
        img_frame.pack(side="left", padx=10, pady=10)  # 将框架添加到image_frame中

        img = read_image(img_path)  # 使用新的读取方式
        img = resize_image(img)  # 按比例调整大小
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        
        panel = ttk.Label(img_frame, image=imgtk)  # 将图片标签添加到img_frame而不是直接到self.image_frame
        panel.image = imgtk
        panel.pack(side="top")  # 确保图片在框架的顶部
        
        # 计算当前图片在组内的索引
        current_index = group.index(img_path)
        
        # 修改lambda函数，传递整个图片组和当前图片的索引
        panel.bind("<Button-1>", lambda e, group=group, current_index=current_index: open_image_in_window(self.root, group, current_index))

        # 为当前图片创建删除复选框，并放置在图片下方
        chk_var = tk.BooleanVar()
        delete_chk = ttk.Checkbutton(img_frame, text="删除", variable=chk_var)  # 将删除按钮添加到img_frame
        delete_chk.pack(side="bottom")  # 确保删除按钮在框架的底部
        delete_chk.configure(command=lambda var=chk_var, path=img_path: self.mark_for_deletion(path, var))

    def mark_for_deletion(self, path, var):
        if var.get():
            self.selected_for_deletion.append(path)
        else:
            self.selected_for_deletion.remove(path)

    def confirm_delete(self):
        if not self.selected_for_deletion:
            messagebox.showinfo("信息", "没有选中的图片。")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的图片吗？"):
            # 更新内存中的数据结构
            updated_groups = []
            for group in self.similar_images:
                # 从当前组中移除选中的图片
                updated_group = [img_path for img_path in group if img_path not in self.selected_for_deletion]
                
                # 仅当组中剩余图片数量大于1时，才添加到更新后的列表中
                if len(updated_group) > 1:
                    updated_groups.append(updated_group)
                
                # 如果组中仅剩一张图片或为空，则该组不被添加到更新后的列表中，相当于从JSON中去除这组条目
                
            # 删除文件
            for path in self.selected_for_deletion:
                os.remove(path)
                print(f"Deleted: {path}")  # 实际使用时可以去除

            # 更新内部状态
            self.similar_images = updated_groups
            self.selected_for_deletion.clear()  # 清空待删除列表
            
            # 将更新后的数据写回 JSON 文件
            self.write_updated_json()

            # 移动到下一组或刷新当前视图
            if self.current_group_index < len(self.similar_images):
                self.show_group(self.similar_images[self.current_group_index])
            else:
                self.current_group_index = max(0, len(self.similar_images) - 1)  # 防止索引越界
                if self.similar_images:
                    self.show_group(self.similar_images[self.current_group_index])
                else:
                    self.reset_view()

    def write_updated_json(self):
        # 假设您的 JSON 文件路径存储在 self.json_file_path
        with open(self.file_path, 'w', encoding='utf-8') as file:
            json.dump(self.similar_images, file, ensure_ascii=False, indent=4)
        print("JSON file has been updated.")

    def reset_view(self):
        # 重置视图的实现可能会根据您的应用逻辑有所不同
        # 这里是一些基本操作的示例
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.next_button['state'] = tk.DISABLED
        self.previous_button['state'] = tk.DISABLED
        self.confirm_delete_button['state'] = tk.DISABLED
        messagebox.showinfo("信息", "所有图片组都已处理完毕或已删除。")

    def next_group(self):
        self.current_group_index += 1
        if self.current_group_index < len(self.similar_images):
            self.show_group(self.similar_images[self.current_group_index])
        else:
            messagebox.showinfo("完成", "所有组都已处理完毕。")
            self.next_button['state'] = tk.DISABLED
            self.confirm_delete_button['state'] = tk.DISABLED

    def previous_group(self):
        self.current_group_index -= 1  # 减少当前图片组的索引
        if self.current_group_index >= 0:
            self.show_group(self.similar_images[self.current_group_index])
            self.next_button['state'] = tk.NORMAL  # 重新启用“下一组”按钮
        else:
            messagebox.showinfo("信息", "已经是第一组了。")
            self.current_group_index = 0  # 确保索引不会变成负数

        # 每次切换到前一组图片时，都应该检查是否还能再往前，如果不能，则禁用“上一组”按钮
        if self.current_group_index == 0:
            self.previous_button['state'] = tk.DISABLED
        else:
            self.previous_button['state'] = tk.NORMAL

        # 确保在有可显示的图片组时，“确认删除选中的图片”按钮是启用的
        if self.similar_images:
            self.confirm_delete_button['state'] = tk.NORMAL

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageReviewer(root)
    root.mainloop()
