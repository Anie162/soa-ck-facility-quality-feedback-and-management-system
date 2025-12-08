import streamlit as st
import requests
import pandas as pd
import base64

# --- CẤU HÌNH ---
API_URL = "https://irc-service.onrender.com" 
# API_URL = "http://127.0.0.1:10000"

# Danh sách sự cố
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

def image_to_base64(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        return f"data:{uploaded_file.type};base64,{base64_str}"
    except: return None

def sort_reports_priority(reports_data):
    if not reports_data: return []
    df = pd.DataFrame(reports_data)
    priority_order = ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"]
    # Kiểm tra tính hợp lệ của status trước khi sort
    df['Status'] = pd.Categorical(df['Status'], categories=priority_order, ordered=True)
    df = df.sort_values(by=['Status', 'Created_at'], ascending=[True, False])
    return df.to_dict('records')

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
def clear_form():
    keys = ["content", "media", "detail", "street", "ward", "district", "city"]
    for k in keys: st.session_state[k] = ""
    st.session_state.uploader_key += 1

st.set_page_config(page_title="Hệ thống Quản lý Sự cố", layout="wide")

st.sidebar.title("🔐 Đăng nhập hệ thống")
current_user_id = st.sidebar.text_input("UserID / Mã NV", value="MN001")
current_role = st.sidebar.selectbox("Vai trò", ["USER", "MANAGER", "TECHNICIAN"], index=1)
headers = {"user-id": current_user_id, "X-Role": current_role}

# ==========================================
# 1. GIAO DIỆN USER (DÂN CƯ)
# ==========================================
def render_user_interface():
    st.title(f"👋 Xin chào cư dân {current_user_id}")
    tab1, tab2 = st.tabs(["📝 Gửi Báo Cáo", "🗂️ Lịch Sử Của Tôi"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            incident_key = st.selectbox("Loại sự cố (*)", list(INCIDENT_TYPES.keys()), format_func=lambda x: INCIDENT_TYPES[x])
            content = st.text_area("Mô tả (*)", height=100, key="content")
            uploaded = st.file_uploader("Ảnh minh họa", type=['jpg','png'], key=f"up_{st.session_state.uploader_key}")
            media_url = image_to_base64(uploaded) if uploaded else st.text_input("Hoặc link ảnh:", key="media")
        with c2:
            detail = st.text_input("Số nhà", key="detail")
            street = st.text_input("Đường", key="street")
            ward = st.text_input("Phường/Xã", key="ward")
            district = st.text_input("Quận/Huyện", key="district")
            city = st.text_input("Tỉnh/TP", key="city")

        if st.button("🚀 Gửi Báo Cáo", type="primary"):
            if not media_url: st.error("Thiếu ảnh minh họa!")
            else:
                payload = {
                    "IncidentType": INCIDENT_TYPES[incident_key],
                    "Content": content, "MediaURL": media_url,
                    "Address": {"Detail": detail.strip().title(), "Street": street.strip().title(), "Ward": ward.strip().title(), "District": district.strip().title(), "City": city.strip().title()}
                }
                try:
                    res = requests.post(f"{API_URL}/api/report/reports", json=payload, headers=headers)
                    if res.status_code == 200:
                        st.success(f"Gửi thành công! Mã: {res.json()['data']['ReportId']}")
                        clear_form(); st.rerun()
                    else: st.error(res.text)
                except Exception as e: st.error(f"Lỗi: {e}")

    with tab2:
        res = requests.get(f"{API_URL}/api/report/reports", params={"reporter_id": current_user_id}, headers=headers)
        if res.status_code == 200:
            for r in sort_reports_priority(res.json()):
                with st.expander(f"[{r['Status']}] {r['Title']} - {r['Created_at'][:10]}"):
                    st.write(f"**Nội dung:** {r.get('Content')}")
                    if r.get('MediaURL'): st.image(r['MediaURL'], width=200)
                    if r.get("Note"): st.info(f"Phản hồi: {r['Note']}")
                    if r['Status'] == "COMPLETED":
                        with st.form(key=f"form_{r['ReportId']}"):
                            reason = st.text_input("Lý do khiếu nại")
                            if st.form_submit_button("Gửi Khiếu Nại"):
                                requests.post(f"{API_URL}/api/complaint/report/{r['ReportId']}", json={"Content": reason}, headers=headers)
                                st.success("Đã gửi khiếu nại!"); st.rerun()

# ==========================================
# 2. GIAO DIỆN MANAGER (QUẢN LÝ)
# ==========================================
def render_manager_interface():
    st.title("👮 Trung Tâm Điều Hành")
    res = requests.get(f"{API_URL}/api/report/reports", headers=headers)
    
    if res.status_code == 200:
        reports = sort_reports_priority(res.json())
        df = pd.DataFrame(reports)
        if not df.empty:
            st.dataframe(df[["Status", "ReportId", "Title", "Created_at", "ReporterID"]], use_container_width=True, hide_index=True)
            
            st.divider()
            c1, c2 = st.columns([1, 2])
            with c1:
                selected_id = st.selectbox("👉 Chọn Mã Báo Cáo để xử lý:", df["ReportId"].tolist())
            
            if selected_id:
                r = next((item for item in reports if item["ReportId"] == selected_id), None)
                if r:
                    with st.container(border=True):
                        st.markdown(f"### {r['Title']}")
                        cols = st.columns([1, 1])
                        with cols[0]:
                            if r.get('MediaURL'): st.image(r['MediaURL'], caption="Hiện trường")
                        with cols[1]:
                            st.write(f"**Người báo:** {r['ReporterID']}")
                            st.write(f"**Địa chỉ:** {r['Address'].get('Detail')}, {r['Address'].get('City')}")
                            
                            # --- PHẦN NÀY ĐÃ ĐƯỢC KHÔI PHỤC ---
                            st.write("---")
                            st.write("#### 🛠️ Giao việc (Assign Task)")
                            
                            tech_id_input = st.text_input("Nhập Mã Technician:", placeholder="VD: TECH01")
                            
                            if st.button("🚀 Giao việc ngay"):
                                if not tech_id_input:
                                    st.error("Vui lòng nhập Mã nhân viên kỹ thuật!")
                                else:
                                    # Giả lập: Gọi PATCH update status -> IN_PROGRESS và ghi Note
                                    assign_note = f"Đã giao việc cho kỹ thuật viên: {tech_id_input}"
                                    assign_res = requests.patch(
                                        f"{API_URL}/api/report/reports/{selected_id}/status",
                                        params={"status": "IN_PROGRESS", "note": assign_note},
                                        headers=headers
                                    )
                                    if assign_res.status_code == 200:
                                        st.success(f"Đã giao việc cho {tech_id_input}! Trạng thái chuyển sang IN_PROGRESS.")
                                        st.rerun()
                                    else:
                                        st.error(f"Lỗi: {assign_res.text}")
                            # -----------------------------------

                            st.write("---")
                            st.write("#### 📝 Duyệt / Cập nhật khác")
                            
                            status_opts = ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"]
                            current_status_idx = 0
                            if r['Status'] in status_opts:
                                current_status_idx = status_opts.index(r['Status'])

                            new_status = st.selectbox("Trạng thái", status_opts, index=current_status_idx)
                            manager_note = st.text_input("Ghi chú / Lý do từ chối:", value=r.get("Note", ""))
                            
                            if st.button("💾 Lưu Trạng Thái"):
                                if new_status == "REJECTED" and not manager_note.strip():
                                    st.error("⚠️ BẮT BUỘC phải nhập lý do khi Từ chối (Rejected)!")
                                else:
                                    patch_res = requests.patch(
                                        f"{API_URL}/api/report/reports/{selected_id}/status",
                                        params={"status": new_status, "note": manager_note},
                                        headers=headers
                                    )
                                    if patch_res.status_code == 200: st.success("Cập nhật thành công!"); st.rerun()
                                    else: st.error(f"Lỗi: {patch_res.text}")

# ==========================================
# 3. GIAO DIỆN TECHNICIAN (KỸ THUẬT VIÊN)
# ==========================================
def render_technician_interface():
    st.title(f"👷 Kỹ Thuật Viên: {current_user_id}")
    st.info("Danh sách công việc đang thực hiện (Mô phỏng)")
    
    # Giả lập: Technician thấy tất cả đơn IN_PROGRESS
    res = requests.get(f"{API_URL}/api/report/reports", params={"status": "IN_PROGRESS"}, headers=headers)
    
    if res.status_code == 200:
        reports = res.json()
        if not reports:
            st.warning("Hiện không có công việc nào đang tiến hành.")
        else:
            for task in reports:
                # Chỉ hiện những task có Note chứa tên Tech (Giả lập filter)
                # Hoặc hiện hết nếu muốn test dễ
                with st.expander(f"⚙️ {task['Title']} ({task['ReportId']})"):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if task.get('MediaURL'): st.image(task['MediaURL'], width=250)
                    with c2:
                        st.write(f"**Địa chỉ:** {task['Address'].get('Detail')}, {task['Address'].get('District')}")
                        st.write(f"**Mô tả:** {task.get('Content')}")
                        if task.get('Note'): st.info(f"Yêu cầu: {task.get('Note')}")
                        
                        st.write("---")
                        if st.button("✅ Báo cáo Hoàn thành", key=f"done_{task['ReportId']}"):
                            res_update = requests.patch(
                                f"{API_URL}/api/report/reports/{task['ReportId']}/status",
                                params={"status": "COMPLETED", "note": f"KTV {current_user_id} báo cáo đã xử lý xong."},
                                headers=headers
                            )
                            if res_update.status_code == 200:
                                st.success("Đã hoàn thành!"); st.rerun()
                            else: st.error("Lỗi cập nhật")

# --- ĐIỀU HƯỚNG ---
if current_role == "MANAGER":
    render_manager_interface()
elif current_role == "TECHNICIAN":
    render_technician_interface()
else:
    render_user_interface()