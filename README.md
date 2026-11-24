# 云继颜免费邀请注册推广管理网站（MVP）

## 功能
- 推广员只能通过有效邀请链接注册。
- 注册后记录邀请来源，供总部追踪渠道；**邀请本身不产生佣金**。
- 推广员只能查看和登记自己的直接销售订单。
- 总部管理员可审核订单、查看推广员和佣金汇总。
- 佣金只按本人直接成交订单计算。

## 免费部署架构
- Streamlit Community Cloud：免费托管（以平台当前免费额度/规则为准）。
- Supabase Free：认证与数据库（以平台当前免费额度/规则为准）。
- 不需要先购买域名；部署后使用平台分配的网址。

## 第一步：创建 Supabase 免费项目
1. 打开 https://supabase.com/ 注册并创建项目。
2. 进入 SQL Editor，运行本压缩包中的 `supabase_schema.sql`。
3. 进入 Project Settings -> API，复制：
   - Project URL
   - anon/public key
   - service_role key（仅服务端使用，绝不可公开）

## 第二步：建立管理员
1. 在 Supabase -> Authentication -> Users 中手动添加管理员邮箱和密码。
2. 复制该用户的 UUID。
3. 在 SQL Editor 执行（把 UUID 和名称替换为实际值）：

```sql
insert into public.profiles (id, display_name, role)
values ('替换为管理员UUID', '云继颜总部', 'admin');
```

4. 首次登录后确认管理员资料已建立。

## 第三步：上传 GitHub
1. 创建 GitHub 账号和一个新仓库，建议设为 Private。
2. 上传 `app.py`、`requirements.txt`。
3. 不要上传任何密钥或真实客户资料。

## 第四步：部署 Streamlit
1. 打开 https://share.streamlit.io/ 并授权 GitHub。
2. 选择刚才的仓库和 `app.py`，点击 Deploy。
3. 在 Streamlit 应用设置的 Secrets 中填入：

```toml
SUPABASE_URL = "你的 Project URL"
SUPABASE_ANON_KEY = "你的 anon/public key"
SUPABASE_SERVICE_ROLE_KEY = "你的 service_role key"
```

4. 保存后应用会重新启动。使用管理员邮箱密码登录。

## 第五步：添加第一批推广员并发邀请链接
当前 MVP 的推广员账号由管理员在 Supabase Authentication -> Users 中创建后，再在 SQL Editor 添加 profiles 记录：

```sql
insert into public.profiles (id, display_name, role)
values ('推广员Auth用户UUID', '推广员A', 'member');
```

然后管理员登录网站，在“邀请链接管理”选择该推广员，生成邀请码。把网站地址加上 `?invite=邀请码` 发给新人，例如：
`https://你的应用.streamlit.app/?invite=ABC123XYZ`

新人通过该链接进入“邀请注册”页，填写邮箱和密码。若 Supabase 开启邮箱验证，新人需先验证邮箱后登录。

## 重要说明
- 当前为可部署的最小可用版本，不是已代用户创建或部署的在线网站。
- Streamlit/Supabase 免费套餐可能有休眠、资源和使用限制；请查看服务商当期条款。
- 邀请关系只用于追踪邀请来源，不构成多级计酬。无拉人头奖、无下线抽成、无入门费。
- 佣金页面仅统计已审核的直接销售佣金。实际付款仍需总部线下核对并记录。
- 这是早期 MVP，未实现自动佣金打款、微信支付、短信验证、完整退款冲正和细粒度 RLS。上线收集真实个人信息或接入真实资金前，必须完成安全、隐私、税务和法律审查。
