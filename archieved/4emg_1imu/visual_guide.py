import os
import random
import time
import cv2
import pandas as pd
import numpy as np

# 指定图片文件夹路径
image_folder = r"alpha"
path = r"data\G"
os.makedirs(path, exist_ok=True)
excel_file = r"data\G\shuffle_order.xlsx"  # 结果存储 Excel

# 获取所有 PNG 图片文件
image_files = [f for f in os.listdir(image_folder) if f.endswith(".png")]

# 生成标签映射 (A->1, B->2, ..., Z->26)
label_dict = {chr(i + 65): i + 1 for i in range(26)}  # 65 是 'A' 的 ASCII 值

# 过滤并映射文件名
image_map = {file: label_dict[file.split(".")[0]] for file in image_files if file.split(".")[0] in label_dict}

# 打乱顺序
shuffled_images = list(image_map.keys())
random.shuffle(shuffled_images)

# 获取对应的数字顺序
shuffled_labels = [image_map[file] for file in shuffled_images]

# 读取或创建 Excel 文件
if os.path.exists(excel_file):
    df = pd.read_excel(excel_file, engine='openpyxl')  # 需要 `openpyxl`
else:
    df = pd.DataFrame()

# 使用 `pd.concat()` 代替 `df.append()`
new_row = pd.DataFrame([shuffled_labels])  # 新的一行数据
df = pd.concat([df, new_row], ignore_index=True)

# 保存到 Excel
df.to_excel(excel_file, index=False, engine='openpyxl')
i = 0

# 显示图片
for image_file in shuffled_images:
    img_path = os.path.join(image_folder, image_file)
    print(f"加载图片路径: {img_path}")  # 调试

    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is not None and img.size > 0:
        if img.shape[-1] == 4:  # 透明 PNG 处理
            bgr = img[:, :, :3]  # 获取 BGR 通道
            alpha = img[:, :, 3]  # 获取 Alpha 通道
            white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
            alpha = alpha[:, :, np.newaxis] / 255.0
            img = (bgr * alpha + white_bg * (1 - alpha)).astype(np.uint8)
        
        letter = image_file.split(".")[0]
        print(f"准备阶段: {image_file}, 标签: {image_map[image_file]}")
        start_time = time.time()
        
        # 准备阶段 5 秒
        for countdown in range(5, 0, -1):
            prep_img = img.copy()
            cv2.putText(prep_img, f"Prepare for {letter}, No.{i+1}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(prep_img, str(countdown), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
            cv2.imshow("Image", prep_img)
            elapsed = time.time() - start_time
            cv2.waitKey(max(1, int((5 - elapsed) * 1000 / (countdown))))  # 保证每秒更新一次
        
        i += 1
        start_time = time.time()
        
        # 显示阶段 5 秒
        for countdown in range(5, 0, -1):
            countdown_img = img.copy()
            cv2.putText(countdown_img, "GO", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(countdown_img, str(countdown), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
            cv2.imshow("Image", countdown_img)
            elapsed = time.time() - start_time
            cv2.waitKey(max(1, int((5 - elapsed) * 1000 / (countdown))) )# 保证每秒更新一次
        
        cv2.destroyAllWindows()
    else:
        print(f"无法打开图片: {image_file}")