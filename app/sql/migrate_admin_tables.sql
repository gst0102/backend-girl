-- ===========================================
-- 迁移：Admin 管理后台相关表
-- ===========================================

CREATE TABLE IF NOT EXISTS banners (
    id          BIGSERIAL    NOT NULL,
    title       VARCHAR(200) NOT NULL,
    image_url   VARCHAR(500) NOT NULL,
    link_url    VARCHAR(500),
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    status      VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS kdocs_sources (
    id               BIGSERIAL    NOT NULL,
    name             VARCHAR(100) NOT NULL,
    url              VARCHAR(500) NOT NULL,
    type             VARCHAR(50)  NOT NULL,
    enabled          BOOLEAN      NOT NULL DEFAULT TRUE,
    last_sync_at     TIMESTAMPTZ,
    last_sync_result VARCHAR(200),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS kdocs_rules (
    id               BIGSERIAL    NOT NULL,
    cron_expression  VARCHAR(100) NOT NULL DEFAULT '0 2,14 * * *',
    enabled          BOOLEAN      NOT NULL DEFAULT TRUE,
    last_run_at      TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS mine_apps (
    id          BIGSERIAL    NOT NULL,
    name        VARCHAR(100) NOT NULL,
    app_id      VARCHAR(100) NOT NULL,
    path        VARCHAR(200),
    icon        VARCHAR(200),
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    enabled     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_mine_apps_sort ON mine_apps (sort_order);

CREATE TABLE IF NOT EXISTS reserve_config (
    id          BIGSERIAL    NOT NULL,
    config_type VARCHAR(50)  NOT NULL,
    config_data TEXT         NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_reserve_config_type ON reserve_config (config_type);

CREATE TABLE IF NOT EXISTS ad_stats (
    id                BIGSERIAL    NOT NULL,
    position          VARCHAR(50)  NOT NULL,
    user_id           UUID,
    action            VARCHAR(20)  NOT NULL,
    estimated_revenue REAL         NOT NULL DEFAULT 0,
    stats_date        VARCHAR(10)  NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_ad_stats_pos_date ON ad_stats (position, stats_date);
CREATE INDEX IF NOT EXISTS idx_ad_stats_user ON ad_stats (user_id);

-- 插入默认数据
INSERT INTO kdocs_rules (cron_expression, enabled) SELECT '0 2,14 * * *', TRUE WHERE NOT EXISTS (SELECT 1 FROM kdocs_rules);

INSERT INTO reserve_config (config_type, config_data) SELECT 'official_account', '{"enabled":false,"name":"","qrcode_url":""}' WHERE NOT EXISTS (SELECT 1 FROM reserve_config WHERE config_type='official_account');