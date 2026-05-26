// kdocs_dismiss_login.js - 关闭金文档登录弹窗
(function() {
    var btns = document.querySelectorAll('button, a, [role=button], .close, .cancel, [class*=close], [class*=cancel]');
    var found = [];
    btns.forEach(function(b) {
        var t = (b.innerText || b.textContent || '').trim();
        if (t) {
            var isTarget = t === '\u00d7' ||
                t.indexOf('\u53d6\u6d88') !== -1 ||
                t.indexOf('\u5173\u95ed') !== -1 ||
                t.indexOf('Cancel') !== -1 ||
                t.indexOf('Close') !== -1 ||
                t.indexOf('\u8df3\u8fc7') !== -1 ||
                t.indexOf('Skip') !== -1;
            if (isTarget) {
                found.push({text: t, tag: b.tagName, cls: b.className});
            }
        }
    });
    if (found.length > 0) {
        var closeBtns = document.querySelectorAll('[class*=close], [class*=cancel], .dialog-close, .modal-close');
        for (var i = 0; i < closeBtns.length; i++) {
            var b = closeBtns[i];
            var t = (b.innerText || b.textContent || '').trim();
            if (!t || t === '\u00d7' || t.indexOf('\u5173\u95ed') !== -1 || t.indexOf('\u53d6\u6d88') !== -1) {
                b.click();
                return 'clicked_close_icon';
            }
        }
        var allBtns = document.querySelectorAll('button, a');
        for (var j = 0; j < allBtns.length; j++) {
            var b2 = allBtns[j];
            var t2 = (b2.innerText || b2.textContent || '').trim();
            if (t2 === '\u53d6\u6d88' || t2 === '\u5173\u95ed' || t2 === 'Cancel') {
                b2.click();
                return 'clicked_' + t2;
            }
            if (t2 === '\u8df3\u8fc7' || t2 === 'Skip') {
                b2.click();
                return 'clicked_skip';
            }
        }
        document.body.click();
        return 'clicked_body';
    }
    return 'no_login_dialog';
})()