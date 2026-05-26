// kdocs_extract.js - 金山文档数据提取脚本
// 在浏览器页面中执行，提取文档的 JSON 结构并解析为条目
(() => {
    try {
        const editor = window.COLLABX.editor;
        const json = editor.getJSON();

        const texts = [];
        function walk(node) {
            if (node.type === 'text' && node.text) texts.push(node.text);
            if (node.type === 'emoji' && node.attrs && node.attrs.emoji) texts.push(node.attrs.emoji);
            if (node.content) node.content.forEach(function(c) { walk(c); });
        }
        walk(json);
        const allText = texts.join('\n');

        const now = new Date();
        function pad(n) { return String(n).padStart(2, '0'); }
        const fetchTime = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate()) +
            ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());

        var updateDate = null;
        var updateTime = null;

        var headingMatch = allText.match(/(\d{4})\.(\d{1,2})\.(\d{1,2})/);
        if (headingMatch) {
            updateDate = headingMatch[1] + '-' + pad(parseInt(headingMatch[2])) + '-' + pad(parseInt(headingMatch[3]));
        }

        var timeMatch = allText.match(/(\d{1,2}):(\d{2})\s*\u66f4\u65b0/);
        if (timeMatch) {
            updateTime = pad(parseInt(timeMatch[1])) + ':' + timeMatch[2];
        }

        var paragraphs = [];
        function collect(node) {
            if (!node || !node.content) return;
            for (var i = 0; i < node.content.length; i++) {
                var child = node.content[i];
                if (child.type === 'paragraph' && child.content) {
                    var text = '';
                    var href = null;
                    for (var j = 0; j < child.content.length; j++) {
                        var c = child.content[j];
                        if (c.type === 'text' && c.text) text += c.text;
                        if (c.type === 'emoji' && c.attrs && c.attrs.emoji) text += c.attrs.emoji;
                        if (c.marks) {
                            for (var k = 0; k < c.marks.length; k++) {
                                var m = c.marks[k];
                                if (m.type === 'link' && m.attrs && m.attrs.href) href = m.attrs.href;
                            }
                        }
                    }
                    paragraphs.push({ text: text.trim(), href: href });
                }
                collect(child);
            }
        }
        collect(json);

        var noise = [
            'solution','resolve','copy','open app','auto pop','click save',
            'back to','search','notice','save first','top right',
            'quark harmony','quark missing'
        ];

        var entries = [];
        var cur = null;

        for (var pi = 0; pi < paragraphs.length; pi++) {
            var p = paragraphs[pi];
            var t = p.text;
            if (!t) continue;

            if (t.indexOf('\u767e\u5ea6\u94fe\u63a5') !== -1 || (p.href && t.indexOf('pan.baidu.com') !== -1)) {
                if (cur) cur.baiduUrl = p.href || t.replace(/^\u767e\u5ea6\u94fe\u63a5\s*[\uff1a:]\s*/, '').trim();
            } else if (t.indexOf('\u63d0\u53d6\u7801') === 0) {
                var pwMatch = t.match(/\u63d0\u53d6\u7801\s*[\uff1a:]\s*(\S+)/);
                if (cur && pwMatch) cur.baiduPassword = pwMatch[1];
            } else if (t.indexOf('\u5938\u514b\u94fe\u63a5') !== -1 || (p.href && t.indexOf('pan.quark.cn') !== -1)) {
                if (cur) cur.quarkUrl = p.href || t.replace(/^\u5938\u514b\u94fe\u63a5\s*[\uff1a:]\s*/, '').trim();
            } else if (t.indexOf('4K\u94fe\u63a5') !== -1 || t.indexOf('4K') === 0) {
                if (cur) {
                    var k4 = t.replace(/^4K\s*\u94fe\u63a5\s*[\uff1a:]\s*/, '').trim();
                    cur.k4Note = k4 || '\u70ed\u5267\u30104K\u207a\u3011\u6e05\u6670\u5ea6\u4e13\u7528\u6587\u6863(NEW)';
                }
            } else if (noise.some(function(k) { return t.indexOf(k) !== -1; })) {
                continue;
            } else {
                if (cur) entries.push(cur);
                var raw = t.replace(/^[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]\s*/u, '');
                var qM = raw.match(/(\d{3,4}P)/);
                var epM = raw.match(/(\u66f4\s*\d+)/);
                var stM = raw.match(/\u3010(.+?)\u3011/);
                cur = {
                    title: raw.replace(/\.\d{3,4}P.*/, '').trim(),
                    quality: qM ? qM[1] : null,
                    episode: epM ? epM[1] : null,
                    status: stM ? stM[1] : null,
                    baiduUrl: null,
                    baiduPassword: null,
                    quarkUrl: null,
                    k4Note: null
                };
            }
        }
        if (cur) entries.push(cur);

        return JSON.stringify({
            meta: {
                source: 'kdocs.cn',
                url: window.location.href,
                title: document.title || '',
                fetch_time: fetchTime,
                update_date: updateDate,
                update_time: updateTime
            },
            entries: entries.map(function(e, i) {
                return {
                    index: i + 1,
                    title: e.title,
                    quality: e.quality,
                    episode: e.episode,
                    status: e.status,
                    fetch_time: fetchTime,
                    update_date: updateDate,
                    update_time: updateTime,
                    baidu_url: e.baiduUrl,
                    baidu_password: e.baiduPassword,
                    quark_url: e.quarkUrl,
                    k4_note: e.k4Note
                };
            }),
            total_entries: entries.length
        });
    } catch (e) {
        return JSON.stringify({ error: e.message, stack: e.stack });
    }
})()