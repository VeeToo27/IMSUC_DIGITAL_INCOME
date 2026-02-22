import streamlit as st
import sys, os, re, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (COMMON_CSS, get_live_balance, save_token_and_deduct,
                   get_tokens_for_user, load_stalls, render_pin_dots, top_bar, esc, stat_card)

st.set_page_config(page_title="Vault — User", page_icon="🛒", layout="centered", initial_sidebar_state="collapsed")
st.markdown(COMMON_CSS, unsafe_allow_html=True)

if st.session_state.get("role") != "user":
    st.switch_page("app.py")

for k, v in {"u_page": "home", "selected_stall": None, "cart": {}, "last_token": None}.items():
    if k not in st.session_state: st.session_state[k] = v

username     = st.session_state.current_user.get("Username", "")
uid          = st.session_state.current_user.get("UID", "N/A")
live_balance = get_live_balance(username)

top_bar("Logged in as User", username, uid, balance=live_balance)

# ══════════════════════════════════════════════════════════════════════════════
# TOKEN RESULT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.u_page == "token" and st.session_state.last_token:
    t = st.session_state.last_token
    items_html = "".join([
        f'<div style="font-size:0.85rem;opacity:0.9;padding:2px 0;">'
        f'{esc(v["qty"])}× {esc(k)} — ₹{int(v["price"]*v["qty"])}</div>'
        for k, v in t["items"].items()
    ])
    st.markdown(f"""
    <div class="token-card">
      <div style="font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:0.12em;opacity:0.8;">🎉 Order Confirmed!</div>
      <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;opacity:0.65;margin-top:1rem;letter-spacing:0.1em;">Token Number</div>
      <div class="token-num">#{esc(t['token'])}</div>
      <div style="font-size:1rem;font-weight:800;margin-top:0.75rem;">
        📍 {esc(t['stall_name'])}
        <span style="opacity:0.6;font-size:0.75rem;"> ({esc(t['stall_id'])})</span>
      </div>
      <div style="margin-top:0.6rem;line-height:1.7;">{items_html}</div>
      <div style="font-family:'Space Mono',monospace;font-size:1.25rem;font-weight:700;
           margin-top:1rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.2);">
        Total Paid: ₹{t['total']:.2f}
      </div>
      <div style="font-size:0.65rem;opacity:0.55;margin-top:0.4rem;">{esc(t['time'])}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🛍️ Order More"):
            st.session_state.u_page = "stalls"; st.session_state.cart = {}; st.session_state.last_token = None; st.rerun()
    with c2:
        if st.button("🏠 Home"):
            st.session_state.u_page = "home"; st.session_state.cart = {}; st.session_state.last_token = None; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.u_page == "home":
    try:    bal_str = f"₹{live_balance:,.2f}"
    except: bal_str = f"₹{live_balance}"

    st.markdown('<div class="section-title">What would you like to do?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏪 Browse Stalls"):
            st.session_state.u_page = "stalls"; st.session_state.cart = {}; st.rerun()
    with c2:
        if st.button("🎟️ My Tokens"):
            st.session_state.u_page = "my_tokens"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="info-row"><span class="info-label">Username</span><span class="info-value">{esc(username)}</span></div>
    <div class="info-row"><span class="info-label">UID</span><span class="info-value">{esc(uid)}</span></div>
    <div class="info-row"><span class="info-label">Balance</span><span class="info-value">{esc(bal_str)}</span></div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔓 Sign Out"):
        for k in ["role","current_user","u_page","selected_stall","cart","last_token"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")
    time.sleep(5)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MY TOKENS  — auto-refreshes every 8s
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.u_page == "my_tokens":
    if st.button("← Back"):
        st.session_state.u_page = "home"; st.rerun()
    st.markdown('<div class="section-title">🎟️ My Order History</div>', unsafe_allow_html=True)

    tokens = get_tokens_for_user(username)

    if tokens:
        pending_n   = len([t for t in tokens if str(t.get("Status","")).strip() != "Served"])
        total_spent = sum(float(t.get("Total",0) or 0) for t in tokens)
        c1, c2, c3 = st.columns(3)
        with c1: stat_card(len(tokens), "Orders",  "#818cf8")
        with c2: stat_card(pending_n,   "Pending", "#f59e0b")
        with c3: stat_card(f"₹{total_spent:.0f}", "Spent", "#34d399")

        now_str = datetime.now().strftime("%I:%M:%S %p")
        st.markdown(f'<p class="hint">🔄 Updated {now_str} · refreshes every 8s</p>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        for t in reversed(tokens):
            status    = str(t.get("Status","Pending")).strip()
            is_served = status == "Served"
            badge     = '<span class="green-badge">✅ Served</span>' if is_served else '<span class="orange-badge">⏳ Pending</span>'
            border    = "#059669" if is_served else "#f59e0b"
            st.markdown(f"""
            <div class="card" style="border-left-color:{border};">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div style="font-size:1.5rem;font-weight:900;color:#818cf8;font-family:'Space Mono',monospace;">
                    #{esc(t.get('Token_No',''))}
                  </div>
                  <div style="font-size:0.88rem;font-weight:800;color:#e2e8f0;margin-top:3px;">
                    {esc(t.get('Stall_Name',''))}
                    <span style="font-size:0.68rem;color:#475569;"> ({esc(t.get('Stall_ID',''))})</span>
                  </div>
                  <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">{esc(t.get('Items',''))}</div>
                  <div style="font-size:0.68rem;color:#475569;margin-top:3px;">🕐 {esc(t.get('Time',''))}</div>
                </div>
                <div style="text-align:right;flex-shrink:0;margin-left:8px;">
                  {badge}
                  <div style="font-family:'Space Mono',monospace;font-size:0.9rem;font-weight:700;
                       color:#e2e8f0;margin-top:6px;">₹{esc(t.get('Total','0'))}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("You haven't placed any orders yet.")

    time.sleep(8)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STALLS LIST
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.u_page == "stalls":
    if st.button("← Back"):
        st.session_state.u_page = "home"; st.rerun()
    st.markdown('<div class="section-title">🏪 Stalls</div>', unsafe_allow_html=True)
    search = st.text_input("Search by name or ID", placeholder="e.g. Tasty Bites or S101", key="stall_search")

    try:    stalls = load_stalls()
    except FileNotFoundError: st.error("❌ Excel file not found."); stalls = []
    except Exception as e:    st.error(f"Error: {esc(str(e))}"); stalls = []

    filtered = [s for s in stalls if not search.strip() or
                search.strip().lower() in s["name"].lower() or
                search.strip().lower() in s["id"].lower()]

    if not filtered:
        st.info("No stalls found.")
    else:
        for s in filtered:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""
                <div class="stall-card">
                  <div>
                    <div style="font-size:0.98rem;font-weight:800;color:#e2e8f0;">{esc(s['name'])}</div>
                    <div style="font-size:0.7rem;font-family:'Space Mono',monospace;color:#475569;margin-top:2px;">
                      {esc(s['id'])} · {len(s['menu'])} items
                    </div>
                  </div>
                  <div style="font-size:1.1rem;color:#818cf8;">›</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                if st.button("View", key=f"s_{s['id']}"):
                    st.session_state.selected_stall = s
                    st.session_state.u_page = "stall_detail"
                    st.session_state.cart = {}
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STALL DETAIL + CART
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.u_page == "stall_detail":
    stall = st.session_state.selected_stall
    if not stall: st.session_state.u_page = "stalls"; st.rerun()

    cb, cc = st.columns([3, 1])
    with cb:
        if st.button("← Back to Stalls"):
            st.session_state.u_page = "stalls"; st.session_state.cart = {}; st.rerun()
    with cc:
        if st.button("🗑️ Clear"):
            st.session_state.cart = {}; st.rerun()

    st.markdown(
        f'<div class="section-title">🍽️ {esc(stall["name"])} '
        f'<span style="font-size:0.7rem;color:#475569;font-family:monospace;">{esc(stall["id"])}</span></div>',
        unsafe_allow_html=True
    )

    cart = st.session_state.cart
    for item in stall["menu"]:
        iname  = item["item"]
        iprice = item["price"]
        qty    = cart.get(iname, {}).get("qty", 0)
        cn, cp, cminus, cqty, cplus = st.columns([3, 1.5, 0.8, 0.6, 0.8])
        with cn:
            st.markdown(
                f'<div style="font-size:0.92rem;font-weight:800;color:#e2e8f0;padding:10px 0;">{esc(iname)}</div>',
                unsafe_allow_html=True
            )
        with cp:
            st.markdown(
                f'<div style="font-family:\'Space Mono\',monospace;font-size:0.88rem;font-weight:700;color:#818cf8;padding:10px 0;">₹{iprice:.0f}</div>',
                unsafe_allow_html=True
            )
        with cminus:
            if st.button("−", key=f"m_{iname}"):
                if qty == 1:   cart.pop(iname, None)
                elif qty > 1:  cart[iname]["qty"] -= 1
                st.session_state.cart = cart; st.rerun()
        with cqty:
            st.markdown(
                f'<div style="text-align:center;font-weight:900;color:#e2e8f0;padding:10px 0;">{qty}</div>',
                unsafe_allow_html=True
            )
        with cplus:
            if st.button("＋", key=f"p_{iname}"):
                if iname in cart: cart[iname]["qty"] += 1
                else:             cart[iname] = {"price": iprice, "qty": 1}
                st.session_state.cart = cart; st.rerun()

    if cart:
        total     = sum(v["price"] * v["qty"] for v in cart.values())
        cart_rows = "".join([
            f'<div class="cart-row"><span>{esc(v["qty"])}× {esc(k)}</span><span>₹{int(v["price"]*v["qty"])}</span></div>'
            for k, v in cart.items()
        ])
        st.markdown(f"""
        <div class="cart-bar">
          <div class="cart-title">🛒 Your Cart</div>
          {cart_rows}
          <div class="cart-total"><span>Total</span><span>₹{total:.2f}</span></div>
        </div>""", unsafe_allow_html=True)

        fresh_bal = get_live_balance(username)
        if fresh_bal < total:
            st.error(f"❌ Insufficient balance. You have ₹{fresh_bal:.2f} but need ₹{total:.2f}")
        else:
            st.markdown('<p class="hint" style="margin-bottom:0.4rem;">Confirm with your PIN to pay</p>', unsafe_allow_html=True)
            cpay = st.text_input("PIN", key="cpay", placeholder="••••", max_chars=4, type="password", label_visibility="collapsed")
            render_pin_dots(min(len([c for c in (cpay or "") if c.isdigit()]), 4))

            if st.button(f"💳 Pay ₹{total:.2f}", key="btn_pay"):
                pin_clean = re.sub(r"\D", "", cpay or "")
                if len(pin_clean) != 4:
                    st.warning("Enter your 4-digit PIN.")
                elif pin_clean != str(st.session_state.current_user.get("Pin", "")):
                    st.error("❌ Wrong PIN.")
                else:
                    with st.spinner("Processing..."):
                        token_no, result = save_token_and_deduct(
                            username, stall["id"], stall["name"], cart, total
                        )
                        if token_no is None:
                            st.error(f"❌ Insufficient balance: ₹{result:.2f}")
                        else:
                            st.session_state.last_token = {
                                "token":      token_no,
                                "stall_id":   stall["id"],
                                "stall_name": stall["name"],
                                "items":      dict(cart),
                                "total":      total,
                                "time":       datetime.now().strftime("%d %b %Y, %I:%M %p"),
                            }
                            st.session_state.u_page = "token"
                            st.session_state.cart = {}
                            st.rerun()
    else:
        st.markdown('<p class="hint">Tap ＋ to add items to your cart</p>', unsafe_allow_html=True)
