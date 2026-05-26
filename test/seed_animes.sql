-- ==================================================
-- 番剧中心 DDL + 初始数据
-- 执行方式: psql -U postgres -d your_db -f seed_animes.sql
-- ==================================================

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

-- 番剧初始数据
INSERT INTO animes (id, name, cover, update_day, description, latest_episode, status) VALUES
('1', '咒术回战 第三季', '📺', 6, '热血战斗番', 8, 1),
('2', '我独自升级 第二季', '📺', 7, '爽文改编', 5, 1),
('3', '鬼灭之刃 柱训练篇', '📺', 1, '热血番', 3, 1),
('4', '葬送的芙莉莲', '📺', 2, '治愈奇幻', 12, 2)
ON CONFLICT (id) DO NOTHING;

-- 网盘资源初始数据
INSERT INTO anime_drive_resources (anime_id, episode, url, password, expire_at) VALUES
('1', 8, 'https://pan.baidu.com/s/zzz_fake_001', 'abcd', '2026-12-31 23:59:59+08'),
('2', 5, 'https://pan.baidu.com/s/zzz_fake_002', '1234', '2026-12-31 23:59:59+08'),
('3', 3, 'https://pan.baidu.com/s/zzz_fake_003', NULL, NULL),
('4', 12, 'https://pan.baidu.com/s/zzz_fake_004', '5678', '2026-06-01 00:00:00+08');