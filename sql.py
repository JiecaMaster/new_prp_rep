import datetime

n = 0
m = 0

# 新增时间范围筛选
while True:
    time_filter = input("是否要筛选时间戳范围？(y/n): ").lower()
    if time_filter in ['y', 'n']:
        break
if time_filter == 'y':
    start = float(input("请输入起始时间戳（秒）: "))
    end = float(input("请输入结束时间戳（秒）: "))

with open('logs/http.txt', 'r') as f:
    lines = f.readlines()

processed = lines[n:-m] if m != 0 else lines[n:]

# 解析字段名称
header_fields = processed[0].strip().split()[1:]
target_fields = ['ts', 'id.orig_h', 'id.resp_h', 'uri', 'referrer', 'user_agent']

try:
    indices = [header_fields.index(f) for f in target_fields]
    ts_index = header_fields.index('ts')  # 获取时间戳字段索引
except ValueError as e:
    print(f"错误：字段 {e} 不存在")
    exit()

# 初始化输出
output = []
filtered_output = []

for idx, line in enumerate(processed[2:]):
    parts = line.strip().split()

    if len(parts) < len(header_fields):
        continue

    try:
        # 提取时间戳（支持科学计数法）
        ts = float(parts[ts_index])
    except (ValueError, IndexError):
        continue

    # 时间范围筛选
    if time_filter == 'y' and not (start <= ts <= end):
        continue  # 跳过不符合时间范围的记录

    try:
        values = [parts[i] for i in indices]
    except IndexError:
        continue

    # 构建记录
    record = f"记录{idx + 1}:" + ",".join(
        [f"${k}:{v}$" for k, v in zip(target_fields, values)]
    ) + ";\n"

    output.append(record)
    # 当启用时间筛选时，只保存符合条件的数据到独立文件
    if time_filter == 'y':
        filtered_output.append(record)

# 保存主文件
with open('http_sql.txt', 'w') as f:
    f.writelines(output)

# 保存时间筛选文件（当启用时）
if time_filter == 'y':
    # filename = f"http_sql_{datetime.datetime.fromtimestamp(start):%Y%m%d_%H%M}-" \
    #            f"{datetime.datetime.fromtimestamp(end):%Y%m%d_%H%M}.txt"
    filename = "http_sql.txt"
    with open(filename, 'w') as f:
        f.writelines(filtered_output)
    print(f"已生成时间筛选文件：{filename}")

