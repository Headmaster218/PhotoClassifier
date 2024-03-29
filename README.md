<!--
 * @Author: Headmaster1615  e-mail:hm-218@qq.com
 * @Date: 2024-02-27 13:59:30
 * @LastEditors: Headmaster1615(Server)  e-mail:hm-218@qq.com
 * @LastEditTime: 2024-03-03 21:16:10
 * @FilePath: \图片分类查看器\README.md
 * @Description: 
 * 
 * Copyright (c) 2024 by Headmaster1615, All Rights Reserved. 
-->
# 媒体管理与格式转换工具

本项目提供了一个综合的解决方案，以实现图片和视频的分类、管理、查看、导出、查重等功能。包含格式转换功能，针对Apple的HEIC格式。而且支持***Live图像***！！！它结合了图形用户界面(GUI)的便利性和命令行工具的强大功能，旨在为用户提供一个简单高效的方式来处理和组织大量图片。

## 主要功能

- **图片和视频分类与管理**：
  - 分类指定目录下的所有图片。
  - 动态分类标签。
  - 快捷键操作以提高分类效率。
  - 图片路径选择与进度保存。
  - 查找与删除相似照片。
- **图片和视频查看与编辑**：
  - 可放大查看单张图片并支持缩放和平移。
  - 查看和编辑图片和视频分类，实时更新。
  - 支持查看Apple的Live，并在图片上特殊标注以提示此图片为Live。
  - 支持视频查看，在预览图上加入Video标注。
- **高级图片和视频浏览**：
  - 基于分类的高级图片和视频浏览界面。
  - 分页显示、分类过滤和导出功能。
- **HEIC格式转换**：
  - 批量将Apple的HEIC图片格式转换为JPG格式。
  - 自动删除原HEIC文件以节省空间。
- **完善的帮助**：
  - 小程序中带有帮助提示。
- **即将加入。。。**
  - 人脸识别并提供可修改姓名的标签
  - 按时间线排序
  - 批量修改时间
  - 按地图查看
  - 批量修改位置
  - 批量修改标签
  - 旋转照片
  - 旋转Live视频
  - 多用户/多配置文件/多工作区
  - 创建缩略图以提高响应速度
  - Live照片声音播放

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
4. 运行`main.py`打开主界面
4. 或者直接下载打包好的exe文件，运行即可。


## 使用说明

- 首次运行时，通过图形界面选择图片存储目录。
- 使用界面按钮或快捷键进行图片分类和浏览。
- 若要转换图片格式，选择包含HEIC图片的文件夹，程序将自动处理所有子目录中的图片。

## 贡献

欢迎通过GitHub提交pull requests来贡献代码或功能改进建议。

## 许可证

本项目采用MIT许可证，详情请参见LICENSE文件。
