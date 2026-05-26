#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
KDocs 热门剧文档抓取脚本
- 打开金山文档链接
- 分段滚动提取虚拟化内容
- 解析为结构化JSON
- 支持定时轮询（默认30分钟）
"""

import json
import os
import re
import time
from datetime import datetime
from DrissionPage import Chromium, ChromiumOptions
from loguru import logger

# 配置
KDOCS_URL = "https://www.kdocs.cn/l/co72a28MWkmI"
OUTPUT_FILE = r"d:\Desktop\dp-mcp\vide.json"
DEBUG_PORT = 9222
POLL_INTERVAL = 30 * 60  # 30分钟

# 配置日志
logger.remove()
logger.add("kdocs_fetch.log", format="{time} {level} {message}", rotation="10 MB")
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {level:<7} | {message}")


def connect_browser():
    """连接已打开的浏览器"""
    co = ChromiumOptions()
    co.set_local_port(str(DEBUG_PORT))
    browser = Chromium(co)
    tab = browser.latest_tab
    return browser, tab


def extract_all_content(tab):
    """关闭弹窗 + 逐步滚动 + 分段提取全部内容"""
    parts = []

    # 发送ESC关闭弹窗
    try:
        tab.run_js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', code: 'Escape', keyCode: 27, which: 27})); document.dispatchEvent(new KeyboardEvent('keyup', {key: 'Escape', code: 'Escape', keyCode: 27, which: 27}));")
        logger.info("已发送ESC关闭弹窗")
    except Exception as e:
        logger.warning(f"发送ESC失败（可能无弹窗）: {e}")

    tab.wait(1)

    # 获取滚动容器
    scroll_h = tab.run_js("var c=document.querySelector('.otl-scroll-container'); return c ? c.scrollHeight : document.body.scrollHeight;")
    logger.info(f"滚动容器高度: {scroll_h}px")

    if scroll_h and int(scroll_h) > 1000:
        total_h = int(scroll_h)
        step = 6000  # 更小的步长，确保捕获所有内容
        positions = list(range(0, total_h, step))
        if positions[-1] < total_h:
            positions.append(total_h)
        positions = sorted(set(positions))

        for pos in positions:
            js = f"var c=document.querySelector('.otl-scroll-container'); if(c) c.scrollTop={pos};"
            tab.run_js(js)
            tab.wait(1.0)
            text = tab('t:body').text
            parts.append(text)

        logger.info(f"提取完成，共 {len(positions)} 个位置")
    else:
        text = tab('t:body').text
        parts.append(text)
        logger.info(f"单次提取完成 ({len(text)} 字符)")

    return parts


def clean_text(text):
    """清理提取的文本，去掉UI元素和emoji列表"""
    idx = text.find("taskName - keyword")
    if idx > 0:
        text = text[:idx]
    for marker in ["取消悬浮", "顶部工具栏已关闭", "热门剧\n小丸子\n邀你登录"]:
        idx = text.rfind(marker)
        if idx > 0:
            text = text[:idx]
    return text.strip()


def parse_entries(all_text):
    """解析剧集条目 - 逐行扫描"""
    entries = []
    seen = set()

    lines = all_text.split('\n')
    current = None

    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue

        # 标准化unicode空格
        norm = s.replace('\u2006', ' ').replace('\u200a', ' ')

        # 检测标题行: 包含 .1080P 或 .720P 或 短剧 或 铂金珍藏版
        is_title = bool(re.search(r'\.1080P', norm, re.IGNORECASE) or
                        re.search(r'\.720P', norm, re.IGNORECASE) or
                        re.search(r'（1080P', norm) or
                        '铂金珍藏版' in norm)

        # 链接检测
        baidu_m = re.search(r'https?://pan\.baidu\.com/s/[a-zA-Z0-9_-]+', norm)
        quark_m = re.search(r'https?://pan\.quark\.cn/s/[a-zA-Z0-9]+', norm)
        pwd_m = re.search(r'提取码[：:\s]*(\w+)', norm)

        if is_title:
            # 保存之前的条目
            if current and current.get('title_raw'):
                key = current['title_raw']
                if key not in seen:
                    seen.add(key)
                    # 清理标题
                    title = current['title_raw'].replace('\u2006', ' ').strip()
                    # 提取tag
                    tag = ''
                    for t in ['【超前完结】', '【完结】', '【新】']:
                        if t in title:
                            tag = t
                            title = title.replace(t, '').strip()
                            break
                    entry = {'title': title, 'links': current.get('links', [])}
                    if tag:
                        entry['tag'] = tag
                    entries.append(entry)

            current = {'title_raw': s, 'links': []}

        elif baidu_m and current is not None:
            url = baidu_m.group(0)
            pwd = re.search(r'\?pwd=(\w+)', norm)
            current['links'].append({
                "type": "百度网盘",
                "url": url,
                "extract_code": pwd.group(1) if pwd else "1120"
            })

        elif quark_m and current is not None:
            current['links'].append({
                "type": "夸克网盘",
                "url": quark_m.group(0)
            })

    # 最后一个
    if current and current.get('title_raw'):
        key = current['title_raw']
        if key not in seen:
            title = current['title_raw'].replace('\u2006', ' ').strip()
            tag = ''
            for t in ['【超前完结】', '【完结】', '【新】']:
                if t in title:
                    tag = t
                    title = title.replace(t, '').strip()
                    break
            entry = {'title': title, 'links': current.get('links', [])}
            if tag:
                entry['tag'] = tag
            entries.append(entry)

    return entries


def normalize_line(line):
    """标准化单行文本"""
    return line.replace('\u2006', ' ').replace('\u200a', ' ').strip()


def parse_document(text_parts):
    """解析所有文本部分为结构化JSON"""
    # 先每段单独清理，再合并去重
    cleaned_parts = [clean_text(t) for t in text_parts]
    unique_lines = set()
    all_clean_lines = []
    for t in cleaned_parts:
        for line in t.split('\n'):
            key = line.strip()
            if key and key not in unique_lines:
                unique_lines.add(key)
                all_clean_lines.append(line)
    combined = '\n'.join(all_clean_lines)

    # 提取更新信息
    update_info = {}
    update_match = re.search(r'(\d{4}\.\d{1,2}\.\d{1,2})（(.+?)）', combined)
    if update_match:
        update_info = {"date": update_match.group(1), "label": update_match.group(2)}

    # 提取说明
    notes = []
    for line in combined.split('\n'):
        nl = normalize_line(line)
        if '搜索方法' in nl or '注意' in nl or '先转存' in nl or '夸克和谐' in nl or '夸克缺集数' in nl or '解决方法' in nl:
            notes.append(nl)
        elif re.match(r'[①②③④⑤]', nl.strip()):
            notes.append(nl.strip())

    entries = parse_entries(combined)

    result = {
        "title": "热门剧",
        "document_info": {
            "title": "热门剧",
            "source_url": KDOCS_URL,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "latest_update": update_info,
        "notes": '\n'.join(notes),
        "total_entries": len(entries),
        "entries": entries
    }

    return result


def save_json(data, filepath):
    """保存JSON到文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    count = len(data.get('entries', []))
    logger.success(f"已保存 {count} 条剧集到 {filepath}")


