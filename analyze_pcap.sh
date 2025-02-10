#!/bin/bash

# 设置 pcap 文件夹和 logs 文件夹路径
pcap_dir="./pcap"
log_dir="./logs"

# 检查 pcap 文件夹是否存在
if [ ! -d "$pcap_dir" ]; then
    echo "pcap 文件夹不存在"
    exit 1
fi

# 获取 pcap 文件夹中的 .pcap 文件数量
pcap_files=$(ls $pcap_dir/*.pcap 2>/dev/null)

# 计算 pcap 文件数量
pcap_count=$(echo "$pcap_files" | wc -l)

# 根据 pcap 文件数量执行不同操作
if [ "$pcap_count" -eq 1 ]; then
    # 确保 logs 文件夹存在
    if [ ! -d "$log_dir" ]; then
        mkdir "$log_dir"
    fi

    # 获取 pcap 文件名
    pcap_file=$(echo "$pcap_files" | head -n 1)

    # 执行 Zeek 命令
    echo "正在处理 pcap 文件: $pcap_file"
    zeek -Cr "$pcap_file" -o "$log_dir"

    echo "Zeek 处理完成，日志已保存到 $log_dir"
else
    echo "请检查 pcap 文件数量，当前数量为 $pcap_count"
    exit 1
fi
