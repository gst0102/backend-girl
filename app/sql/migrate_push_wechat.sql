-- ==============================
-- 迁移：添加微信订阅消息推送相关字段
-- ==============================

-- 1. push_logs 表：添加微信推送数据字段
ALTER TABLE push_logs
    ADD COLUMN IF NOT EXISTS wechat_data TEXT DEFAULT NULL;

-- 2. config_push_templates 表：添加微信模板ID和跳转页面
ALTER TABLE config_push_templates
    ADD COLUMN IF NOT EXISTS wechat_template_id VARCHAR(100) DEFAULT NULL;

ALTER TABLE config_push_templates
    ADD COLUMN IF NOT EXISTS wechat_keywords TEXT DEFAULT NULL;

-- ==============================
-- 3. 插入追番相关的推送模板（微信订阅消息）
-- ==============================
INSERT INTO config_push_templates (template_id, title, content, channel, wechat_template_id, wechat_keywords)
SELECT 'msg_anime_update', '追番更新提醒', '你订阅的《{anime_title}》更新了：{episode}，点击查看最新资源', 'subscribe', NULL, '{"thing1":"{anime_title}","thing2":"{episode}","date3":"{update_time}"}'
WHERE NOT EXISTS (SELECT 1 FROM config_push_templates WHERE template_id = 'msg_anime_update');

INSERT INTO config_push_templates (template_id, title, content, channel, wechat_template_id, wechat_keywords)
SELECT 'msg_anime_remind', '剧集催更提醒', '你催更的《{anime_title}》有新资源了：{episode}，快来看看吧', 'subscribe', NULL, '{"thing1":"{anime_title}","thing2":"{episode}","date3":"{update_time}"}'
WHERE NOT EXISTS (SELECT 1 FROM config_push_templates WHERE template_id = 'msg_anime_remind');

INSERT INTO config_push_templates (template_id, title, content, channel, wechat_template_id, wechat_keywords)
SELECT 'msg_daily_reminder', '每日打卡提醒', '亲爱的，今天还没有记录哦，快来打卡吧~', 'subscribe', NULL, '{"thing1":"今日打卡提醒","date3":"{today}"}'
WHERE NOT EXISTS (SELECT 1 FROM config_push_templates WHERE template_id = 'msg_daily_reminder');