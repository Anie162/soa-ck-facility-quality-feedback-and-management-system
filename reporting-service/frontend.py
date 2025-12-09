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
    """Hàm wrapper để gọi API an toàn"""
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "PATCH":
            response = requests.patch(url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Không thể kết nối tới: {url.split('/')[2]}")
        return None
    except Exception as e:
        st.error(f"Lỗi không xác định: {e}")
        return None

# ==========================================
# AUTHENTICATION
# ==========================================
def login_handler():
    st.sidebar.title("🔐 Đăng nhập")
    
    with st.sidebar.form("login_form"):
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")
        
        if submitted:
            with st.spinner("Đang xác thực..."):
                # Gọi API Login của General Service
                res = api_request("POST", f"{GENERAL_SERVICE_URL}/api/auth/login", json={"username": username, "password": password})
                
                if res and res.status_code == 200:
                    user_data = res.json()
                    # Chuẩn hóa dữ liệu user trả về (đề phòng backend trả khác)
                    # Giả định backend trả: { "id": "...", "role": "...", "access_token": "..." }
                    st.session_state.user_info = user_data
                    st.success("Đăng nhập thành công!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu!")
                    
                    # --- CHẾ ĐỘ DEBUG (XÓA KHI CHẠY THẬT NẾU MUỐN) ---
                    if username.startswith("test"):
                        st.warning("⚠️ Đang dùng chế độ Test User (Offline)")
                        mock_role = "MANAGER" if "admin" in username else "TECHNICIAN" if "tech" in username else "USER"
                        st.session_state.user_info = {"id": username, "role": mock_role, "name": f"Test {mock_role}"}
                        st.rerun()
                    # ------------------------------------------------

def logout_handler():
    user = st.session_state.user_info
    st.sidebar.success(f"👤 **{user.get('username', user.get('id'))}**")
    st.sidebar.caption(f"Role: {user.get('role')}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.user_info = None
        st.rerun()

# ==========================================
# GIAO DIỆN: CƯ DÂN (USER)
# ==========================================
def view_resident(headers):
    st.title("🏙️ Cổng Phản Ánh Đô Thị")
    tab1, tab2 = st.tabs(["📝 Gửi Phản Ánh", "🗂️ Lịch Sử"])

    # TAB 1: FORM
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
                st.warning("Vui lòng đính kèm ảnh minh họa để chúng tôi xử lý nhanh hơn.")
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
                    st.success(f"✅ Đã gửi thành công! Mã hồ sơ: **{res.json()['data']['ReportId']}**")
                    clear_form_state()
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Gửi thất bại. Vui lòng thử lại.")

    # TAB 2: HISTORY
    with tab2:
        res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports", headers=headers)
        if res and res.status_code == 200:
            reports = res.json()
            if not reports: st.info("Bạn chưa có phản ánh nào.")
            else:
                for r in reports:
                    status_map = {"WAITING": "🟡 Đang chờ", "IN_PROGRESS": "🔵 Đang xử lý", "COMPLETED": "🟢 Đã xong", "REJECTED": "🔴 Từ chối"}
                    s_label = status_map.get(r['Status'], r['Status'])
                    
                    with st.expander(f"{s_label} - {r['Title']} ({r['Created_at'][:10]})"):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            if r.get('MediaURL'): st.image(r['MediaURL'], use_column_width=True)
                        with c2:
                            st.write(f"**Nội dung:** {r.get('Content')}")
                            addr = r.get('Address', {})
                            st.caption(f"📍 {addr.get('Detail','')}, {addr.get('Street','')}, {addr.get('District','')}")
                            
                            if r.get("Note"): st.info(f"👮 **Phản hồi:** {r['Note']}")
                            
                            # Khiếu nại
                            if r['Status'] == "COMPLETED":
                                with st.form(key=f"complaint_{r['ReportId']}"):
                                    reason = st.text_input("Lý do khiếu nại (nếu chưa hài lòng):")
                                    if st.form_submit_button("Gửi Khiếu Nại"):
                                        res_c = api_request("POST", f"{REPORT_SERVICE_URL}/api/complaint/report/{r['ReportId']}", json={"Content": reason}, headers=headers)
                                        if res_c and res_c.status_code == 200:
                                            st.success("Đã ghi nhận khiếu nại!")
                                            time.sleep(1)
                                            st.rerun()

# ==========================================
# GIAO DIỆN: QUẢN LÝ (MANAGER)
# ==========================================
def view_manager(headers):
    st.title("👮 Trung Tâm Điều Hành")
    
    # Load Data
    res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports", headers=headers)
    if not res or res.status_code != 200:
        st.error("Không thể tải dữ liệu báo cáo.")
        return
    
    reports = res.json()
    
    # KPI Dashboard
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng tiếp nhận", len(reports))
    c2.metric("Chờ xử lý", len([x for x in reports if x['Status'] == 'WAITING']))
    c3.metric("Đã hoàn thành", len([x for x in reports if x['Status'] == 'COMPLETED']))
    st.divider()

    # Main Workflow
    if reports:
        df = pd.DataFrame(reports)
        # Show table
        st.dataframe(
            df[["Status", "ReportId", "Title", "Created_at"]],
            use_container_width=True,
            hide_index=True
        )
        
        # Detail View
        selected_id = st.selectbox("👉 Chọn Mã Hồ Sơ để xử lý:", df["ReportId"].tolist())
        if selected_id:
            r = next((item for item in reports if item["ReportId"] == selected_id), None)
            if r:
                with st.container(border=True):
                    st.subheader(r['Title'])
                    col_img, col_info = st.columns([1, 1])
                    
                    with col_img:
                        if r.get('MediaURL'): st.image(r['MediaURL'], caption="Ảnh hiện trường")
                    
                    with col_info:
                        st.write(f"**Người báo:** `{r['ReporterID']}`")
                        addr = r.get('Address', {})
                        st.write(f"**Địa chỉ:** {addr.get('Detail','')}, {addr.get('District','')}, {addr.get('City','')}")
                        st.write(f"**Mô tả:** {r.get('Content')}")
                        st.write("---")
                        
                        # --- TASK ASSIGNMENT ---
                        st.write("#### 🛠️ Điều Phối & Xử Lý")
                        
                        # Lấy danh sách thợ từ General Service
                        tech_res = api_request("GET", f"{GENERAL_SERVICE_URL}/api/users", params={"role": "TECHNICIAN"})
                        tech_list = tech_res.json() if (tech_res and tech_res.status_code == 200) else []
                        
                        if tech_list:
                            tech_opts = {t['id']: f"{t.get('username','Noname')} ({t['id']})" for t in tech_list}
                            sel_tech = st.selectbox("Chọn Kỹ Thuật Viên:", list(tech_opts.keys()), format_func=lambda x: tech_opts[x])
                        else:
                            sel_tech = st.text_input("Mã KTV (Nhập tay do lỗi API User):", placeholder="TECH...")

                        task_note = st.text_input("Ghi chú giao việc:", value=f"Xử lý: {r['Title']}")
                        
                        if st.button("🚀 Giao Việc (Tạo Task)"):
                            if not sel_tech: st.error("Chưa chọn KTV!")
                            else:
                                payload = {
                                    "ReportId": r["ReportId"],
                                    "TechnicianID": sel_tech,
                                    "ManagerID": headers["user-id"],
                                    "Description": task_note,
                                    "Status": "ASSIGNED"
                                }
                                # 1. Tạo Task
                                t_res = api_request("POST", f"{TASK_SERVICE_URL}/api/tasks", json=payload, headers=headers)
                                if t_res and t_res.status_code in [200, 201]:
                                    # 2. Update Report Status
                                    api_request(
                                        "PATCH", 
                                        f"{REPORT_SERVICE_URL}/api/report/reports/{selected_id}/status", 
                                        params={"status": "IN_PROGRESS", "note": f"Đã giao cho {sel_tech}"}, 
                                        headers=headers
                                    )
                                    st.success("✅ Đã giao việc thành công!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Lỗi khi tạo Task!")

                        # --- MANUAL UPDATE ---
                        with st.expander("Cập nhật trạng thái thủ công (Không giao việc)"):
                            new_st = st.selectbox("Trạng thái mới", ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"], key="manual_st")
                            new_note = st.text_input("Lý do:", key="manual_note")
                            if st.button("Lưu thay đổi"):
                                if new_st == "REJECTED" and not new_note:
                                    st.error("Phải có lý do từ chối!")
                                else:
                                    api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{selected_id}/status", params={"status": new_st, "note": new_note}, headers=headers)
                                    st.success("Đã cập nhật!")
                                    st.rerun()

# ==========================================
# GIAO DIỆN: KỸ THUẬT VIÊN (TECHNICIAN)
# ==========================================
def view_technician(headers):
    st.title("👷 Cổng Kỹ Thuật Viên")
    user_id = headers["user-id"]
    
    # Lấy Task của tôi
    res = api_request("GET", f"{TASK_SERVICE_URL}/api/tasks", params={"technician_id": user_id}, headers=headers)
    
    if res and res.status_code == 200:
        tasks = res.json()
        if not tasks:
            st.info("🎉 Bạn hiện không có nhiệm vụ nào.")
        else:
            st.subheader(f"Danh sách nhiệm vụ ({len(tasks)})")
            for task in tasks:
                report_id = task.get("ReportId")
                # Lấy chi tiết báo cáo để hiển thị kèm
                r_res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports/{report_id}", headers=headers)
                
                if r_res and r_res.status_code == 200:
                    r_data = r_res.json()
                    
                    # Card
                    card_color = "green" if task['Status'] == "COMPLETED" else "red"
                    with st.expander(f":{card_color}[{task['Status']}] Task: {task.get('Description')} ({report_id})"):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            if r_data.get('MediaURL'): st.image(r_data['MediaURL'])
                        with c2:
                            st.write(f"**Địa chỉ:** {r_data['Address'].get('Detail')}, {r_data['Address'].get('District')}")
                            st.write(f"**Sự cố:** {r_data.get('Title')}")
                            st.info(f"Yêu cầu từ Manager: {task.get('Description')}")
                            
                            st.write("#### Cập nhật tiến độ:")
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("🚧 Bắt đầu làm", key=f"start_{task.get('TaskId', task.get('id'))}"):
                                    api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{task.get('TaskId', task.get('id'))}", json={"Status": "IN_PROGRESS"}, headers=headers)
                                    st.rerun()
                            with b2:
                                if st.button("✅ Hoàn thành", key=f"end_{task.get('TaskId', task.get('id'))}"):
                                    # 1. Close Task
                                    api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{task.get('TaskId', task.get('id'))}", json={"Status": "COMPLETED"}, headers=headers)
                                    # 2. Close Report
                                    api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{report_id}/status", params={"status": "COMPLETED", "note": "KTV đã xử lý xong"}, headers=headers)
                                    st.success("Tuyệt vời! Nhiệm vụ hoàn tất.")
                                    time.sleep(1)
                                    st.rerun()
                else:
                    st.warning(f"Task ID {task.get('TaskId')} bị lỗi dữ liệu báo cáo.")
    else:
        st.error("Không thể tải danh sách nhiệm vụ.")

# ==========================================
# MAIN APP FLOW
# ==========================================
if "user_info" not in st.session_state:
    st.session_state.user_info = None

if not st.session_state.user_info:
    login_handler()
    st.info("👈 Vui lòng đăng nhập từ thanh bên trái để tiếp tục.")
else:
    logout_handler()
    
    # Phân quyền điều hướng
    user = st.session_state.user_info
    role = user.get("role")
    
    # Tạo header chuẩn để gọi API
    req_headers = {
        "user-id": str(user.get("id")),
        "X-Role": role
    }
    
    if role == "MANAGER":
        view_manager(req_headers)
    elif role == "TECHNICIAN":
        view_technician(req_headers)
    else:
        view_resident(req_headers)