def fetch_once():
    """单次抓取流程"""
    browser = None
    try:
        browser, tab = connect_browser()
        logger.info("浏览器已连接")

        tab.get(KDOCS_URL)
        tab.wait(3)
        logger.info(f"页面已加载: {tab.title}")

        text_parts = extract_all_content(tab)
        data = parse_document(text_parts)
        save_json(data, OUTPUT_FILE)
        return True

    except Exception as e:
        logger.error(f"抓取出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        if browser:
            try:
                browser.quit()
            except:
                pass


def main():
    """主函数 - 支持单次或轮询模式"""
    import argparse

    parser = argparse.ArgumentParser(description="KDocs热门剧文档抓取工具")
    parser.add_argument("--poll", action="store_true", help="启用轮询模式（每30分钟）")
    parser.add_argument("--interval", type=int, default=POLL_INTERVAL, help="轮询间隔（秒）")
    parser.add_argument("--update-time", type=str, default="",
                        help="可选：设置更新时间标记，如 2026.5.24")
    args = parser.parse_args()

    if args.update_time:
        logger.info(f"设置更新时间: {args.update_time}")

    if args.poll:
        logger.info(f"启动轮询模式，间隔 {args.interval} 秒")
        while True:
            logger.info("=" * 50)
            logger.info(f"开始抓取: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            fetch_once()
            logger.info(f"等待 {args.interval} 秒后下次抓取...")
            time.sleep(args.interval)
    else:
        fetch_once()


if __name__ == "__main__":
    main()
