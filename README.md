# 云继颜推广管理中心（首次管理员初始化修复版）

## 本版本修复
- 新增首次管理员初始化入口：只有设置了 `ADMIN_SETUP_TOKEN` 且数据库尚无管理员时才显示。
- 第一个管理员创建成功后，数据库写入 `admin_initialized=true`，初始化入口永久关闭。
- 修复邀请码使用次数读取错误（使用 `inv.data[0]`）。
- 邀请链接使用明确的 `APP_URL`，不再依赖 Streamlit 不稳定的上下文 URL。
- 管理员可以为自己或推广员生成邀请链接；推广员只能生成归属于自己的邀请链接。
- 允许总部管理员作为第一条邀请链的邀请人；邀请不产生招募佣金。

## 更新 GitHub
将本压缩包中的 `app.py`、`admin_init_migration.sql`、`README.md` 上传并覆盖/新增到 GitHub 仓库根目录。保留原来的 `requirements.txt` 和 `supabase_schema.sql`。

## 数据库迁移
在 Supabase → SQL Editor 新建查询，粘贴并运行 `admin_init_migration.sql`。

## Streamlit Secrets
在 App settings → Secrets 中保留已有 Supabase 配置，并追加：

```toml
APP_URL = "https://yunjiyan-promo.streamlit.app"
ADMIN_SETUP_TOKEN = "请自己生成一段至少32位的随机口令"
```

示例随机口令可在 Mac 终端运行 `openssl rand -hex 32` 生成。不要把口令或 Supabase service_role/secret key 上传到 GitHub、发给推广员或发到聊天中。

## 创建管理员
更新部署并执行数据库迁移后，打开网站。首次初始化页面会要求一次性口令、管理员昵称、邮箱和至少12位密码。创建成功后：
1. 如 Supabase 开启邮箱验证，先到邮箱完成验证。
2. 回到 Streamlit Secrets，删除 `ADMIN_SETUP_TOKEN` 这一行并保存。
3. 使用刚才设置的管理员邮箱和密码登录。
4. 在「邀请链接管理」中选择总部管理员，生成第一条推广员邀请链接。

注意：此应用目前由 Streamlit 服务端使用 Supabase service_role key 访问数据库。该密钥权限很高。正式使用前必须进行 RLS、权限边界、隐私及安全审查；当前版本适合小范围测试，不应存放敏感个人信息。
