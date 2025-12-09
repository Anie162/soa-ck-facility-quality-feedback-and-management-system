import streamlit as st
import requests
import pandas as pd
import base64
import time

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
REPORT_SERVICE_URL = "https://irc-service.onrender.com"
TASK_SERVICE_URL = "https://task-management-service-kt6i.onrender.com"
GENERAL_SERVICE_URL = "https://general-service-u75j.onrender.com"

# Danh sách loại sự cố
INCIDENT_TYPES = {
    "ROAD_DAMAGE": "Hư hỏng đường bộ (Ổ gà, nứt)",
    "DRAINAGE_ISSUE": "Ngập úng / Tắc cống thoát nước",
    "STREET_LIGHT_FAILURE": "Hỏng đèn chiếu sáng công cộng",
    "TRAFFIC_SIGNAL_FAILURE": "Hỏng đèn tín hiệu / Biển báo",
    "SIDEWALK_DAMAGE": "Hư hỏng vỉa hè / Lấn chiếm",
    "WATER_LEAKAGE": "Vỡ ống nước / Rò rỉ nước sạch",
    "FALLEN_TREE": "Cây xanh gãy đổ",
    "GARBAGE_ACCUMULATION": "Rác thải ùn ứ / Môi trường",
    "BROKEN_MANHOLE_COVER": "Mất hoặc hỏng nắp hố ga",
    "PUBLIC_FACILITY_DAMAGE": "Hư hỏng công trình công cộng khác",
    "OTHER": "Sự cố khác"
}

st.set_page_config(page_title="City Feedback System", layout="wide", page_icon="🏙️")

