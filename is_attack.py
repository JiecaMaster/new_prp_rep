# 输入要删除的行数范围
n = int(input("请输入要删除的前n行："))
m = int(input("请输入要删除的后m行："))

with open('logs/http_sql.txt', 'r') as f:
    lines = f.readlines()

# 执行首尾行删除
processed = lines[n:-m] if m != 0 else lines[n:]

# 解析字段索引
header = processed[0].strip().split()[1:]
try:
    src_ip_idx = header.index('id.orig_h')
    dst_ip_idx = header.index('id.resp_h')
    # 需要保留的目标字段
    target_indices = [
        header.index('ts'),
        header.index('id.orig_h'),
        header.index('id.resp_h'),
        header.index('uri'),
        header.index('referrer'),
        header.index('user_agent')
    ]
except ValueError as e:
    print(f"关键字段缺失: {e}")
    exit()

output = []
for idx, line in enumerate(processed[2:]):  # 跳过前两行说明
    parts = line.strip().split()

    # 有效性检查
    if len(parts) < len(header):
        continue

    # IP地址筛选（严格匹配）
    if (parts[src_ip_idx] == '172.16.0.1'
            and parts[dst_ip_idx] == '192.168.10.50'):

        # 提取目标字段值
        try:
            values = [parts[i] for i in target_indices]
        except IndexError:
            continue

        # 构建记录格式
        formatted = [
            f"${name}:{val}$"
            for name, val in zip(
                ['ts', 'id.orig_p', 'id.resp_p', 'uri', 'referrer', 'user_agent'],
                values
            )
        ]
        output.append(f"记录{idx + 1}:" + ",".join(formatted) + ";\n")

# 结果输出
with open('filtered_http_sql.txt', 'w') as f:
    f.writelines(output)

print(f"处理完成，有效记录数：{len(output)}")
print(f"输出文件：filtered_http_sql.txt")
