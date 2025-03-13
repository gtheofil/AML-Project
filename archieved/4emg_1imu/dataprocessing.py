import pandas as pd
import numpy as np
import os

# 读取数据
file_path = '1_filtered(in).csv'  # 替换为你的文件路径
raw_data = pd.read_csv(file_path)

# 设定采样率和片段长度
fs = 1000  # 采样率 Hz
skip_seconds = 4  # 需要跳过的秒数
segment_length_sec = 6  # 每个手势 6 秒
skip_samples = fs * skip_seconds  # 4 秒的采样点数
segment_size = fs * segment_length_sec  # 6 秒的采样点数

# 跳过前 4 秒的数据
filtered_data = raw_data.iloc[skip_samples:].reset_index(drop=True)

# 创建保存文件夹
output_folder = 'segmented_data'
os.makedirs(output_folder, exist_ok=True)

# 遍历数据，按 6 秒片段切割
num_segments = len(filtered_data) // segment_size  # 计算完整片段的数量
segments = []  # 存储所有分割后的数据

for i in range(num_segments):
    start_idx = i * segment_size
    end_idx = start_idx + segment_size
    segment = filtered_data.iloc[start_idx:end_idx]  # 取 6 秒片段

    # 保存到列表
    segments.append(segment.values)

    # 可选：存储到 CSV
    segment.to_csv(f"{output_folder}/segment_{i+1}.csv", index=False)

    print(f"Segment {i+1} saved: Rows {start_idx} to {end_idx}")

# 转换为 NumPy 数组
segments_array = np.array(segments)  # 形状: (num_segments, 12000, 数据列数)

# 保存 NumPy 文件
np.save(f"{output_folder}/segments.npy", segments_array)

print(f"Total segments saved: {num_segments}")
