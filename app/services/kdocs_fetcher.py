"""
KDocs 数据源动态抓取服务
- 从数据库 kdocs_sources 表读取启用的数据源
- 使用 DrissionPage 无头浏览器抓取
- 支持任意数据源 URL，按 type 区分存储
"""
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from DrissionPage import Chromium, ChromiumOptions

logger = logging.getLogger(__name__)

RESULT_DIR = Path(__file__).parent.parent.parent / "date"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

KDOCS_PAGE_WAIT_SECONDS = float(os.getenv("KDOCS_PAGE_WAIT_SECONDS", "3"))
KDOCS_NETWORK_WAIT_SECONDS = float(os.getenv("KDOCS_NETWORK_WAIT_SECONDS", "8"))
KDOCS_EDITOR_WAIT_SECONDS = float(os.getenv("KDOCS_EDITOR_WAIT_SECONDS", "20"))
KDOCS_SCROLL_WAIT_SECONDS = float(os.getenv("KDOCS_SCROLL_WAIT_SECONDS", "1.2"))
KDOCS_SCROLL_STEP = int(os.getenv("KDOCS_SCROLL_STEP", "1200"))
KDOCS_STABLE_ROUNDS = int(os.getenv("KDOCS_STABLE_ROUNDS", "3"))
KDOCS_STABLE_WAIT_SECONDS = float(os.getenv("KDOCS_STABLE_WAIT_SECONDS", "0.8"))
KDOCS_MAX_ENTRIES = int(os.getenv("KDOCS_MAX_ENTRIES", "20"))


def _create_headless_browser():
    """创建无头浏览器"""
    co = ChromiumOptions(read_file=False)
    co.auto_port()
    chrome_bin = os.getenv("CHROME_BIN") or os.getenv("CHROMIUM_BIN")
    if chrome_bin:
        co.set_browser_path(chrome_bin)
    co.set_timeouts(base=10, page_load=25, script=10)
    co.headless(True)
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument("--disable-extensions")
    co.set_argument("--disable-background-networking")
    co.set_argument("--disable-sync")
    co.set_argument("--disable-default-apps")
    co.set_argument("--disable-popup-blocking")
    co.set_argument("--hide-scrollbars")
    co.set_argument("--mute-audio")
    co.set_argument("--window-size=1920,2400")
    if os.getenv("KDOCS_DISABLE_IMAGES", "0").lower() in {"1", "true", "yes"}:
        co.set_argument("--blink-settings=imagesEnabled=false")
    browser = Chromium(co)
    browser.set.timeouts(base=10, page_load=25, script=10)
    browser.set.retry_times(1)
    browser.set.retry_interval(0.5)
    browser.set.load_mode.eager()
    tab = browser.latest_tab
    tab.set.load_mode.eager()
    return browser, tab


def _extract_all_content(tab):
    """提取页面全部文本内容"""
    try:
        tab.run_js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', code: 'Escape', keyCode: 27, which: 27}))")
    except Exception:
        pass
    tab.wait(1.5)
    _wait_network_idle(tab)
    _wait_text_stable(tab)

    scroll_h = tab.run_js(
        "var c=document.querySelector('.otl-scroll-container'); return c ? c.scrollHeight : document.body.scrollHeight;"
    )

    parts = []
    if scroll_h and int(scroll_h) > 1000:
        total_h = int(scroll_h)
        step = KDOCS_SCROLL_STEP
        positions = list(range(0, total_h, step))
        if positions[-1] < total_h:
            positions.append(total_h)
        positions = sorted(set(positions))
        for pos in positions:
            js = f"var c=document.querySelector('.otl-scroll-container'); if(c) c.scrollTop={pos};"
            tab.run_js(js)
            _wait_network_idle(tab, timeout=KDOCS_SCROLL_WAIT_SECONDS)
            _wait_text_stable(tab, rounds=2)
            tab.wait(KDOCS_SCROLL_WAIT_SECONDS)
            parts.append(tab('t:body').text)
    else:
        parts.append(tab('t:body').text)
    return parts


