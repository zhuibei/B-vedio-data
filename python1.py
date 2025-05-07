import requests
import pandas as pd
import time
import re
import os


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}
input_file = "idlist.txt"  # 输入文件名（支持链接或BV号混合）
output_file = "video_data.csv"  # 输出文件名（支持csv/xlsx）
request_delay = 1  # 请求间隔（秒）


def load_bv_ids(file_path):
    """从文件提取BV号（自动去重）"""
    print(f"[准备] 正在从文件加载视频ID: {os.path.abspath(file_path)}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 匹配所有BV号（兼容新旧格式）
            bv_ids = re.findall(r"BV[\w\d]{10,}", content)
            unique_ids = list(set(bv_ids))  # 去重
            print(f"[成功] 找到 {len(unique_ids)} 个唯一视频ID")
            return unique_ids
    except FileNotFoundError:
        print(f"[错误] 文件不存在: {file_path}")
        return []
    except Exception as e:
        print(f"[错误] 文件读取失败: {str(e)}")
        return []


def fetch_video_data(bv_id):
    """调用B站API获取视频数据"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查HTTP状态码

        data = response.json()
        if data.get("code") == 0:
            return parse_api_data(data["data"])
        else:
            print(f"[警告] 视频 {bv_id} 获取失败: {data.get('message')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[网络错误] {bv_id}: {str(e)}")
        return None
    except ValueError as e:
        print(f"[解析错误] {bv_id}: JSON解析失败")
        return None


def parse_api_data(data):
    """解析API返回的原始数据"""
    try:
        return {
            "视频ID": data["bvid"],
            "标题": data["title"],
            "UP主": data["owner"]["name"],
            "UP主ID": data["owner"]["mid"],
            "播放量": data["stat"]["view"],
            "弹幕数": data["stat"]["danmaku"],
            "点赞数": data["stat"]["like"],
            "收藏数": data["stat"]["favorite"],
            "硬币数": data["stat"]["coin"],
            "分享数": data["stat"]["share"],
            "发布时间": timestamp_to_date(data["pubdate"]),
            "最后更新": timestamp_to_date(data["ctime"]),
            "视频时长": format_duration(data["duration"]),
            "分区类别": data["tname"],
            "视频封面": data["pic"]
        }
    except KeyError as e:
        print(f"[数据错误] 字段缺失: {str(e)}")
        return None


def timestamp_to_date(timestamp):
    """时间戳转换"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def format_duration(seconds):
    """秒数转分钟:秒"""
    return f"{seconds // 60}:{seconds % 60:02d}"


def save_to_file(data, filename):
    """保存数据到文件"""
    if not data:
        print("[警告] 无有效数据可保存")
        return

    try:
        df = pd.DataFrame(data)
        # 根据扩展名选择保存格式
        if filename.endswith('.xlsx'):
            df.to_excel(filename, index=False)
        else:
            df.to_csv(filename, index=False, encoding='utf_8_sig')
        print(f"[成功] 数据已保存至: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"[错误] 文件保存失败: {str(e)}")


if __name__ == "__main__":
    # 步骤1: 加载视频ID
    bv_ids = load_bv_ids(input_file)
    if not bv_ids:
        exit()

    # 步骤2: 批量获取数据
    results = []
    total = len(bv_ids)
    for i, bv_id in enumerate(bv_ids, 1):
        print(f"[进度] 正在处理 {i}/{total}: {bv_id}")
        data = fetch_video_data(bv_id)
        if data:
            results.append(data)
        time.sleep(request_delay)  # 遵守访问频率

    # 步骤3: 保存结果
    save_to_file(results, output_file)