# verify_db.py
import asyncpg
import asyncio

async def verify():
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="w12345",
        database="record_db"
    )
    
    # 查询所有表
    tables = await conn.fetch("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    
    print("=== 已创建的表 ===")
    for t in tables:
        print(f"  ✅ {t['tablename']}")
    
    expected_tables = [
        'users', 'invite_relations', 'records', 'user_features',
        'badges', 'user_badges', 'guardian_relations', 'couple_relations',
        'families', 'family_members', 'push_logs', 'reward_logs',
        'config_unlock', 'config_push_templates'
    ]
    
    existing = [t['tablename'] for t in tables]
    missing = [t for t in expected_tables if t not in existing]
    
    if missing:
        print(f"\n❌ 缺失的表：{missing}")
    else:
        print("\n✅ 所有 14 张表都已创建成功！")
    
    await conn.close()

asyncio.run(verify())