import streamlit as st
from supabase import create_client
from datetime import datetime
import secrets, string

st.set_page_config(page_title="云继颜推广管理中心", page_icon="💎", layout="wide")
st.markdown("""<style>
.stApp{background:#f5f7fb}.block-container{max-width:1050px;padding-top:2rem}
.brand{background:#202c42;color:white;padding:22px 26px;border-radius:16px;margin-bottom:18px}
.brand h1{color:white;margin:0;font-size:28px}.brand p{color:#d8dfeb;margin:6px 0 0}
div[data-testid="stMetric"]{background:white;border:1px solid #e8ecf2;padding:14px;border-radius:12px}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="brand"><h1>💎 云继颜推广管理中心</h1><p>邀请注册 · 真实订单 · 直接销售佣金</p></div>', unsafe_allow_html=True)

try:
    url=st.secrets["SUPABASE_URL"].strip()
    anon=st.secrets.get("SUPABASE_ANON_KEY", "").strip()
    service=st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip()
    auth_client=create_client(url, anon or service)
    db=create_client(url, service)
except Exception:
    st.error("Supabase 配置不完整。请在 Streamlit → App settings → Secrets 设置 SUPABASE_URL、SUPABASE_ANON_KEY（可选）和 SUPABASE_SERVICE_ROLE_KEY。")
    st.stop()

APP_URL=st.secrets.get("APP_URL", "https://yunjiyan-promo.streamlit.app").strip().rstrip("/")

def profile(uid):
    r=db.table("profiles").select("*").eq("id",uid).limit(1).execute()
    return r.data[0] if r.data else None

def admin_exists():
    r=db.table("profiles").select("id").eq("role","admin").limit(1).execute()
    return bool(r.data)

def bootstrap_done():
    r=db.table("app_settings").select("value").eq("key","admin_initialized").limit(1).execute()
    return bool(r.data and r.data[0].get("value")=="true")

def money(v): return f"¥{float(v or 0):,.2f}"
def make_code(n=10):
    chars=string.ascii_uppercase+string.digits
    return ''.join(secrets.choice(chars) for _ in range(n))
def logout():
    for k in ("user","profile","new_invite"): st.session_state.pop(k,None)
    st.rerun()

# First administrator bootstrap: gated by a secret stored only in Streamlit Secrets,
# and permanently disabled after the first successful initialization.
if not admin_exists() and not bootstrap_done():
    st.subheader("首次初始化：创建总部管理员")
    st.warning("这是一次性初始化入口。创建第一个管理员后，此入口将自动关闭。不要把初始化口令告诉推广员。")
    setup_secret=st.secrets.get("ADMIN_SETUP_TOKEN", "")
    if not setup_secret:
        st.error("尚未设置 ADMIN_SETUP_TOKEN。请先在 Streamlit → App settings → Secrets 中添加一个仅你自己知道的初始化口令。")
        st.code('ADMIN_SETUP_TOKEN = "请替换成一段你自己设置的长随机口令"', language="toml")
        st.stop()
    with st.form("first_admin"):
        token=st.text_input("一次性初始化口令",type="password")
        display=st.text_input("管理员姓名或昵称")
        email=st.text_input("管理员邮箱")
        password=st.text_input("登录密码（至少12位）",type="password")
        password2=st.text_input("再次输入密码",type="password")
        submit=st.form_submit_button("创建唯一总部管理员",use_container_width=True)
    if submit:
        if not secrets.compare_digest(token,setup_secret): st.error("初始化口令不正确。")
        elif not display.strip() or not email.strip() or len(password)<12 or password!=password2: st.error("请填写完整信息，密码至少12位且两次一致。")
        elif admin_exists() or bootstrap_done(): st.error("管理员已初始化，请返回登录。")
        else:
            try:
                result=auth_client.auth.sign_up({"email":email.strip(),"password":password})
                if not result.user: st.error("管理员账号创建失败，请检查邮箱或稍后重试。")
                else:
                    db.table("profiles").insert({"id":result.user.id,"display_name":display.strip(),"role":"admin","invited_by":None}).execute()
                    db.table("app_settings").upsert({"key":"admin_initialized","value":"true"}).execute()
                    st.success("总部管理员创建成功！如果 Supabase 开启邮箱验证，请先验证邮箱，再使用邮箱和密码登录。")
                    st.info("请立即从 Streamlit Secrets 删除 ADMIN_SETUP_TOKEN，然后刷新应用。")
            except Exception as e:
                st.error("创建失败。请确认邮箱未注册、app_settings 表已创建，并查看 Streamlit 日志。")
    st.stop()

if "user" not in st.session_state:
    login_tab,reg_tab=st.tabs(["登录","邀请注册"])
    with login_tab:
        with st.form("login"):
            email=st.text_input("邮箱")
            password=st.text_input("密码",type="password")
            ok=st.form_submit_button("登录",use_container_width=True)
        if ok:
            try:
                result=auth_client.auth.sign_in_with_password({"email":email.strip(),"password":password})
                p=profile(result.user.id)
                if not p: st.error("账号资料未建立，请联系总部管理员。")
                else: st.session_state.user=result.user; st.session_state.profile=p; st.rerun()
            except Exception: st.error("登录失败，请检查邮箱、密码或邮箱验证状态。")
    with reg_tab:
        invite_code=st.query_params.get("invite","").strip().upper()
        if not invite_code: st.info("请使用推广员发给你的专属邀请链接注册。没有邀请链接暂时无法注册。")
        else:
            inv=db.table("invites").select("*").eq("code",invite_code).eq("active",True).limit(1).execute()
            if not inv.data: st.error("邀请链接无效或已停用，请联系邀请人重新获取。")
            else:
                inviter_id=inv.data[0]["owner_id"]
                inviter=profile(inviter_id)
                if not inviter or inviter.get("role") not in ("admin","member"):
                    st.error("邀请人账号状态异常，请联系总部。")
                else:
                    st.caption(f"邀请人：{inviter.get('display_name','推广员')}。邀请关系仅记录来源，不产生招募佣金。")
                    with st.form("register"):
                        display=st.text_input("姓名或昵称")
                        email=st.text_input("邮箱")
                        password=st.text_input("设置密码（至少12位）",type="password")
                        password2=st.text_input("再次输入密码",type="password")
                        submit=st.form_submit_button("提交注册",use_container_width=True)
                    if submit:
                        if not display.strip() or not email.strip() or len(password)<12 or password!=password2: st.error("请填写完整信息，密码至少12位且两次一致。")
                        else:
                            try:
                                result=auth_client.auth.sign_up({"email":email.strip(),"password":password})
                                if not result.user: st.error("注册未完成，请稍后重试。")
                                else:
                                    db.table("profiles").insert({"id":result.user.id,"display_name":display.strip(),"role":"member","invited_by":inviter_id}).execute()
                                    db.table("invites").update({"uses":int(inv.data[0].get("uses",0))+1}).eq("code",invite_code).execute()
                                    st.success("注册成功！如邮箱验证已开启，请先完成邮箱验证，再返回登录。")
                            except Exception: st.error("注册失败。该邮箱可能已注册，或数据库配置尚未完成。")
    st.stop()

user=st.session_state.user
p=st.session_state.get("profile") or profile(user.id)
if not p: st.error("账号资料缺失，请联系总部管理员。"); st.stop()
st.session_state.profile=p
is_admin=p["role"]=="admin"
with st.sidebar:
    st.write(f"**{p.get('display_name','用户')}**")
    st.caption("总部管理员" if is_admin else "推广员")
    pages=["经营总览","订单管理","佣金汇总","推广员管理","邀请链接管理"] if is_admin else ["经营总览","订单管理","我的佣金","邀请链接管理"]
    page=st.radio("功能导航",pages)
    st.button("退出登录",on_click=logout,use_container_width=True)

if page=="经营总览":
    if is_admin:
        orders=db.table("orders").select("*").execute().data or []
        members=db.table("profiles").select("id").eq("role","member").execute().data or []
        cols=st.columns(4); cols[0].metric("推广员人数",len(members)); cols[1].metric("订单笔数",len(orders)); cols[2].metric("订单金额",money(sum(float(x["sale_amount"]) for x in orders))); cols[3].metric("已确认佣金",money(sum(float(x["commission"]) for x in orders if x["status"]=="approved")))
    else:
        mine=db.table("orders").select("*").eq("member_id",user.id).execute().data or []
        cols=st.columns(3); cols[0].metric("我的订单",len(mine)); cols[1].metric("成交金额",money(sum(float(x["sale_amount"]) for x in mine))); cols[2].metric("已确认佣金",money(sum(float(x["commission"]) for x in mine if x["status"]=="approved")))
    st.info("佣金只按本人直接成交且经总部核实的真实订单计算。邀请注册仅记录来源，不产生招募佣金或下线抽成。")
elif page=="订单管理":
    st.subheader("登记本人直接成交订单")
    with st.form("new_order"):
        customer=st.text_input("客户称呼或内部编号（不要填写身份证等敏感信息）"); product=st.text_input("商品名称")
        a,b=st.columns(2); sale=a.number_input("成交金额（元）",min_value=0.01,value=69.9,step=1.0); cost=b.number_input("商品及履约成本（元）",min_value=0.0,value=49.9,step=1.0)
        rate=st.slider("直接销售佣金比例",0,50,30,5); submit=st.form_submit_button("提交总部审核",use_container_width=True)
    if submit:
        if not customer.strip() or not product.strip() or cost>sale: st.error("请检查客户、商品和成本金额。")
        else:
            commission=round((sale-cost)*rate/100,2)
            db.table("orders").insert({"member_id":user.id,"customer_ref":customer.strip(),"product":product.strip(),"sale_amount":sale,"cost_amount":cost,"commission_rate":rate/100,"commission":commission,"status":"pending"}).execute(); st.success("订单已提交，等待总部核实。"); st.rerun()
    q=db.table("orders").select("*").order("created_at",desc=True)
    if not is_admin: q=q.eq("member_id",user.id)
    rows=q.execute().data or []; st.subheader("订单记录")
    for o in rows:
        with st.container(border=True):
            a,b,c=st.columns([3,2,2]); a.write(f"**{o['product']}**"); a.caption(f"{o.get('customer_ref','')} · {o.get('created_at','')[:10]}"); b.write(f"成交：{money(o['sale_amount'])}"); c.write(f"佣金：{money(o['commission'])}")
            st.caption({"pending":"待审核","approved":"已确认","rejected":"已驳回"}.get(o["status"],o["status"]))
            if is_admin and o["status"]=="pending":
                x,y=st.columns(2)
                if x.button("确认订单",key=f"ok{o['id']}"): db.table("orders").update({"status":"approved"}).eq("id",o["id"]).execute(); st.rerun()
                if y.button("驳回订单",key=f"no{o['id']}"): db.table("orders").update({"status":"rejected","commission":0}).eq("id",o["id"]).execute(); st.rerun()
elif page in ("我的佣金","佣金汇总"):
    rows=db.table("orders").select("*").execute().data or []
    if not is_admin: rows=[o for o in rows if o["member_id"]==user.id]
    approved=[o for o in rows if o["status"]=="approved"]
    st.metric("已确认佣金",money(sum(float(o["commission"]) for o in approved))); st.metric("待审核订单数",sum(1 for o in rows if o["status"]=="pending"))
    if is_admin:
        members=db.table("profiles").select("*").eq("role","member").execute().data or []
        for m in members:
            mine=[o for o in approved if o["member_id"]==m["id"]]; st.write(f"**{m['display_name']}** · {len(mine)}笔已确认订单 · {money(sum(float(o['commission']) for o in mine))}")
elif page=="推广员管理":
    st.subheader("推广员管理")
    members=db.table("profiles").select("*").eq("role","member").order("created_at",desc=True).execute().data or []
    for m in members: st.write(f"**{m['display_name']}** · {m['id'][:8]} · 邀请来源：{(m.get('invited_by') or '未记录')[:8]}")
elif page=="邀请链接管理":
    st.subheader("生成推广员邀请链接")
    if is_admin:
        owners=db.table("profiles").select("*").in_("role",["admin","member"]).order("created_at").execute().data or []
        labels={f"{m['display_name']}（{'总部' if m['role']=='admin' else '推广员'} · {m['id'][:8]}）":m["id"] for m in owners}
        if labels: selected=st.selectbox("选择邀请人",list(labels.keys())); owner_id=labels[selected]
        else: owner_id=None
    else: owner_id=user.id; st.caption("此邀请链接归属于你的直接销售账号。")
    if owner_id and st.button("生成邀请链接"):
        code=make_code(); db.table("invites").insert({"code":code,"owner_id":owner_id,"active":True,"uses":0}).execute(); st.session_state["new_invite"]=code
    if st.session_state.get("new_invite"):
        link=f"{APP_URL}/?invite={st.session_state['new_invite']}"; st.code(link); st.caption("复制此链接发送给新推广员。邀请仅记录来源，不产生招募佣金。")
    existing=db.table("invites").select("*").eq("owner_id",user.id).order("created_at",desc=True).execute().data or []
    if existing:
        st.subheader("我创建的邀请链接")
        for x in existing: st.write(f"{APP_URL}/?invite={x['code']} · 使用次数：{x['uses']} · {'启用' if x['active'] else '停用'}")
st.divider(); st.caption("云继颜推广管理中心。佣金仅按本人直接成交且核实的订单计算，不按招募人数或下线团队计酬。上线前请完成权限、隐私及业务合规审查。")
