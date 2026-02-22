import streamlit as st
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import COMMON_CSS, find_user, get_admin_credentials, find_stall, render_pin_dots, register_user, esc

st.set_page_config(page_title="Digital Vault", page_icon="🔐", layout="centered", initial_sidebar_state="collapsed")
st.markdown(COMMON_CSS, unsafe_allow_html=True)

for k, v in {"role": None, "current_user": None, "current_stall": None, "current_admin": None}.items():
    if k not in st.session_state: st.session_state[k] = v

if st.session_state.role == "user":          st.switch_page("pages/User.py")
elif st.session_state.role == "stall_owner": st.switch_page("pages/Stall_Owner.py")
elif st.session_state.role == "admin":       st.switch_page("pages/Admin.py")

st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1.5rem 0;">
  <div style="width:76px;height:76px;background:linear-gradient(135deg,#4f46e5,#7c3aed);border-radius:24px;
       display:inline-flex;align-items:center;justify-content:center;font-size:2.2rem;margin-bottom:0.85rem;
       box-shadow:0 8px 40px rgba(79,70,229,0.45);">🔐</div>
  <div style="font-size:1.9rem;font-weight:900;color:#e2e8f0;letter-spacing:-0.03em;">Digital
    <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);-webkit-background-clip:text;
          -webkit-text-fill-color:transparent;background-clip:text;">Vault</span>
  </div>
  <div style="font-size:0.78rem;color:#475569;margin-top:0.35rem;font-weight:700;letter-spacing:0.06em;">
    CHOOSE YOUR ROLE TO CONTINUE
  </div>
</div>
""", unsafe_allow_html=True)

tab_user, tab_stall, tab_admin = st.tabs(["👤 User", "🧑‍🍳 Stall Owner", "🛠️ Admin"])

# ── USER LOGIN ─────────────────────────────────────────────────────────────────
with tab_user:
    st.markdown("<br>", unsafe_allow_html=True)
    u_user = st.text_input("Username", key="u_user", placeholder="Enter your username")
    u_pin  = st.text_input("4-Digit PIN", key="u_pin", placeholder="••••", max_chars=4, type="password")
    render_pin_dots(min(len([c for c in (u_pin or "") if c.isdigit()]), 4))
    st.markdown('<p class="hint">Enter your 4-digit numeric PIN</p>', unsafe_allow_html=True)

    if st.button("Sign In →", key="btn_user"):
        pin = re.sub(r"\D", "", u_pin or "")
        if not u_user:     st.warning("Please enter your username.")
        elif len(pin) != 4: st.warning("PIN must be exactly 4 digits.")
        else:
            with st.spinner("Verifying..."):
                try:
                    user = find_user(u_user)
                    if not user:
                        st.error("❌ No account found.")
                    elif str(user.get("Pin", "")).upper() == "BLOCKED":
                        st.error("❌ This account is blocked. Contact admin.")
                    elif str(user.get("Pin", "")) != pin:
                        st.error("❌ Incorrect PIN.")
                    else:
                        st.session_state.role = "user"
                        st.session_state.current_user = user
                        st.switch_page("pages/User.py")
                except FileNotFoundError: st.error("❌ Excel file not found in assets/ folder.")
                except Exception as e:    st.error(f"Error: {esc(str(e))}")

    st.markdown('<hr style="border:none;border-top:1px solid #1e2130;margin:1.2rem 0;">', unsafe_allow_html=True)
    with st.expander("📝 New here? Create an account"):
        r_user = st.text_input("Username",    key="r_user", placeholder="Choose a username")
        r_pin  = st.text_input("Create PIN",  key="r_pin",  placeholder="••••", max_chars=4, type="password")
        render_pin_dots(min(len([c for c in (r_pin or "") if c.isdigit()]), 4))
        r_conf = st.text_input("Confirm PIN", key="r_conf", placeholder="••••", max_chars=4, type="password")
        render_pin_dots(min(len([c for c in (r_conf or "") if c.isdigit()]), 4))
        if st.button("Create Account →", key="btn_reg"):
            pc = re.sub(r"\D", "", r_pin or "")
            pf = re.sub(r"\D", "", r_conf or "")
            if not r_user:                                  st.warning("Enter a username.")
            elif len(r_user) < 3:                           st.error("❌ Username must be at least 3 characters.")
            elif not re.match(r"^[a-zA-Z0-9_]+$", r_user): st.error("❌ Letters, numbers & underscores only.")
            elif len(pc) != 4:                              st.error("❌ PIN must be 4 digits.")
            elif pc != pf:                                  st.error("❌ PINs do not match.")
            else:
                with st.spinner("Creating account..."):
                    new, err = register_user(r_user, pc)
                    if err:  st.error(f"❌ {esc(err)}")
                    else:    st.success(f"✅ Account created! UID: **{esc(new['UID'])}**")

# ── STALL OWNER LOGIN ──────────────────────────────────────────────────────────
with tab_stall:
    st.markdown("<br>", unsafe_allow_html=True)
    s_id   = st.text_input("Stall ID",   key="s_id",   placeholder="e.g. S101")
    s_name = st.text_input("Stall Name", key="s_name", placeholder="e.g. Tasty Bites")
    s_pin  = st.text_input("Stall PIN",  key="s_pin",  placeholder="••••", max_chars=4, type="password")
    render_pin_dots(min(len([c for c in (s_pin or "") if c.isdigit()]), 4))
    st.markdown('<p class="hint">All three fields must match your stall record</p>', unsafe_allow_html=True)

    if st.button("Sign In →", key="btn_stall"):
        pin = re.sub(r"\D", "", s_pin or "")
        if not s_id or not s_name: st.warning("Please enter Stall ID and Stall Name.")
        elif len(pin) != 4:        st.warning("PIN must be exactly 4 digits.")
        else:
            with st.spinner("Verifying..."):
                try:
                    stall = find_stall(s_id, s_name, pin)
                    if not stall: st.error("❌ No stall found. Check ID, Name, and PIN.")
                    else:
                        st.session_state.role = "stall_owner"
                        st.session_state.current_stall = stall
                        st.switch_page("pages/Stall_Owner.py")
                except FileNotFoundError: st.error("❌ Excel file not found in assets/ folder.")
                except Exception as e:    st.error(f"Error: {esc(str(e))}")

# ── ADMIN LOGIN ────────────────────────────────────────────────────────────────
with tab_admin:
    st.markdown("<br>", unsafe_allow_html=True)
    a_user = st.text_input("Admin Username", key="a_user", placeholder="Enter admin username")
    a_pass = st.text_input("Password",       key="a_pass", placeholder="Enter password", type="password")

    if st.button("Sign In →", key="btn_admin"):
        if not a_user or not a_pass: st.warning("Please enter both username and password.")
        else:
            with st.spinner("Verifying..."):
                try:
                    au, ap = get_admin_credentials()
                    if a_user.strip() == au and a_pass.strip() == ap:
                        st.session_state.role = "admin"
                        st.session_state.current_admin = {"username": au}
                        st.switch_page("pages/Admin.py")
                    else: st.error("❌ Invalid admin credentials.")
                except FileNotFoundError: st.error("❌ Excel file not found in assets/ folder.")
                except Exception as e:    st.error(f"Error: {esc(str(e))}")
