# 照片管理与格式转换工具

本项目提供了一个综合的解决方案，以打标签的方式实现图片的分类、管理、查看、导出。包含格式转换功能，针对Apple的HEIC格式。而且支持***Live图像***！！！它结合了图形用户界面(GUI)的便利性和命令行工具的强大功能，旨在为用户提供一个简单高效的方式来处理和组织大量图片。

## 主要功能

- **图片分类与管理**：
  - 浏览指定目录下的所有图片。
  - 动态管理图片分类标签。
  - 快捷键操作以提高分类效率。
  - 图片路径选择与进度保存。
- **图片查看与编辑**：
  - 可放大查看单张图片并支持缩放和平移。
  - 查看和编辑图片分类，实时更新。
  - 支持Apple的Live，并在图片上特殊标注以提示此图片为Live。
- **高级图片浏览**：
  - 基于分类的高级图片浏览界面。
  - 分页显示、分类过滤和导出功能。
- **HEIC格式转换**：
  - 批量将Apple的HEIC图片格式转换为JPG格式。
  - 自动删除原HEIC文件以节省空间。

## 特色功能

- **实时视频预览**：对于带有“Live”标签的图片，支持预览Live。
- **动态分类过滤**：支持根据不同条件（并集、交集、补集）过滤显示的图片。
- **导出功能**：允许用户将符合特定分类的图片导出到一个自定义目录中。
- **支持中文路径**：解决了OpenCV等不支持中文路径的问题。

## 依赖

- **Tkinter**：用于创建和管理GUI组件。
- **Pillow (PIL)**：用于图片的加载、显示和处理。
- **OpenCV (cv2)**：用于图像处理。
- **ImageMagick**：用于HEIC到JPG的格式转换。
- **NumPy**：处理图像数据。

## 安装与使用

1. 安装Python 3.x及所需的库：
   ```bash
   pip install numpy opencv-python pillow
   ```
2. 安装ImageMagick，并确保`magick`命令在系统PATH中可用。
3. 克隆仓库或下载源代码。
4. 运行`convert_heic_to_jpg.py`以批量转换HEIC格式图片到JPG。（针对IPhone）
5. 运行`sorter.py`以启动图片分类应用。
6. 运行`album.py`以启动图片分类浏览器应用。


## 使用说明

- 首次运行时，通过图形界面选择图片存储目录。
- 使用界面按钮或快捷键进行图片分类和浏览。
- 若要转换图片格式，选择包含HEIC图片的文件夹，程序将自动处理所有子目录中的图片。

## 贡献

欢迎通过GitHub提交pull requests来贡献代码或功能改进建议。

## 许可证

本项目采用MIT许可证，详情请参见LICENSE文件。