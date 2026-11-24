import streamlit as st
from supabase import create_client
from datetime import datetime, timezone
import secrets, string

st.set_page_config(page_title="云继颜推广管理中心", page_icon="💎", layout="wide")

st.markdown("""
<style>
.stApp {background:#f5f7fb}
.block-container {max-width:1050px;padding-top:2rem}
.brand {background:#202c42;color:white;padding:22px 26px;border-radius:16px;margin-bottom:18px}
.brand h1 {color:white;margin:0;font-size:28px}
.brand p {color:#d8dfeb;margin:6px 0 0}
div[data-testid="stMetric"] {background:white;border:1px solid #e8ecf2;padding:14px;border-radius:12px}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand"><h1>💎 云继颜推广管理中心</h1><p>邀请注册 · 真实订单 · 直接销售佣金</p></div>', unsafe_allow_html=True)

def clients():
    url=st.secrets["SUPABASE_URL"]
    anon=st.secrets["SUPABASE_ANON_KEY"]
    service=st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, anon), create_client(url, service)

try:
    auth_client, db = clients()
except Exception:
    st.error("尚未完成 Supabase 配置。请先按压缩包 README 设置 Streamlit Secrets。")
    st.stop()

def get_profile(uid):
    r=db.table("profiles").select("*").eq("id",uid).limit(1).execute()
    return r.data[0] if r.data else None

def money(v):
    return f"¥{float(v or 0):,.2f}"

def logout():
    for k in ["user","profile"]:
        st.session_state.pop(k,None)
    st.rerun()

def make_code(n=10):
    chars=string.ascii_uppercase+string.digits
    return ''.join(secrets.choice(chars) for _ in range(n))

if "user" not in st.session_state:
    login_tab, reg_tab = st.tabs(["登录", "邀请注册"])
    with login_tab:
        with st.form("login"):
            email=st.text_input("邮箱")
            password=st.text_input("密码",type="password")
            ok=st.form_submit_button("登录",use_container_width=True)
        if ok:
            try:
                result=auth_client.auth.sign_in_with_password({"email":email.strip(),"password":password})
                st.session_state.user=result.user
                st.session_state.profile=get_profile(result.user.id)
                if not st.session_state.profile:
                    st.error("账号资料未建立，请联系总部管理员。")
                    st.session_state.pop("user",None)
                else:
                    st.rerun()
            except Exception:
                st.error("登录失败，请检查邮箱和密码。")
    with reg_tab:
        invite_code=st.query_params.get("invite","").strip().upper()
        if not invite_code:
            st.info("请使用推广员发给你的专属邀请链接注册。没有邀请链接暂时无法注册。")
        else:
            inv=db.table("invites").select("*").eq("code",invite_code).eq("active",True).limit(1).execute()
            if not inv.data:
                st.error("邀请链接无效或已停用，请联系邀请人重新获取。")
            else:
                inviter_id=inv.data[0]["owner_id"]
                inviter=get_profile(inviter_id)
                if not inviter or inviter.get("role")!="member":
                    st.error("邀请人账号状态异常，请联系总部。")
                else:
                    st.caption(f"邀请人：{inviter.get('display_name','推广员')}。注册后将记录邀请来源，但不会产生拉人头佣金。")
                    with st.form("register"):
                        display=st.text_input("姓名或昵称")
                        email=st.text_input("邮箱")
                        password=st.text_input("设置密码（至少10位）",type="password")
                        password2=st.text_input("再次输入密码",type="password")
                        submit=st.form_submit_button("提交注册申请",use_container_width=True)
                    if submit:
                        if not display.strip() or not email.strip() or len(password)<10 or password!=password2:
                            st.error("请填写完整信息，密码至少10位且两次一致。")
                        else:
                            try:
                                result=auth_client.auth.sign_up({"email":email.strip(),"password":password})
                                if not result.user:
                                    st.error("注册未完成，请稍后重试。")
                                else:
                                    db.table("profiles").insert({"id":result.user.id,"display_name":display.strip(),"role":"member","invited_by":inviter_id}).execute()
                                    db.table("invites").update({"uses":int(inv[0].get("uses",0))+1}).eq("code",invite_code).execute()
                                    st.success("注册成功！如邮箱验证已开启，请先完成邮箱验证，再返回登录。")
                            except Exception:
                                st.error("注册失败。该邮箱可能已注册，或数据库配置尚未完成。")
    st.stop()

user=st.session_state.user
profile=st.session_state.get("profile") or get_profile(user.id)
if not profile:
    st.error("账号资料缺失，请联系总部管理员。")
    st.stop()
st.session_state.profile=profile
is_admin=profile["role"]=="admin"

with st.sidebar:
    st.write(f"**{profile.get('display_name','用户')}**")
    st.caption("总部管理员" if is_admin else "推广员")
    page=st.radio("功能导航",["经营总览","订单管理","我的佣金","邀请推广员"] if not is_admin else ["经营总览","订单管理","佣金汇总","推广员管理","邀请链接管理"])
    st.button("退出登录",on_click=logout,use_container_width=True)

if page=="经营总览":
    if is_admin:
        all_orders=db.table("orders").select("*").execute().data or []
        members=db.table("profiles").select("id").eq("role","member").execute().data or []
        total_sales=sum(float(x["sale_amount"]) for x in all_orders)
        approved=sum(float(x["commission"]) for x in all_orders if x["status"]=="approved")
        pending=sum(1 for x in all_orders if x["status"]=="pending")
        c1,c2,c3,c4=st.columns(4)
        c1.metric("推广员人数",len(members)); c2.metric("订单笔数",len(all_orders)); c3.metric("订单金额",money(total_sales)); c4.metric("已确认佣金",money(approved))
    else:
        mine=db.table("orders").select("*").eq("member_id",user.id).execute().data or []
        c1,c2,c3=st.columns(3)
        c1.metric("我的订单",len(mine))
        c2.metric("成交金额",money(sum(float(x["sale_amount"]) for x in mine)))
        c3.metric("已确认佣金",money(sum(float(x["commission"]) for x in mine if x["status"]=="approved")))
    st.info("佣金只按本人直接成交且经总部核实的真实订单计算。邀请注册只记录来源，不产生招募佣金或下线抽成。")

elif page=="订单管理":
    st.subheader("登记本人直接成交订单")
    with st.form("new_order"):
        customer=st.text_input("客户称呼或内部编号（不要填写身份证等敏感信息）")
        product=st.text_input("商品名称")
        c1,c2=st.columns(2)
        sale=c1.number_input("成交金额（元）",min_value=0.01,value=69.9,step=1.0)
        cost=c2.number_input("商品及履约成本（元）",min_value=0.0,value=49.9,step=1.0)
        rate=st.slider("直接销售佣金比例",0,50,30,5)
        submit=st.form_submit_button("提交总部审核",use_container_width=True)
    if submit:
        if not customer.strip() or not product.strip() or cost>sale:
            st.error("请检查客户、商品和成本金额。")
        else:
            commission=round((sale-cost)*rate/100,2)
            db.table("orders").insert({"member_id":user.id,"customer_ref":customer.strip(),"product":product.strip(),"sale_amount":sale,"cost_amount":cost,"commission_rate":rate/100,"commission":commission,"status":"pending"}).execute()
            st.success("订单已提交，等待总部核实付款、发货及退款状态。")
    q=db.table("orders").select("*").order("created_at",desc=True)
    if not is_admin: q=q.eq("member_id",user.id)
    rows=q.execute().data or []
    st.subheader("订单记录")
    if rows:
        for o in rows:
            with st.container(border=True):
                a,b,c=st.columns([3,2,2])
                a.write(f"**{o['product']}**")
                a.caption(f"{o.get('customer_ref','')} · {o.get('created_at','')[:10]}")
                b.write(f"成交：{money(o['sale_amount'])}")
                c.write(f"佣金：{money(o['commission'])}")
                st.caption({"pending":"待审核","approved":"已确认","rejected":"已驳回"}.get(o["status"],o["status"]))
                if is_admin and o["status"]=="pending":
                    x,y=st.columns(2)
                    if x.button("确认订单",key=f"ok{o['id']}"):
                        db.table("orders").update({"status":"approved"}).eq("id",o["id"]).execute(); st.rerun()
                    if y.button("驳回订单",key=f"no{o['id']}"):
                        db.table("orders").update({"status":"rejected","commission":0}).eq("id",o["id"]).execute(); st.rerun()
    else: st.caption("暂无订单。")

elif page in ["我的佣金","佣金汇总"]:
    st.subheader("佣金统计")
    q=db.table("orders").select("*")
    if not is_admin: q=q.eq("member_id",user.id)
    rows=q.execute().data or []
    approved=[o for o in rows if o["status"]=="approved"]
    st.metric("已确认佣金",money(sum(float(o["commission"]) for o in approved)))
    st.metric("待审核订单数",sum(1 for o in rows if o["status"]=="pending"))
    if is_admin:
        profiles=db.table("profiles").select("*").eq("role","member").execute().data or []
        for p in profiles:
            po=[o for o in approved if o["member_id"]==p["id"]]
            st.write(f"**{p['display_name']}** · {len(po)}笔已确认订单 · {money(sum(float(o['commission']) for o in po))}")

elif page=="推广员管理":
    st.subheader("推广员管理")
    members=db.table("profiles").select("*").eq("role","member").order("created_at",desc=True).execute().data or []
    for m in members:
        st.write(f"**{m['display_name']}** · {m['id'][:8]} · 邀请来源：{(m.get('invited_by') or '直接/未记录')[:8]}")

elif page=="邀请链接管理":
    st.subheader("生成推广员邀请链接")
    members=db.table("profiles").select("*").eq("role","member").order("created_at",desc=True).execute().data or []
    if members:
        labels={f"{m['display_name']}（{m['id'][:8]}）":m["id"] for m in members}
        selected=st.selectbox("选择邀请人",list(labels.keys()))
        if st.button("生成邀请链接"):
            code=make_code()
            db.table("invites").insert({"code":code,"owner_id":labels[selected],"active":True,"uses":0}).execute()
            st.session_state["new_invite"]=code
        if st.session_state.get("new_invite"):
            link=f"{st.context.url if hasattr(st.context,'url') else ''}?invite={st.session_state['new_invite']}"
            st.code(link if link.strip("?") else f"网站域名/?invite={st.session_state['new_invite']}")
            st.caption("部署后将网站域名与邀请码组合发送给新人。")
    else:
        st.info("目前还没有推广员账号。管理员需先在 Supabase 中创建推广员资料。")

st.divider()
st.caption("云继颜 MVP：邀请关系仅用于来源追踪，不因招募人数、下线层级或团队人头计酬。上线前请完成隐私、安全和业务合规审查。")