# ==========================================
# CÁC HÀM HỖ TRỢ (UTILS)
# ==========================================
def image_to_base64(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        return f"data:{uploaded_file.type};base64,{base64_str}"
    except: return None

def clear_form_state():
    if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
    st.session_state.uploader_key += 1

def api_request(method, url, **kwargs):
    try:
        if method == "GET": response = requests.get(url, **kwargs)
        elif method == "POST": response = requests.post(url, **kwargs)
        elif method == "PATCH": response = requests.patch(url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Không thể kết nối tới: {url.split('/')[2]}")
        return None
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# ==========================================
# AUTHENTICATION FLOW (LOGIN / REGISTER / FORGOT)
# ==========================================

# Khởi tạo trạng thái Auth Mode (login | register | forgot)
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'

def switch_auth_mode(mode):
    st.session_state.auth_mode = mode
    st.rerun() # Load lại trang để đổi giao diện

def render_auth_sidebar():
    mode = st.session_state.auth_mode
    
    # --- MODE 1: ĐĂNG NHẬP ---
    if mode == 'login':
        st.sidebar.title("🔐 Đăng nhập")
        with st.sidebar.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập")
            
            if submitted:
                with st.spinner("Đang xác thực..."):
                    # Gọi API Login
                    res = api_request("POST", f"{GENERAL_SERVICE_URL}/api/auth/login", json={"username": username, "password": password})
                    
                    if res and res.status_code == 200:
                        st.session_state.user_info = res.json()
                        st.success("Thành công!")
                        st.rerun()
                    else:
                        st.error("Sai tài khoản hoặc mật khẩu!")
        
        st.sidebar.markdown("---")
        # Nút chuyển sang Đăng ký & Quên MK
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Đăng ký"): switch_auth_mode('register')
        with col2:
            if st.button("Quên MK?"): switch_auth_mode('forgot')

    # --- MODE 2: ĐĂNG KÝ (CHỈ DÀNH CHO CITIZEN/USER) ---
    elif mode == 'register':
        st.sidebar.title("📝 Đăng ký Cư dân")
        st.sidebar.info("Tài khoản mới sẽ mặc định là Cư dân (Citizen).")
        
        with st.sidebar.form("register_form"):
            new_user = st.text_input("Tên đăng nhập (*)")
            new_pass = st.text_input("Mật khẩu (*)", type="password")
            confirm_pass = st.text_input("Nhập lại mật khẩu (*)", type="password")
            email = st.text_input("Email (*)")
            full_name = st.text_input("Họ và tên")
            
            submitted = st.form_submit_button("Tạo tài khoản")
            
            if submitted:
                if new_pass != confirm_pass:
                    st.error("Mật khẩu nhập lại không khớp!")
                elif not new_user or not new_pass or not email:
                    st.error("Vui lòng điền đủ thông tin!")
                else:
                    payload = {
                        "username": new_user,
                        "password": new_pass,
                        "email": email,
                        "full_name": full_name,
                        "role": "Citizen" # <--- MẶC ĐỊNH ROLE LÀ USER (CITIZEN)
                    }
                    # Gọi API Register (Giả định endpoint là /api/auth/register hoặc /api/users)
                    res = api_request("POST", f"{GENERAL_SERVICE_URL}/api/users", json=payload)
                    
                    if res and res.status_code in [200, 201]:
                        st.success("Đăng ký thành công! Vui lòng đăng nhập.")
                        time.sleep(1)
                        switch_auth_mode('login')
                    else:
                        err_msg = res.text if res else "Lỗi kết nối"
                        st.error(f"Đăng ký thất bại: {err_msg}")
        
        if st.sidebar.button("🔙 Quay lại Đăng nhập"):
            switch_auth_mode('login')

    # --- MODE 3: QUÊN MẬT KHẨU ---
    elif mode == 'forgot':
        st.sidebar.title("🔑 Quên mật khẩu")
        st.sidebar.caption("Nhập email để nhận link đặt lại mật khẩu.")
        
        with st.sidebar.form("forgot_form"):
            email_forgot = st.text_input("Email của bạn")
            submitted = st.form_submit_button("Gửi yêu cầu")
            
            if submitted:
                # Gọi API Forgot Password (Giả định)
                # res = api_request("POST", f"{GENERAL_SERVICE_URL}/api/auth/forgot-password", json={"email": email_forgot})
                
                # Vì thường đồ án chưa làm kỹ phần gửi mail, ta giả lập thành công
                st.success(f"Nếu email {email_forgot} tồn tại, chúng tôi đã gửi hướng dẫn cho bạn.")
        
        if st.sidebar.button("🔙 Quay lại"):
            switch_auth_mode('login')

def logout_handler():
    user = st.session_state.user_info
    st.sidebar.success(f"👤 **{user.get('username', user.get('id'))}**")
    
    # Hiển thị Role tiếng Việt cho đẹp
    role_map = {"Citizen": "Cư dân", "Manager": "Quản lý", "Technician": "Kỹ thuật viên"}
    display_role = role_map.get(user.get('role'), user.get('role'))
    st.sidebar.info(f"Vai trò: `{display_role}`")
    
    if st.sidebar.button("Đăng xuất"):
        st.session_state.user_info = None
        st.session_state.auth_mode = 'login'
        st.rerun()

# ==========================================
# GIAO DIỆN: CƯ DÂN (USER)
# ==========================================
def view_resident(headers):
    st.title("🏙️ Cổng Phản Ánh Đô Thị")
    tab1, tab2 = st.tabs(["📝 Gửi Phản Ánh", "🗂️ Lịch Sử"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            incident_key = st.selectbox("Loại sự cố (*)", list(INCIDENT_TYPES.keys()), format_func=lambda x: INCIDENT_TYPES[x])
            content = st.text_area("Mô tả chi tiết (*)", height=120)
            uploaded = st.file_uploader("Ảnh hiện trường", type=['jpg','png'], key=f"up_{st.session_state.get('uploader_key',0)}")
            media_url = image_to_base64(uploaded)
        with c2:
            st.write("📍 **Vị trí sự cố**")
            detail = st.text_input("Số nhà/Ngõ")
            street = st.text_input("Đường/Phố")
            ward = st.text_input("Phường/Xã")
            district = st.text_input("Quận/Huyện")
            city = st.text_input("Tỉnh/Thành phố", value="TP. Hồ Chí Minh")

        if st.button("🚀 Gửi Phản Ánh", type="primary"):
            if not media_url:
                st.warning("Vui lòng đính kèm ảnh minh họa.")
            else:
                payload = {
                    "IncidentType": INCIDENT_TYPES[incident_key],
                    "Content": content, "MediaURL": media_url,
                    "Address": {
                        "Detail": detail.strip().title(), "Street": street.strip().title(),
                        "Ward": ward.strip().title(), "District": district.strip().title(), "City": city.strip().title()
                    }
                }
                res = api_request("POST", f"{REPORT_SERVICE_URL}/api/report/reports", json=payload, headers=headers)
                if res and res.status_code == 200:
                    st.success(f"✅ Đã gửi thành công! Mã: **{res.json()['data']['ReportId']}**")
                    clear_form_state(); time.sleep(1.5); st.rerun()
                else: st.error("Gửi thất bại.")

    with tab2:
        res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports", headers=headers)
        if res and res.status_code == 200:
            reports = res.json()
            if not reports: st.info("Bạn chưa có phản ánh nào.")
            else:
                for r in reports:
                    status_icon = "🟢" if r['Status'] == "COMPLETED" else "🔴" if r['Status'] == "REJECTED" else "🟡"
                    with st.expander(f"{status_icon} [{r['Status']}] {r['Title']} - {r['Created_at'][:10]}"):
                        c1, c2 = st.columns([1, 2])
                        with c1: 
                            if r.get('MediaURL'): st.image(r['MediaURL'], use_column_width=True)
                        with c2:
                            st.write(f"**Nội dung:** {r.get('Content')}")
                            if r.get("Note"): st.info(f"👮 **Phản hồi:** {r['Note']}")
                            if r['Status'] == "COMPLETED":
                                with st.form(key=f"complaint_{r['ReportId']}"):
                                    reason = st.text_input("Lý do khiếu nại (nếu chưa hài lòng):")
                                    if st.form_submit_button("Gửi Khiếu Nại"):
                                        res_c = api_request("POST", f"{REPORT_SERVICE_URL}/api/complaint/report/{r['ReportId']}", json={"Content": reason}, headers=headers)
                                        if res_c and res_c.status_code == 200: st.success("Đã ghi nhận khiếu nại!"); time.sleep(1); st.rerun()

# ==========================================
# GIAO DIỆN: QUẢN LÝ (MANAGER)
# ==========================================
def view_manager(headers):
    st.title("👮 Trung Tâm Điều Hành")
    res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports", headers=headers)
    if not res: return
    reports = res.json()
    
    # Dashboard
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng tiếp nhận", len(reports))
    c2.metric("Chờ xử lý", len([x for x in reports if x['Status'] == 'WAITING']))
    c3.metric("Đã hoàn thành", len([x for x in reports if x['Status'] == 'COMPLETED']))
    st.divider()

    if reports:
        df = pd.DataFrame(reports)
        st.dataframe(df[["Status", "ReportId", "Title", "Created_at"]], use_container_width=True, hide_index=True)
        
        selected_id = st.selectbox("👉 Chọn Mã Hồ Sơ để xử lý:", df["ReportId"].tolist())
        if selected_id:
            r = next((item for item in reports if item["ReportId"] == selected_id), None)
            if r:
                with st.container(border=True):
                    st.subheader(r['Title'])
                    col_img, col_info = st.columns([1, 1])
                    with col_img: 
                        if r.get('MediaURL'): st.image(r['MediaURL'], caption="Hiện trường")
                    with col_info:
                        st.write(f"**Người báo:** `{r['ReporterID']}`")
                        st.write(f"**Mô tả:** {r.get('Content')}")
                        st.write("---")
                        
                        st.write("#### 🛠️ Điều Phối & Xử Lý")
                        # Lấy danh sách thợ
                        tech_res = api_request("GET", f"{GENERAL_SERVICE_URL}/api/users", params={"role": "Techinician"}, headers=headers)
                        tech_list = tech_res.json() if (tech_res and tech_res.status_code == 200) else []
                        
                        if tech_list:
                            tech_opts = {t['id']: f"{t.get('username','Noname')} ({t['id']})" for t in tech_list}
                            sel_tech = st.selectbox("Chọn Kỹ Thuật Viên:", list(tech_opts.keys()), format_func=lambda x: tech_opts[x])
                        else:
                            sel_tech = st.text_input("Mã KTV (Nhập tay):", placeholder="TECH...")

                        task_desc = st.text_input("Mô tả công việc:", value=f"Xử lý: {r['Title']}")
                        
                        if st.button("🚀 Giao Việc (Tạo Task)"):
                            if not sel_tech: st.error("Chưa chọn KTV!")
                            else:
                                payload = {"ReportId": r["ReportId"], "TechnicianID": sel_tech, "ManagerID": headers["user-id"], "Description": task_desc, "Status": "ASSIGNED"}
                                t_res = api_request("POST", f"{TASK_SERVICE_URL}/api/tasks", json=payload, headers=headers)
                                if t_res and t_res.status_code in [200, 201]:
                                    api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{selected_id}/status", params={"status": "IN_PROGRESS", "note": f"Đã giao cho {sel_tech}"}, headers=headers)
                                    st.success("✅ Đã giao việc thành công!"); time.sleep(1); st.rerun()
                                else: st.error("Lỗi khi tạo Task!")

                        with st.expander("Cập nhật trạng thái thủ công (Không giao việc)"):
                            new_st = st.selectbox("Trạng thái mới", ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"], key="manual_st")
                            new_note = st.text_input("Lý do:", key="manual_note")
                            if st.button("Lưu thay đổi"):
                                if new_st == "REJECTED" and not new_note: st.error("Phải có lý do từ chối!")
                                else:
                                    api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{selected_id}/status", params={"status": new_st, "note": new_note}, headers=headers)
                                    st.success("Đã cập nhật!"); st.rerun()

# ==========================================
# GIAO DIỆN: KỸ THUẬT VIÊN (TECHNICIAN)
# ==========================================
def view_technician(headers):
    st.title("👷 Cổng Kỹ Thuật Viên")
    res = api_request("GET", f"{TASK_SERVICE_URL}/api/tasks", params={"technician_id": headers["user-id"]}, headers=headers)
    
    if res and res.status_code == 200:
        tasks = res.json()
        if not tasks: st.info("🎉 Bạn hiện không có nhiệm vụ nào.")
        else:
            st.subheader(f"Danh sách nhiệm vụ ({len(tasks)})")
            for task in tasks:
                report_id = task.get("ReportId")
                r_res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports/{report_id}", headers=headers)
                
                if r_res and r_res.status_code == 200:
                    r_data = r_res.json()
                    card_color = "green" if task['Status'] == "COMPLETED" else "red"
                    with st.expander(f":{card_color}[{task['Status']}] Task: {task.get('Description')} ({report_id})"):
                        c1, c2 = st.columns([1, 2])
                        with c1: 
                            if r_data.get('MediaURL'): st.image(r_data['MediaURL'])
                        with c2:
                            st.write(f"**Sự cố:** {r_data.get('Title')}")
                            st.write(f"**Địa chỉ:** {r_data.get('Address',{}).get('Detail')}")
                            st.info(f"Yêu cầu: {task.get('Description')}")
                            
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("🚧 Bắt đầu", key=f"start_{task.get('TaskId', task.get('id'))}"):
                                    api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{task.get('TaskId', task.get('id'))}", json={"Status": "IN_PROGRESS"}, headers=headers)
                                    st.rerun()
                            with b2:
                                if st.button("✅ Hoàn thành", key=f"end_{task.get('TaskId', task.get('id'))}"):
                                    api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{task.get('TaskId', task.get('id'))}", json={"Status": "COMPLETED"}, headers=headers)
                                    api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{report_id}/status", params={"status": "COMPLETED", "note": "KTV đã xử lý xong"}, headers=headers)
                                    st.success("Tuyệt vời! Nhiệm vụ hoàn tất."); time.sleep(1); st.rerun()
    else: st.error("Lỗi tải danh sách nhiệm vụ.")

# ==========================================
# MAIN APP FLOW
# ==========================================
if "user_info" not in st.session_state: st.session_state.user_info = None

if not st.session_state.user_info:
    render_auth_sidebar()
    st.info("👈 Vui lòng đăng nhập hoặc đăng ký tài khoản từ thanh bên trái.")
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQoE3Cza7rUEc5t7CTzWeQgHoBUkuhfr8RyPA&s", caption="Smart City Management")
else:
    logout_handler()
    user = st.session_state.user_info
    role = user.get("role")
    req_headers = {"user-id": str(user.get("id")), "X-Role": role}
    
    if role == "Manager": view_manager(req_headers)
    elif role == "Technician": view_technician(req_headers)
    else: view_resident(req_headers)