def _start_network_listener(tab):
    """必须在 get/滚动等动作前启动监听，否则已发生的请求不会进入队列。"""
    try:
        tab.listen.start(
            targets=("kdocs.cn", "wpscdn.cn", "docer.wps.cn", "wps.cn"),
            method=True,
            res_type=True,
        )
    except Exception as e:
        logger.debug(f"KDocs 网络监听启动失败，继续使用 DOM/JS 等待: {e}")


def _wait_network_idle(tab, timeout=KDOCS_NETWORK_WAIT_SECONDS):
    """等待网络安静，避免 KDocs 文档 JS 数据还没落到页面就开始解析。"""
    try:
        return tab.listen.wait_silent(timeout=timeout, targets_only=False, limit=0)
    except Exception as e:
        logger.debug(f"KDocs 网络静默等待失败，继续后续解析: {e}")
        return False


def _wait_text_stable(tab, rounds=KDOCS_STABLE_ROUNDS):
    """等待 body 文本长度连续稳定，兜底处理虚拟滚动和异步渲染。"""
    last_len = -1
    stable = 0
    for _ in range(max(rounds * 3, rounds)):
        try:
            text_len = int(tab.run_js("return document.body ? document.body.innerText.length : 0;") or 0)
        except Exception:
            text_len = 0
        if text_len == last_len and text_len > 0:
            stable += 1
            if stable >= rounds:
                return True
        else:
            stable = 0
            last_len = text_len
        tab.wait(KDOCS_STABLE_WAIT_SECONDS)
    return False


def _extract_editor_json_entries(tab, max_entries=KDOCS_MAX_ENTRIES):
    """优先从 KDocs 编辑器 JSON 提取文档，并通过滚动加载虚拟片段。"""
    ready = _wait_editor_json_ready(tab)
    if not ready:
        logger.info("KDocs 编辑器 JSON 等待超时，继续尝试分段读取")

    entries = []
    by_title = {}

    def merge(items):
        for item in items or []:
            title = item.get("title", "")
            if not title or not item.get("links"):
                continue
            if title not in by_title:
                by_title[title] = item
                entries.append(item)
                continue
            old_links = by_title[title].setdefault("links", [])
            old_keys = {(link.get("type"), link.get("url")) for link in old_links}
            for link in item.get("links", []):
                key = (link.get("type"), link.get("url"))
                if key not in old_keys:
                    old_links.append(link)
                    old_keys.add(key)

    merge(_read_editor_json_entries(tab))
    if 0 < max_entries <= len(entries):
        logger.info(f"KDocs 编辑器 JSON 提取到前 {len(entries)} 条，停止继续滚动")
        return entries

    try:
        scroll_h = int(tab.run_js(
            "var c=document.querySelector('.otl-scroll-container'); return c ? c.scrollHeight : document.body.scrollHeight;"
        ) or 0)
    except Exception:
        scroll_h = 0

    if scroll_h > 1000:
        positions = list(range(0, scroll_h, KDOCS_SCROLL_STEP))
        if not positions or positions[-1] < scroll_h:
            positions.append(scroll_h)

        for pos in sorted(set(positions)):
            tab.run_js(f"var c=document.querySelector('.otl-scroll-container'); if(c) c.scrollTop={pos};")
            tab.wait(KDOCS_SCROLL_WAIT_SECONDS)
            _wait_network_idle(tab, timeout=0.5)
            merge(_read_editor_json_entries(tab))
            if 0 < max_entries <= len(entries):
                logger.info(f"KDocs 编辑器 JSON 提取到前 {len(entries)} 条，停止继续滚动")
                break

    if entries:
        logger.info(f"KDocs 编辑器 JSON 分段提取完成: {len(entries)} 条")
        return entries
    return None


