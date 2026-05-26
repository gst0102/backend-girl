CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    openid          VARCHAR(64) NOT NULL,
    nickname        VARCHAR(50) NOT NULL DEFAULT '用户',
    avatar          VARCHAR(20) NOT NULL DEFAULT '👤',
    invite_count    INTEGER     NOT NULL DEFAULT 0,
    continuous_days INTEGER     NOT NULL DEFAULT 0,
    last_record_at  TIMESTAMPTZ          DEFAULT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_openid       ON users (openid);
CREATE INDEX IF NOT EXISTS        idx_users_invite_count  ON users (invite_count);


CREATE TABLE IF NOT EXISTS invite_relations (
    id             BIGSERIAL    NOT NULL,
    inviter_id     UUID         NOT NULL,
    invitee_id     UUID         NOT NULL,
    invitee_openid VARCHAR(64)  NOT NULL,
    invitee_device VARCHAR(100)          DEFAULT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_invite_relations_inviter FOREIGN KEY (inviter_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_invite_relations_invitee FOREIGN KEY (invitee_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_invite_relations_invitee_openid ON invite_relations (invitee_openid);
CREATE INDEX IF NOT EXISTS        idx_invite_relations_inviter_id      ON invite_relations (inviter_id);


CREATE TABLE IF NOT EXISTS records (
    id           BIGSERIAL    NOT NULL,
    user_id      UUID         NOT NULL,
    record_type  VARCHAR(20)  NOT NULL,
    record_date  DATE         NOT NULL,
    record_value JSONB                 DEFAULT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_records_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_records_user_type_date ON records (user_id, record_type, record_date);
CREATE INDEX IF NOT EXISTS        idx_records_user_date      ON records (user_id, record_date);


CREATE TABLE IF NOT EXISTS user_features (
    id          BIGSERIAL    NOT NULL,
    user_id     UUID         NOT NULL,
    feature_key VARCHAR(30)  NOT NULL,
    unlocked_at TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_user_features_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_features_user_feature ON user_features (user_id, feature_key);


CREATE TABLE IF NOT EXISTS badges (
    id              VARCHAR(20)  NOT NULL,
    name            VARCHAR(30)  NOT NULL,
    icon            VARCHAR(10)  NOT NULL,
    rarity          VARCHAR(10)  NOT NULL,
    condition_type  VARCHAR(30)  NOT NULL,
    condition_value INTEGER      NOT NULL,
    PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS user_badges (
    id        BIGSERIAL    NOT NULL,
    user_id   UUID         NOT NULL,
    badge_id  VARCHAR(20)  NOT NULL,
    earned_at TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_user_badges_user  FOREIGN KEY (user_id)  REFERENCES users (id)  ON DELETE CASCADE,
    CONSTRAINT fk_user_badges_badge FOREIGN KEY (badge_id) REFERENCES badges (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges (user_id);


CREATE TABLE IF NOT EXISTS push_logs (
    id          BIGSERIAL    NOT NULL,
    user_id     UUID         NOT NULL,
    template_id VARCHAR(50)  NOT NULL,
    content     TEXT         NOT NULL,
    channel     VARCHAR(20)  NOT NULL,
    status      SMALLINT     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at     TIMESTAMPTZ           DEFAULT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_push_logs_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_push_logs_user_status ON push_logs (user_id, status);
CREATE INDEX IF NOT EXISTS idx_push_logs_created_at  ON push_logs (created_at);


CREATE TABLE IF NOT EXISTS reward_logs (
    id           BIGSERIAL    NOT NULL,
    user_id      UUID         NOT NULL,
    reward_type  VARCHAR(20)  NOT NULL,
    reward_value VARCHAR(50)  NOT NULL,
    grant_reason VARCHAR(50)  NOT NULL,
    granted_at   TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_reward_logs_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reward_logs_user_id ON reward_logs (user_id);


CREATE TABLE IF NOT EXISTS config_unlock (
    id           BIGSERIAL    NOT NULL,
    threshold    INTEGER      NOT NULL,
    feature_key  VARCHAR(30)  NOT NULL,
    feature_name VARCHAR(50)  NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_config_unlock_feature_key ON config_unlock (feature_key);
CREATE INDEX IF NOT EXISTS idx_config_unlock_threshold ON config_unlock (threshold);


CREATE TABLE IF NOT EXISTS config_push_templates (
    id          BIGSERIAL    NOT NULL,
    template_id VARCHAR(50)  NOT NULL,
    title       VARCHAR(100) NOT NULL,
    content     TEXT         NOT NULL,
    channel     VARCHAR(20)  NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_config_push_templates_template_id ON config_push_templates (template_id);


CREATE TABLE IF NOT EXISTS animes (
    id              VARCHAR(20)  NOT NULL,
    name            VARCHAR(100) NOT NULL,
    cover           VARCHAR(20)  NOT NULL DEFAULT '📺',
    update_day      SMALLINT     NOT NULL,
    description     TEXT                  DEFAULT NULL,
    latest_episode  INTEGER      NOT NULL DEFAULT 0,
    status          SMALLINT     NOT NULL DEFAULT 1,
    PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS user_anime_subscriptions (
    id            BIGSERIAL    NOT NULL,
    user_id       UUID         NOT NULL,
    anime_id      VARCHAR(20)  NOT NULL,
    subscribed_at TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_user_anime_subs_user  FOREIGN KEY (user_id)  REFERENCES users (id)  ON DELETE CASCADE,
    CONSTRAINT fk_user_anime_subs_anime FOREIGN KEY (anime_id) REFERENCES animes (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_anime_subs_unique ON user_anime_subscriptions (user_id, anime_id);
CREATE INDEX IF NOT EXISTS        idx_user_anime_subs_user   ON user_anime_subscriptions (user_id);


CREATE TABLE IF NOT EXISTS anime_drive_resources (
    id         BIGSERIAL    NOT NULL,
    anime_id   VARCHAR(20)  NOT NULL,
    episode    INTEGER      NOT NULL,
    url        VARCHAR(500) NOT NULL,
    password   VARCHAR(20)           DEFAULT NULL,
    expire_at  TIMESTAMPTZ           DEFAULT NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_anime_drive_anime FOREIGN KEY (anime_id) REFERENCES animes (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_anime_drive_anime_ep ON anime_drive_resources (anime_id, episode);


INSERT INTO config_unlock (threshold, feature_key, feature_name) VALUES
    (1,  'sleep',          '睡眠记录'),
    (3,  'water',          '喝水提醒'),
    (8,  'anime_remind',   '追番提醒'),
    (15, 'anime_preview',  '追番预告'),
    (30, 'anime_drive',    '网盘资源')
ON CONFLICT DO NOTHING;


INSERT INTO config_push_templates (template_id, title, content, channel) VALUES
    ('msg_invite_progress',  '邀请进度更新', '你已经邀请了{count}人，还差{remaining}人就能解锁{feature}',                   'popup'),
    ('msg_feature_unlock',   '新功能解锁',   '恭喜！你已解锁{feature}',                                                     'popup'),
    ('msg_continuous_7',     '连续记录7天',  '恭喜你连续记录7天，获得🔥徽章',                                                'popup'),
    ('msg_daily_reminder',   '每日提醒',     '今天还没记录，点一下只需要2秒',                                                  'notice'),
    ('msg_low_activity',     '低活跃提醒',   '{nickname}，已经7天没记录了，记得来打卡哦！',                                   'popup'),
    ('msg_weekly_report',    '周报推送',     '本周你记录了{day_count}天，继续保持！',                                           'popup')
ON CONFLICT DO NOTHING;


INSERT INTO badges (id, name, icon, rarity, condition_type, condition_value) VALUES
    ('badge_001', '连续拉屎7天', '💩', 'rare', 'continuous_days', 7),
    ('badge_002', '连续拉屎14天', '💩✨', 'epic', 'continuous_days', 14),
    ('badge_003', '连续拉屎30天', '💩🏆', 'epic', 'continuous_days', 30),
    ('badge_004', '记录满7天', '📅', 'common', 'record_count', 7),
    ('badge_005', '记录满30天', '📅✨', 'rare', 'record_count', 30),
    ('badge_006', '记录满100天', '📅🏆', 'epic', 'record_count', 100),
    ('badge_007', '邀请1人', '🤝', 'common', 'invite_count', 1),
    ('badge_008', '邀请3人', '🤝✨', 'rare', 'invite_count', 3),
    ('badge_009', '邀请10人', '🤝🏆', 'epic', 'invite_count', 10),
    ('badge_010', '裂变之王', '🏆', 'epic', 'invite_count', 30)
ON CONFLICT DO NOTHING;


COMMENT ON TABLE users                  IS '用户表 - 微信小程序用户基础信息';
COMMENT ON TABLE invite_relations       IS '邀请关系表 - 记录邀请人与被邀请人的绑定关系';
COMMENT ON TABLE records                IS '记录表 - 用户每日行为记录（便便/姨妈/睡眠/喝水等）';
COMMENT ON TABLE user_features          IS '功能解锁表 - 用户已解锁的功能模块';
COMMENT ON TABLE badges                 IS '徽章表 - 徽章定义与获取条件';
COMMENT ON TABLE user_badges            IS '用户徽章表 - 用户已获得的徽章';


CREATE TABLE IF NOT EXISTS media_library (
    id              SERIAL       NOT NULL,
    source_type     VARCHAR(20)  NOT NULL,
    title           VARCHAR(200) NOT NULL,
    quality         VARCHAR(20)           DEFAULT NULL,
    episode         VARCHAR(50)           DEFAULT NULL,
    status          VARCHAR(50)           DEFAULT NULL,
    baidu_url       TEXT                  DEFAULT NULL,
    baidu_password  VARCHAR(20)           DEFAULT NULL,
    quark_url       TEXT                  DEFAULT NULL,
    k4_note         VARCHAR(500)          DEFAULT NULL,
    update_date     DATE                  DEFAULT NULL,
    fetch_time      TIMESTAMPTZ           DEFAULT NULL,
    is_active       SMALLINT     NOT NULL DEFAULT 1,
    content_hash    VARCHAR(64)           DEFAULT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uk_media_source_title UNIQUE (source_type, title)
);

CREATE INDEX IF NOT EXISTS idx_media_type  ON media_library (source_type);
CREATE INDEX IF NOT EXISTS idx_media_title ON media_library (title);

COMMENT ON TABLE media_library IS '内容库 - 番剧+电影统一存储';


CREATE TABLE IF NOT EXISTS remind_me_records (
    id              SERIAL       NOT NULL,
    user_id         UUID         NOT NULL,
    source_type     VARCHAR(20)  NOT NULL DEFAULT 'anime',
    media_title     VARCHAR(200) NOT NULL,
    remind_episode  VARCHAR(50)           DEFAULT NULL,
    status          SMALLINT     NOT NULL DEFAULT 0,
    remind_at       TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pushed_at       TIMESTAMPTZ           DEFAULT NULL,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_remind_pending ON remind_me_records (status, source_type, media_title);

COMMENT ON TABLE remind_me_records IS '催更记录表';


CREATE TABLE IF NOT EXISTS kdocs_anime_subscriptions (
    id          SERIAL       NOT NULL,
    user_id     UUID         NOT NULL,
    media_id    INTEGER      NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_kdocs_user_media UNIQUE (user_id, media_id)
);

CREATE INDEX IF NOT EXISTS idx_kdocs_sub_user  ON kdocs_anime_subscriptions (user_id);
CREATE INDEX IF NOT EXISTS idx_kdocs_sub_media ON kdocs_anime_subscriptions (media_id);

COMMENT ON TABLE kdocs_anime_subscriptions IS '番剧订阅表 - 用户订阅media_library条目';


CREATE TABLE IF NOT EXISTS user_subscribe_msg (
    user_id     UUID        NOT NULL,
    openid      VARCHAR(100) NOT NULL,
    is_enabled  SMALLINT    NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id)
);

COMMENT ON TABLE user_subscribe_msg IS '用户订阅消息授权表';
COMMENT ON TABLE push_logs              IS '推送记录表 - 推送消息的发送记录';
COMMENT ON TABLE reward_logs            IS '奖励记录表 - 用户奖励下发记录';
COMMENT ON TABLE config_unlock          IS '解锁阈值配置表 - 邀请人数对应的功能解锁配置';
COMMENT ON TABLE config_push_templates  IS '推送模板配置表 - 推送消息模板定义';
COMMENT ON TABLE animes                 IS '番剧表 - 番剧基础信息（名称/封面/更新日等）';
COMMENT ON TABLE user_anime_subscriptions IS '用户订阅表 - 用户追番订阅关系';
COMMENT ON TABLE anime_drive_resources  IS '网盘资源表 - 番剧每集对应的网盘下载链接';