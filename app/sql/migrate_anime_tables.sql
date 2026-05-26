-- ===========================================
-- 迁移脚本：更新 anime 表结构，添加新字段
-- ===========================================

-- 1. 先删除旧的 anime_drive_resources 表（已不再需要）
DROP TABLE IF EXISTS anime_drive_resources;

-- 2. 添加新字段到 animes 表
ALTER TABLE animes
    DROP COLUMN IF EXISTS name;

ALTER TABLE animes
    DROP COLUMN IF EXISTS cover;

ALTER TABLE animes
    DROP COLUMN IF EXISTS update_day;

ALTER TABLE animes
    DROP COLUMN IF EXISTS description;

ALTER TABLE animes
    DROP COLUMN IF EXISTS latest_episode;

ALTER TABLE animes
    DROP COLUMN IF EXISTS status;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS title VARCHAR(200) NOT NULL DEFAULT '';

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS quality VARCHAR(50) DEFAULT NULL;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS episode VARCHAR(50) DEFAULT NULL;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT NULL;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS baidu_url VARCHAR(500) DEFAULT NULL;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS baidu_password VARCHAR(50) DEFAULT NULL;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS quark_url VARCHAR(500) DEFAULT NULL;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS update_time VARCHAR(10) DEFAULT NULL;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS type VARCHAR(20) NOT NULL DEFAULT 'anime';

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE animes
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- ===========================================
-- 创建 anime_reminders 表
-- ===========================================
CREATE TABLE IF NOT EXISTS anime_reminders (
    id              BIGSERIAL    NOT NULL,
    user_id         UUID        NOT NULL,
    anime_id        VARCHAR(20) NOT NULL,
    is_reminded     BOOLEAN     NOT NULL DEFAULT FALSE,
    reminded_at     TIMESTAMPTZ   DEFAULT NULL,
    current_episode VARCHAR(50)   DEFAULT NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_anime_reminders_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_anime_reminders_anime FOREIGN KEY (anime_id) REFERENCES animes (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_anime_reminders_unique ON anime_reminders (user_id, anime_id);
CREATE INDEX IF NOT EXISTS idx_anime_reminders_user ON anime_reminders (user_id);

COMMENT ON TABLE anime_reminders IS '催更记录表';