def _read_editor_json_entries(tab):
    """读取当前 KDocs 虚拟片段中的编辑器 JSON 条目。"""
    script = r"""
        return (() => {
            function walk(node, paragraphs) {
                if (!node) return;
                if (node.type === 'paragraph' && node.content) {
                    let text = '';
                    let hrefs = [];
                    for (const c of node.content) {
                        if (c.type === 'text' && c.text) text += c.text;
                        if (c.type === 'emoji' && c.attrs && c.attrs.emoji) text += c.attrs.emoji;
                        if (c.marks) {
                            for (const m of c.marks) {
                                if (m.type === 'link' && m.attrs && m.attrs.href) hrefs.push(m.attrs.href);
                            }
                        }
                    }
                    paragraphs.push({text: text.trim(), hrefs});
                }
                if (node.content) node.content.forEach(child => walk(child, paragraphs));
            }

            const editor = window.COLLABX && window.COLLABX.editor;
            if (!editor || typeof editor.getJSON !== 'function') {
                return JSON.stringify({ok: false, reason: 'COLLABX.editor.getJSON not ready'});
            }

            const paragraphs = [];
            walk(editor.getJSON(), paragraphs);

            const noise = [
                '搜索方法', '注意', '解决方法', '先转存', '取消悬浮',
                '顶部工具栏', 'taskName - keyword', '邀你登录', '热门剧'
            ];
            const entries = [];
            let cur = null;

            function pushCur() {
                if (cur && cur.title && cur.links.length) entries.push(cur);
                cur = null;
            }

            function firstUrl(text, hrefs, re) {
                for (const href of hrefs || []) {
                    const m = String(href).match(re);
                    if (m) return m[0];
                }
                const m = String(text || '').match(re);
                return m ? m[0] : null;
            }

            for (const p of paragraphs) {
                const t = (p.text || '').replace(/\u2006|\u200a/g, ' ').trim();
                if (!t) continue;
                if (noise.some(k => t.includes(k))) continue;

                const baidu = firstUrl(t, p.hrefs, /https?:\/\/pan\.baidu\.com\/s\/[a-zA-Z0-9_-]+/);
                const quark = firstUrl(t, p.hrefs, /https?:\/\/pan\.quark\.cn\/s\/[a-zA-Z0-9]+/);
                const pwd = t.match(/(?:提取码|密码|pwd)\s*[：:\s]*([a-zA-Z0-9]{4,})/i);

                if (baidu) {
                    if (cur) cur.links.push({type: '百度网盘', url: baidu, extract_code: pwd ? pwd[1] : '1120'});
                    continue;
                }
                if (pwd) {
                    if (cur) {
                        const link = [...cur.links].reverse().find(item => item.type === '百度网盘');
                        if (link) link.extract_code = pwd[1];
                    }
                    continue;
                }
                if (quark) {
                    if (cur) cur.links.push({type: '夸克网盘', url: quark});
                    continue;
                }

                const title = t
                    .replace(/^[\s.。、《》\[\]（）()，,：:;；!?！？-]+/, '')
                    .replace(/[\s.。、《》\[\]（）()，,：:;；!?！？-]+$/, '')
                    .trim();
                if (!title || title.length > 120) continue;

                pushCur();
                cur = {title, links: []};
                const tag = title.match(/【(.+?)】/);
                if (tag) cur.tag = `【${tag[1]}】`;
            }
            pushCur();

            return JSON.stringify({ok: true, total_entries: entries.length, entries});
        })();
    """
    try:
        raw = tab.run_js(script)
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception as e:
        logger.debug(f"KDocs 编辑器 JSON 提取失败: {e}")
        return None

    if not data or not data.get("ok"):
        logger.info(f"KDocs 编辑器 JSON 未就绪: {(data or {}).get('reason')}")
        return None

    entries = data.get("entries") or []
    return entries


