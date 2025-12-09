import streamlit as st
import requests
import pandas as pd
import base64
import time
from datetime import datetime, timedelta

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
    "OTHER": "Sự cố khác (Nhập chi tiết)"
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

def reset_form():
    if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
    st.session_state.uploader_key += 1
    # Reset các biến session state cho input
    st.session_state["content_input"] = ""
    st.session_state["other_incident_input"] = ""
    st.session_state["detail_input"] = ""
    st.session_state["street_input"] = ""
    st.session_state["ward_input"] = ""
    st.session_state["district_input"] = ""
    st.session_state["city_input"] = "TP. Hồ Chí Minh"

def api_request(method, url, **kwargs):
    try:
        if method == "GET": response = requests.get(url, **kwargs)
        elif method == "POST": response = requests.post(url, **kwargs)
        elif method == "PATCH": response = requests.patch(url, **kwargs)
        elif method == "PUT": response = requests.put(url, **kwargs)
        elif method == "DELETE": response = requests.delete(url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Không thể kết nối tới: {url.split('/')[2]}")
        return None
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- MEDIA SERVICE UPLOAD ---
def upload_file_to_media_service(uploaded_file):
    """Upload file lên Media Service và trả về URL"""
    if not uploaded_file: return None
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        res = requests.post(f"{GENERAL_SERVICE_URL}/api/media/upload", files=files)
        if res.status_code in [200, 201]:
            return res.json().get("url") or res.json().get("secure_url") 
        else:
            st.error(f"Upload thất bại: {res.text}")
            return None
    except Exception as e:
        st.error(f"Lỗi upload: {e}")
        return None

# ==========================================
# AUTHENTICATION FLOW
# ==========================================
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = 'login'
if 'temp_reg_data' not in st.session_state: st.session_state.temp_reg_data = {}

def switch_auth_mode(mode):
    st.session_state.auth_mode = mode
    st.rerun()

def render_auth_sidebar():
    mode = st.session_state.auth_mode
    if mode == 'login':
        st.sidebar.title("🔐 Đăng nhập")
        with st.sidebar.form("login_form"):
            email_input = st.text_input("Email")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập")
            if submitted:
                with st.spinner("Đang xác thực..."):
                    res = api_request("POST", f"{GENERAL_SERVICE_URL}/api/users/login", json={"email": email_input, "password": password})
                    if res and res.status_code == 200:
                        user_data = res.json()
                        st.session_state.user_info = user_data if "role" in user_data else user_data.get("user", {})
                        st.success("Thành công!")
                        st.rerun()
                    else: st.error("Đăng nhập thất bại!")
        st.sidebar.markdown("---")
        c1, c2 = st.sidebar.columns(2)
        with c1: 
            if st.button("Đăng ký"): switch_auth_mode('register')
        with c2: 
            if st.button("Quên MK?"): switch_auth_mode('forgot')

    elif mode == 'register':
        st.sidebar.title("📝 Đăng ký Cư dân")
        with st.sidebar.form("register_form"):
            name = st.text_input("Họ và tên (*)")
            email = st.text_input("Email (*)")
            phone = st.text_input("Số điện thoại (*)")
            password = st.text_input("Mật khẩu (*)", type="password")
            confirm_pass = st.text_input("Nhập lại mật khẩu (*)", type="password")
            submitted = st.form_submit_button("Tạo tài khoản")
            if submitted:
                if password != confirm_pass: st.error("Mật khẩu không khớp!")
                elif not name or not email or not password: st.error("Thiếu thông tin!")
                else:
                    payload = {"name": name, "phone": phone, "email": email, "password": password, "role": "Citizen"}
                    res = api_request("POST", f"{GENERAL_SERVICE_URL}/api/users/register", json=payload)
                    if res and res.status_code in [200, 201]:
                        st.success("Đăng ký thành công! Vui lòng đăng nhập."); time.sleep(1); switch_auth_mode('login')
                    else: st.error(f"Lỗi: {res.text if res else ''}")
        if st.sidebar.button("🔙 Quay lại"): switch_auth_mode('login')

    elif mode == 'forgot':
        st.sidebar.title("🔑 Quên mật khẩu")
        st.sidebar.info("Vui lòng liên hệ Admin để cấp lại mật khẩu.")
        if st.sidebar.button("🔙 Quay lại"): switch_auth_mode('login')

def logout_handler():
    user = st.session_state.user_info
    display_name = user.get('name') or user.get('Name') or user.get('email')
    st.sidebar.success(f"👤 **{display_name}**")
    raw_role = user.get('Role') or user.get('role', 'Unknown')
    role_map = {"Citizen": "Cư dân", "Manager": "Quản lý", "Technician": "Kỹ thuật viên"}
    st.sidebar.info(f"Vai trò: `{role_map.get(raw_role, raw_role)}`")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.user_info = None; st.session_state.auth_mode = 'login'; st.rerun()

# ==========================================
# GIAO DIỆN: CƯ DÂN
# ==========================================
def view_resident(headers):
    st.title("🏙️ Cổng Phản Ánh Đô Thị")
    tab1, tab2 = st.tabs(["📝 Gửi Phản Ánh", "🗂️ Lịch Sử"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            incident_key = st.selectbox("Loại sự cố (*)", list(INCIDENT_TYPES.keys()), format_func=lambda x: INCIDENT_TYPES[x])
            other_detail = ""
            if incident_key == "OTHER":
                other_detail = st.text_input("Chi tiết sự cố khác:", key="other_incident_input")
            content = st.text_area("Mô tả chi tiết (*)", height=120, key="content_input")
            uploaded = st.file_uploader("Ảnh hiện trường", type=['jpg','png'], key=f"up_{st.session_state.get('uploader_key',0)}")
            media_url = image_to_base64(uploaded)
        with c2:
            st.write("📍 **Vị trí sự cố**")
            detail = st.text_input("Số nhà/Ngõ", key="detail_input")
            street = st.text_input("Đường/Phố", key="street_input")
            ward = st.text_input("Phường/Xã", key="ward_input")
            district = st.text_input("Quận/Huyện", key="district_input")
            city = st.text_input("Tỉnh/Thành phố", value="TP. Hồ Chí Minh", key="city_input")

        if st.button("🚀 Gửi Phản Ánh", type="primary"):
            if not media_url: st.warning("Vui lòng đính kèm ảnh minh họa.")
            elif incident_key == "OTHER" and not other_detail.strip(): st.error("Vui lòng nhập chi tiết sự cố khác!")
            else:
                final_content = content
                if incident_key == "OTHER": final_content = f"[Sự cố khác: {other_detail}] {content}"
                payload = {
                    "IncidentType": INCIDENT_TYPES[incident_key], "Content": final_content, "MediaURL": media_url,
                    "Address": {"Detail": detail.strip().title(), "Street": street.strip().title(), "Ward": ward.strip().title(), "District": district.strip().title(), "City": city.strip().title()}
                }
                res = api_request("POST", f"{REPORT_SERVICE_URL}/api/report/reports", json=payload, headers=headers)
                if res and res.status_code == 200:
                    st.success(f"✅ Gửi thành công! Mã: **{res.json()['data']['ReportId']}**")
                    reset_form(); time.sleep(1.5); st.rerun()
                else: 
                    error_msg = res.text if res else "Lỗi kết nối Server"
                    st.error(f"Gửi thất bại. Chi tiết: {error_msg}")
    with tab2:
        res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports", params={"reporter_id": headers["user-id"]}, headers=headers)
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
                                    reason = st.text_input("Lý do khiếu nại (Nếu chưa hài lòng):")
                                    if st.form_submit_button("Gửi Khiếu Nại"):
                                        res_c = api_request("POST", f"{REPORT_SERVICE_URL}/api/complaint/report/{r['ReportId']}", json={"Content": reason}, headers=headers)
                                        if res_c and res_c.status_code == 200: st.success("Đã ghi nhận khiếu nại!"); time.sleep(1); st.rerun()

# ==========================================
# GIAO DIỆN: MANAGER
# ==========================================
def view_manager(headers):
    st.title("👮 Trung Tâm Điều Hành")
    tasks_res = api_request("GET", f"{TASK_SERVICE_URL}/api/tasks", headers=headers)
    tasks = tasks_res.json() if tasks_res and tasks_res.status_code == 200 else []
    
    approval_tasks = [t for t in tasks if t.get('status') in ["WAITING_FOR_APPROVAL", "WAITING_FOR_RESULT_APPROVAL"]]
    
    if approval_tasks:
        st.error(f"🔔 Có {len(approval_tasks)} nhiệm vụ cần phê duyệt!")
        for task in approval_tasks:
            status = task.get('status')
            tid = task.get('id') or task.get('TaskId')
            with st.container(border=True):
                st.subheader(f"Duyệt Task: {task.get('title')}")
                st.write(f"**KTV:** {task.get('technicianId')}")
                st.info(f"Chi tiết/Link: {task.get('description')}")
                c1, c2 = st.columns(2)
                if status == "WAITING_FOR_APPROVAL":
                    with c1:
                        if st.button("✅ Duyệt Vật Tư", key=f"ok_mat_{tid}"):
                            api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{tid}/status", json={"status": "APPROVED_WAITING_FOR_FIX"}, headers=headers)
                            st.success("Đã duyệt!"); time.sleep(1); st.rerun()
                elif status == "WAITING_FOR_RESULT_APPROVAL":
                    with c1:
                        if st.button("✅ Duyệt Nghiệm Thu (Hoàn tất)", key=f"ok_res_{tid}"):
                            api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{tid}/status", json={"status": "COMPLETED"}, headers=headers)
                            report_id = task.get('reportId')
                            api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{report_id}/status", params={"status": "COMPLETED", "note": "Đã nghiệm thu và hoàn tất."}, headers=headers)
                            st.success("Hoàn tất quy trình!"); time.sleep(1.5); st.rerun()

    st.divider()
    res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports", headers=headers)
    if not res: return
    reports = res.json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng đơn", len(reports))
    c2.metric("Wait", len([x for x in reports if x['Status'] == 'WAITING']))
    c3.metric("Done", len([x for x in reports if x['Status'] == 'COMPLETED']))

    if reports:
        df = pd.DataFrame(reports)
        st.dataframe(df[["Status", "ReportId", "Title", "Created_at"]], use_container_width=True, hide_index=True)
        selected_id = st.selectbox("👉 Chọn Mã Hồ Sơ để xử lý:", df["ReportId"].tolist())
        
        if selected_id:
            r = next((item for item in reports if item["ReportId"] == selected_id), None)
            if r:
                with st.container(border=True):
                    st.subheader(r['Title'])
                    c1, c2 = st.columns([1, 1])
                    with c1: 
                        if r.get('MediaURL'): st.image(r['MediaURL'], caption="Hiện trường")
                    with c2:
                        st.write(f"**Người báo:** `{r.get('ReporterID', 'N/A')}`")
                        st.write(f"**Mô tả:** {r.get('Content')}")
                        st.write("---")
                        st.write("#### 🛠️ Giao Việc")
                        tech_res = api_request("GET", f"{GENERAL_SERVICE_URL}/api/users/role/Technician", headers=headers)
                        tech_list = tech_res.json() if (tech_res and tech_res.status_code == 200) else []
                        
                        if tech_list:
                            tech_opts = {}
                            for t in tech_list:
                                tid = str(t.get('_id') or t.get('UserID') or t.get('id'))
                                tname = t.get('Name') or t.get('name') or t.get('username') or "Noname"
                                tech_opts[tid] = f"{tname}"
                            sel_tech_id = st.selectbox("Chọn KTV:", list(tech_opts.keys()), format_func=lambda x: tech_opts[x])
                        else:
                            sel_tech_id = st.text_input("Mã KTV:", placeholder="TECH...")

                        task_desc = st.text_input("Mô tả công việc:", value=f"Xử lý: {r['Title']}")
                        deadline_date = st.date_input("Hạn chót:", datetime.now() + timedelta(days=3))
                        
                        if st.button("🚀 Giao Việc"):
                            deadline_str = deadline_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                            payload = {"reportId": r["ReportId"], "technicianId": sel_tech_id, "managerId": headers["user-id"], "title": f"Xử lý: {r['Title']}", "description": task_desc, "deadline": deadline_str}
                            t_res = api_request("POST", f"{TASK_SERVICE_URL}/api/tasks", json=payload, headers=headers)
                            if t_res and t_res.status_code in [200, 201]:
                                api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{selected_id}/status", params={"status": "IN_PROGRESS", "note": f"Giao cho {sel_tech_id}"}, headers=headers)
                                st.success(f"Đã giao việc thành công!")
                                time.sleep(1.5); st.rerun()
                            else: st.error("Lỗi tạo Task")

                        with st.expander("Cập nhật trạng thái thủ công"):
                            new_st = st.selectbox("Trạng thái", ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"], key="manual_st")
                            new_note = st.text_input("Lý do:", key="manual_note")
                            if st.button("Lưu"):
                                if new_st == "REJECTED" and not new_note: st.error("Thiếu lý do!")
                                else:
                                    api_request("PATCH", f"{REPORT_SERVICE_URL}/api/report/reports/{selected_id}/status", params={"status": new_st, "note": new_note}, headers=headers)
                                    st.success("Đã cập nhật!")
                                    time.sleep(1.5); st.rerun()

# ==========================================
# GIAO DIỆN: TECHNICIAN (FULL WORKFLOW)
# ==========================================
def view_technician(headers):
    st.title("👷 Cổng Kỹ Thuật Viên")
    # Lấy task của đúng Technician đó
    res = api_request("GET", f"{TASK_SERVICE_URL}/api/tasks", params={"technicianId": headers["user-id"]}, headers=headers)
    
    if res and res.status_code == 200:
        all_tasks = res.json()
        if not all_tasks: 
            st.info("🎉 Không có nhiệm vụ nào.")
        else:
            # Phân loại task
            new_tasks = [t for t in all_tasks if t.get('status') == "ASSIGNED"]
            active_tasks = [t for t in all_tasks if t.get('status') not in ["ASSIGNED", "COMPLETED"]]
            done_tasks = [t for t in all_tasks if t.get('status') == "COMPLETED"]

            tab1, tab2, tab3 = st.tabs([f"🆕 Mới ({len(new_tasks)})", f"🚧 Đang xử lý ({len(active_tasks)})", f"✅ Xong ({len(done_tasks)})"])
            
            # --- TAB 1: NHIỆM VỤ MỚI ---
            with tab1:
                if not new_tasks: st.write("Không có nhiệm vụ mới.")
                for task in new_tasks:
                    tid = task.get('id') or task.get('TaskId')
                    report_id = task.get("reportId") or task.get("ReportId")
                    
                    # Lấy chi tiết Report gốc
                    r_res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports/{report_id}", headers=headers)
                    r_data = r_res.json() if r_res and r_res.status_code == 200 else {}
                    
                    with st.container(border=True):
                        st.subheader(f"🆕 {r_data.get('Title', 'Unknown Task')}")
                        
                        # Chia cột hiển thị cho đẹp
                        c_img, c_info = st.columns([1, 2])
                        with c_img:
                            if r_data.get('MediaURL'): 
                                st.image(r_data['MediaURL'], use_container_width=True, caption="Ảnh hiện trường")
                            else:
                                st.info("Không có ảnh")
                        
                        with c_info:
                            st.warning(f"📅 Deadline: {task.get('deadline', 'Chưa có')}")
                            st.write(f"📍 **Địa chỉ:** {r_data.get('Address',{}).get('Detail')}")
                            st.write(f"📝 **Mô tả:** {task.get('description')}")
                            st.caption(f"Nội dung gốc: {r_data.get('Content')}")

                        if st.button("🚀 XÁC NHẬN NHẬN VIỆC", key=f"acc_{tid}"):
                            api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{tid}/status", json={"status": "WAITING_FOR_MATERIAL_REPORT"}, headers=headers)
                            st.success("Đã nhận! Chuyển sang Tab 'Đang xử lý'."); time.sleep(1); st.rerun()

            # --- TAB 2: ĐANG XỬ LÝ (Đã cập nhật hiển thị) ---
            with tab2:
                if not active_tasks: st.write("Chưa có nhiệm vụ đang làm.")
                for task in active_tasks:
                    tid = task.get('id') or task.get('TaskId')
                    status = task.get('status')
                    report_id = task.get("reportId")
                    
                    r_res = api_request("GET", f"{REPORT_SERVICE_URL}/api/report/reports/{report_id}", headers=headers)
                    r_data = r_res.json() if r_res and r_res.status_code == 200 else {}
                    
                    with st.expander(f"[{status}] {task.get('title')}", expanded=True):
                        # --- CẬP NHẬT: Chia cột hiển thị Ảnh, Address, Deadline ---
                        col_img, col_info = st.columns([1, 2])
                        
                        with col_img:
                            if r_data.get('MediaURL'):
                                st.image(r_data['MediaURL'], use_container_width=True, caption="Ảnh hiện trường")
                            else:
                                st.info("Không có ảnh báo cáo")

                        with col_info:
                            st.warning(f"📅 Deadline: {task.get('deadline', 'Chưa thiết lập')}")
                            st.write(f"📍 **Địa chỉ:** {r_data.get('Address',{}).get('Detail')}")
                            st.info(f"📋 **Yêu cầu:** {task.get('description')}")
                        
                        st.divider()

                        # --- CÁC BƯỚC XỬ LÝ (Logic giữ nguyên) ---
                        # BƯỚC 1: BÁO CÁO VẬT TƯ
                        if status == "WAITING_FOR_MATERIAL_REPORT":
                            st.write("#### 📦 Bước 1: Báo cáo vật tư")
                            uploaded_mat = st.file_uploader("Upload file Excel/Word:", key=f"mat_{tid}")
                            if st.button("Gửi báo cáo vật tư", key=f"btn_mat_{tid}"):
                                url = upload_file_to_media_service(uploaded_mat)
                                if url:
                                    new_desc = task.get('description') + f"\n[Vật tư]: {url}"
                                    api_request("PUT", f"{TASK_SERVICE_URL}/api/tasks/{tid}", json={"description": new_desc}, headers=headers)
                                    api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{tid}/status", json={"status": "WAITING_FOR_APPROVAL"}, headers=headers)
                                    st.success("Đã gửi! Chờ duyệt."); st.rerun()
                                else: st.error("Chưa chọn file hoặc lỗi upload!")

                        # CHỜ DUYỆT
                        elif status == "WAITING_FOR_APPROVAL":
                            st.warning("⏳ Đang chờ Manager duyệt vật tư...")

                        # BƯỚC 2: BẮT ĐẦU SỬA
                        elif status == "APPROVED_WAITING_FOR_FIX":
                            st.success("✅ Vật tư đã duyệt!")
                            if st.button("🛠️ Bắt đầu sửa chữa", key=f"fix_{tid}"):
                                api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{tid}/status", json={"status": "IN_PROGRESS"}, headers=headers)
                                st.rerun()

                        # BƯỚC 3: BÁO CÁO KẾT QUẢ
                        elif status == "IN_PROGRESS":
                            st.write("#### 📸 Bước 3: Báo cáo kết quả")
                            uploaded_res = st.file_uploader("Ảnh/Video kết quả:", key=f"res_{tid}")
                            if st.button("✅ Xác nhận xử lý xong", key=f"btn_res_{tid}"):
                                url = upload_file_to_media_service(uploaded_res)
                                if url:
                                    new_desc = task.get('description') + f"\n[Kết quả]: {url}"
                                    api_request("PUT", f"{TASK_SERVICE_URL}/api/tasks/{tid}", json={"description": new_desc}, headers=headers)
                                    api_request("PATCH", f"{TASK_SERVICE_URL}/api/tasks/{tid}/status", json={"status": "WAITING_FOR_RESULT_APPROVAL"}, headers=headers)
                                    st.success("Đã báo cáo! Chờ nghiệm thu."); st.rerun()
                                else: st.error("Thiếu ảnh minh chứng!")

                        # CHỜ NGHIỆM THU
                        elif status == "WAITING_FOR_RESULT_APPROVAL":
                            st.warning("⏳ Đang chờ Manager nghiệm thu kết quả...")

            with tab3:
                st.dataframe(pd.DataFrame(done_tasks))
    else: st.error("Lỗi tải nhiệm vụ.")

# ==========================================
# MAIN APP FLOW
# ==========================================
if "user_info" not in st.session_state: st.session_state.user_info = None

if not st.session_state.user_info:
    render_auth_sidebar()
    st.info("👈 Vui lòng đăng nhập hoặc đăng ký.")

else:
    logout_handler()
    user = st.session_state.user_info
    raw_role = user.get("Role") or user.get("role", "")
    role_check = str(raw_role).lower().strip()
    uid = str(user.get("UserID") or user.get("userID") or user.get("_id"))
    req_headers = {"user-id": uid, "X-Role": raw_role}
    
    if role_check == "manager": view_manager(req_headers)
    elif role_check == "technician": view_technician(req_headers)
    else: view_resident(req_headers)