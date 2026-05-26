-- 数据库结构补齐迁移：2026-05-26
-- 修复 ad_config 缺失字段 + 创建 marquee_config/system_config/mine_sections 表

-- 1. ad_config 补充字段（若表已存在但缺字段）
ALTER TABLE ad_config ADD COLUMN IF NOT EXISTS test_unit_id VARCHAR(200);
ALTER TABLE ad_config ADD COLUMN IF NOT EXISTS ab_test_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE ad_config ADD COLUMN IF NOT EXISTS ab_test_ratio FLOAT DEFAULT 0.5;
ALTER TABLE ad_config ADD COLUMN IF NOT EXISTS description TEXT;

-- 2. 创建跑马灯配置表
CREATE TABLE IF NOT EXISTS marquee_config (
    id          BIGSERIAL    NOT NULL,
    enabled     BOOLEAN      NOT NULL DEFAULT FALSE,
    content     TEXT         NOT NULL DEFAULT '',
    link_url    VARCHAR(500)          DEFAULT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
COMMENT ON TABLE marquee_config IS '跑马灯配置表 - 小程序首页跑马灯文字和链接';

-- 3. 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id          BIGSERIAL    NOT NULL,
    config_key  VARCHAR(100) NOT NULL,
    config_value TEXT        NOT NULL DEFAULT '',
    description VARCHAR(200)          DEFAULT NULL,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_system_config_key ON system_config (config_key);
COMMENT ON TABLE system_config IS '系统配置表 - 全局系统级配置 (key-value)';

-- 4. 创建Mine页板块配置表
CREATE TABLE IF NOT EXISTS mine_sections (
    id          BIGSERIAL    NOT NULL,
    section_key VARCHAR(50)  NOT NULL,
    title       VARCHAR(100) NOT NULL DEFAULT '',
    enabled     BOOLEAN      NOT NULL DEFAULT TRUE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    description VARCHAR(200)          DEFAULT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mine_sections_key ON mine_sections (section_key);
CREATE INDEX IF NOT EXISTS idx_mine_sections_sort ON mine_sections (sort_order);
COMMENT ON TABLE mine_sections IS 'Mine页板块配置表 - 各板块标题和开关';