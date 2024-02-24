import os
import json

def report_missing_files(json_file, src_dir):
    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    missing_files = []
    # 遍历JSON中的所有文件路径
    for path in data.keys():
        # 注意：这里检查的是src_dir和path的组合路径是否存在
        full_path = os.path.join(src_dir, path)
        if not os.path.exists(full_path):
            # 如果文件不存在，添加到缺失文件列表
            missing_files.append(path)
    
    # 打印所有缺失的文件及其序号
    if missing_files:
        print("以下文件在JSON中有记录但实际不存在：")
        for index, file_path in enumerate(missing_files, start=1):
            print(f"{index}. {file_path}")
        
        # 询问用户是否删除这些条目
        user_input = input("是否从JSON文件中删除这些缺失的文件记录？(y/n): ")
        if user_input.lower() == 'y':
            # 删除缺失的文件记录
            for missing in missing_files:
                data.pop(missing, None)
            
            # 写回更新后的数据到JSON文件
            with open(json_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print("已从JSON文件中删除缺失的文件记录。")
    else:
        print("没有缺失的文件。")

# 配置文件和目录路径
json_file = 'classifications.json'
src_dir = 'R:/Backup/DCIM'

# 调用函数
report_missing_files(json_file, src_dir)