def _wait_editor_json_ready(tab):
    """等待 KDocs 编辑器对象和正文 JSON 就绪。"""
    checks = max(1, int(KDOCS_EDITOR_WAIT_SECONDS / 0.5))
    script = """
        return !!(
            window.COLLABX &&
            window.COLLABX.editor &&
            typeof window.COLLABX.editor.getJSON === 'function' &&
            window.COLLABX.editor.getJSON() &&
            window.COLLABX.editor.getJSON().content &&
            window.COLLABX.editor.getJSON().content.length
        );
    """
    for _ in range(checks):
        try:
            if tab.run_js(script):
                return True
        except Exception:
            pass
        _wait_network_idle(tab, timeout=0.5)
        tab.wait(0.5)
    return False


def _clean_text(text):
    """清理提取的文本"""
    idx = text.find("taskName - keyword")
    if idx > 0:
        text = text[:idx]
    for marker in ["取消悬浮", "顶部工具栏已关闭", "热门剧\n小丸子\n邀你登录"]:
        i = text.rfind(marker)
        if i > 0:
            text = text[:i]
    return text.strip()


def _parse_title(title):
    """从原始标题解析字段"""
    quality = "1080P"
    if "4K" in title:
        quality = "4K"
    elif "1080P" in title:
        quality = "1080P"
    elif "720P" in title:
        quality = "720P"

    episode = ""
    m = re.search(r'更(\d+\.?\d*)[期集]?', title)
    if m:
        episode = f"更{m.group(1)}"
    else:
        m = re.search(r'(\d+\.?\d*)[期集]全', title)
        if m:
            episode = f"{m.group(1)}集全"

    status = None
    if "完结" in title:
        status = "已完结"
    elif "超前" in title:
        status = "超前点播"
    elif "铂金" in title or "高码" in title:
        status = "珍藏版"

    clean = title.strip()
    # 只去除首尾的标点符号
    clean = re.sub(r'^[\.\s,，、、;；：:！!?？]+|[\.\s,，、、;；：:！!?？]+$', '', clean)

    update_time = None
    tm = re.search(r'(\d{1,2})\.(\d{1,2})', title)
    if tm:
        mo, da = tm.group(1).zfill(2), tm.group(2).zfill(2)
        if int(mo) <= 12:
            update_time = f"{mo}-{da}"

    return {"title": clean, "quality": quality, "episode": episode, "status": status, "update_time": update_time}


def _parse_entries(all_text):
    """解析剧集条目"""
    entries = []
    seen = set()
    lines = all_text.split('\n')
    current = None

    for line in lines:
        s = line.strip()
        if not s:
            continue
        norm = s.replace('\u2006', ' ').replace('\u200a', ' ')

        is_title = bool(
            re.search(r'\.1080P', norm, re.IGNORECASE)
            or re.search(r'\.720P', norm, re.IGNORECASE)
            or re.search(r'（1080P', norm)
            or '铂金珍藏版' in norm
        )

        baidu_m = re.search(r'https?://pan\.baidu\.com/s/[a-zA-Z0-9_-]+', norm)
        quark_m = re.search(r'https?://pan\.quark\.cn/s/[a-zA-Z0-9]+', norm)

        if is_title:
            if current and current.get('title_raw'):
                key = current['title_raw']
                if key not in seen:
                    seen.add(key)
                    t = current['title_raw'].replace('\u2006', ' ').strip()
                    tag = ''
                    for tg in ['【超前完结】', '【完结】', '【新】']:
                        if tg in t:
                            tag = tg
                            t = t.replace(tg, '').strip()
                            break
                    entry = {'title': t, 'links': current.get('links', [])}
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
            current['links'].append({"type": "夸克网盘", "url": quark_m.group(0)})

    if current and current.get('title_raw') and current['title_raw'] not in seen:
        t = current['title_raw'].replace('\u2006', ' ').strip()
        tag = ''
        for tg in ['【超前完结】', '【完结】', '【新】']:
            if tg in t:
                tag = tg
                t = t.replace(tg, '').strip()
                break
        entry = {'title': t, 'links': current.get('links', [])}
        if tag:
            entry['tag'] = tag
        entries.append(entry)

    return entries


def _parse_document(text_parts):
    """解析所有文本为结构化数据"""
    cleaned_parts = [_clean_text(t) for t in text_parts]
    unique_lines = set()
    all_clean = []
    for t in cleaned_parts:
        for line in t.split('\n'):
            key = line.strip()
            if key and key not in unique_lines:
                unique_lines.add(key)
                all_clean.append(line)
    combined = '\n'.join(all_clean)

    entries = _parse_entries(combined)
    return entries


def _fetch_with_tab(tab, url, label, max_entries=KDOCS_MAX_ENTRIES):
    """使用已有标签页抓取单个数据源。"""
    logger.info(f"[{label}] 开始抓取: {url}")
    _start_network_listener(tab)
    tab.get(url)
    _wait_network_idle(tab)
    tab.wait(KDOCS_PAGE_WAIT_SECONDS)
    logger.info(f"[{label}] 页面加载完成: {tab.title}")

    entries = _extract_editor_json_entries(tab, max_entries=max_entries)
    if entries is None:
        logger.info(f"[{label}] 编辑器 JSON 不可用，回退到 DOM 滚动提取")
        text_parts = _extract_all_content(tab)
        entries = _parse_document(text_parts)
    if max_entries > 0 and len(entries) > max_entries:
        logger.info(f"[{label}] 只同步前 {max_entries} 条，原始抓取 {len(entries)} 条")
        entries = entries[:max_entries]
    logger.info(f"[{label}] 抓取完成: {len(entries)} 条")
    return entries


def fetch_single_source(url, label, max_entries=KDOCS_MAX_ENTRIES):
    """抓取单个数据源"""
    browser = None
    try:
        browser, tab = _create_headless_browser()
        return _fetch_with_tab(tab, url, label, max_entries=max_entries)
    except Exception as e:
        logger.error(f"[{label}] 抓取出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    finally:
        if browser:
            try:
                browser.quit()
            except Exception:
                pass


async def fetch_single_source_from_db(source_id: int):
    """根据数据库中的 source_id 抓取单个数据源"""
    from app.database import async_session
    from app.models.admin_models import KDocsSource
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(KDocsSource).where(KDocsSource.id == source_id))
        src = result.scalar_one_or_none()
        if not src:
            logger.error(f"数据源 {source_id} 不存在")
            return None, None
        if not src.enabled:
            logger.info(f"数据源 {src.name} 已禁用，跳过")
            return None, None
        url, label, media_type = src.url, src.name, src.type

    entries = fetch_single_source(url, label)
    if entries is not None:
        backup_path = RESULT_DIR / f"{label}.json"
        data = {
            "title": label,
            "document_info": {
                "title": label,
                "source_url": url,
                "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "total_entries": len(entries),
            "entries": entries,
        }
        backup_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[{label}] 已保存备份到 {backup_path}")
        return media_type, entries
    return None, None


async def fetch_all_sources():
    """从数据库读取所有启用的数据源并全部抓取"""
    from app.database import async_session
    from app.models.admin_models import KDocsSource
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(KDocsSource).where(KDocsSource.enabled == True))
        sources = result.scalars().all()

    if not sources:
        logger.warning("没有启用的数据源")
        return {}

    results = {}
    browser = None
    try:
        browser, tab = _create_headless_browser()
        for src in sources:
            try:
                entries = _fetch_with_tab(tab, src.url, src.name, max_entries=0)
            except Exception as e:
                logger.error(f"[{src.name}] 抓取出错: {e}")
                import traceback
                logger.error(traceback.format_exc())
                entries = None

            if entries is not None:
                backup_path = RESULT_DIR / f"{src.name}.json"
                data = {
                    "title": src.name,
                    "document_info": {
                        "title": src.name,
                        "source_url": src.url,
                        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    "total_entries": len(entries),
                    "entries": entries,
                }
                backup_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                results[src.type] = entries
                logger.info(f"[{src.name}] 已保存备份到 {backup_path}")
            else:
                logger.warning(f"[{src.name}] 抓取失败")
    finally:
        if browser:
            try:
                browser.quit()
            except Exception:
                pass
    return results
