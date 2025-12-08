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

# --- HÀM HỖ TRỢ ---
def image_to_base64(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        return f"data:{uploaded_file.type};base64,{base64_str}"
    except: return None

# Hàm sắp xếp ưu tiên: WAITING > IN_PROGRESS > COMPLETED > REJECTED
def sort_reports_priority(reports_data):
    if not reports_data: return []
    df = pd.DataFrame(reports_data)
    
    # Định nghĩa thứ tự ưu tiên
    priority_order = ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"]
    
    # Biến cột Status thành kiểu Categorical để sắp xếp theo ý muốn
    df['Status'] = pd.Categorical(df['Status'], categories=priority_order, ordered=True)
    
    # Sắp xếp: Theo Status trước, sau đó đến ngày tạo mới nhất
    df = df.sort_values(by=['Status', 'Created_at'], ascending=[True, False])
    
    return df.to_dict('records')

# Quản lý reset form
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
def clear_form():
    keys = ["content", "media", "detail", "street", "ward", "district", "city"]
    for k in keys: st.session_state[k] = ""
    st.session_state.uploader_key += 1

st.set_page_config(page_title="Hệ thống Báo cáo Sự cố", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🔐 Đăng nhập hệ thống")
current_user_id = st.sidebar.text_input("UserID", value="SV12345")
current_role = st.sidebar.selectbox("Vai trò", ["USER", "MANAGER"], index=0)
headers = {"user-id": current_user_id, "X-Role": current_role}

# ==========================================
# GIAO DIỆN DÀNH CHO NGƯỜI DÂN (REPORTER)
# ==========================================
def render_user_interface():
    st.title(f"👋 Xin chào cư dân {current_user_id}")
    tab1, tab2 = st.tabs(["📝 Gửi Báo Cáo", "🗂️ Lịch Sử Của Tôi"])

    # --- TAB 1: GỬI BÁO CÁO ---
    with tab1:
        st.subheader("Thông báo sự cố mới")
        c1, c2 = st.columns(2)
        with c1:
            incident_key = st.selectbox("Loại sự cố (*)", list(INCIDENT_TYPES.keys()), format_func=lambda x: INCIDENT_TYPES[x])
            content = st.text_area("Mô tả (*)", height=100, key="content")
            uploaded = st.file_uploader("Ảnh minh họa", type=['jpg','png'], key=f"up_{st.session_state.uploader_key}")
            media_url = image_to_base64(uploaded) if uploaded else st.text_input("Hoặc link ảnh:", key="media")
        
        with c2:
            st.write("📍 **Vị trí**")
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
                    "Address": {
                        "Detail": detail.strip().title(), "Street": street.strip().title(),
                        "Ward": ward.strip().title(), "District": district.strip().title(),
                        "City": city.strip().title()
                    }
                }
                try:
                    res = requests.post(f"{API_URL}/api/report/reports", json=payload, headers=headers)
                    if res.status_code == 200:
                        st.success(f"Gửi thành công! Mã: {res.json()['data']['ReportId']}")
                        clear_form()
                        st.rerun()
                    else: st.error(res.text)
                except Exception as e: st.error(f"Lỗi: {e}")

    # --- TAB 2: LỊCH SỬ (CHỈ XEM CỦA MÌNH) ---
    with tab2:
        # Gọi API Filter theo reporter_id
        res = requests.get(f"{API_URL}/api/report/reports", params={"reporter_id": current_user_id}, headers=headers)
        if res.status_code == 200:
            raw_reports = res.json()
            # Sắp xếp ưu tiên
            sorted_reports = sort_reports_priority(raw_reports)
            
            if not sorted_reports:
                st.info("Bạn chưa gửi báo cáo nào.")
            else:
                for r in sorted_reports:
                    # Card hiển thị đẹp
                    with st.expander(f"[{r['Status']}] {r['Title']} - {r['Created_at'][:10]}"):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            if r.get('MediaURL'): st.image(r['MediaURL'], width=200)
                        with c2:
                            st.write(f"**ID:** `{r['ReportId']}`")
                            st.write(f"**Nội dung:** {r.get('Content')}")
                            if r.get("Note"): st.info(f"Phản hồi: {r['Note']}")
                            
                            # Nút khiếu nại nếu đã xong
                            if r['Status'] == "COMPLETED":
                                with st.form(key=f"form_{r['ReportId']}"):
                                    reason = st.text_input("Lý do khiếu nại")
                                    if st.form_submit_button("Gửi Khiếu Nại"):
                                        res_c = requests.post(f"{API_URL}/api/complaint/report/{r['ReportId']}", json={"Content": reason}, headers=headers)
                                        if res_c.status_code == 200:
                                            st.success("Đã gửi khiếu nại!")
                                            st.rerun()

# ==========================================
# GIAO DIỆN DÀNH CHO QUẢN LÝ (MANAGER)
# ==========================================
def render_manager_interface():
    st.title("👮 Trung Tâm Điều Hành Sự Cố")
    
    # Dashboard Thống kê nhanh
    res = requests.get(f"{API_URL}/api/report/reports", headers=headers)
    if res.status_code == 200:
        reports = res.json()
        total = len(reports)
        waiting = len([r for r in reports if r['Status'] == 'WAITING'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng đơn", total)
        m2.metric("Đang chờ xử lý", waiting, delta_color="inverse")
        
        if st.button("🔄 Cập nhật dữ liệu"): st.rerun()
        
        st.divider()
        st.subheader("📋 Danh sách cần xử lý")
        
        # Sắp xếp ưu tiên: WAITING lên đầu
        sorted_reports = sort_reports_priority(reports)
        
        # Hiển thị dạng bảng tương tác
        df = pd.DataFrame(sorted_reports)
        if not df.empty:
            st.dataframe(
                df[["Status", "ReportId", "Title", "Created_at", "ReporterID"]],
                use_container_width=True,
                hide_index=True
            )
            
            st.write("---")
            c1, c2 = st.columns([1, 1])
            with c1:
                selected_id = st.selectbox("Chọn Mã Báo Cáo để xử lý:", df["ReportId"].tolist())
                
            if selected_id:
                # Tìm chi tiết báo cáo
                r = next((item for item in sorted_reports if item["ReportId"] == selected_id), None)
                if r:
                    with st.container(border=True):
                        st.markdown(f"### {r['Title']}")
                        cols = st.columns([1, 1])
                        with cols[0]:
                            if r.get('MediaURL'): st.image(r['MediaURL'], caption="Hiện trường")
                        with cols[1]:
                            st.write(f"**Người báo:** {r['ReporterID']}")
                            st.write(f"**Địa chỉ:** {r['Address'].get('Detail')}, {r['Address'].get('City')}")
                            st.write(f"**Nội dung:** {r.get('Content')}")
                            
                            # Form xử lý
                            st.write("#### ⚡ Xử lý:")
                            new_status = st.selectbox(
                                "Trạng thái", 
                                ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"],
                                index=["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"].index(r['Status'])
                            )
                            manager_note = st.text_input("Ghi chú nội bộ / Lý do:", value=r.get("Note", ""))
                            
                            if st.button("💾 Cập nhật trạng thái"):
                                patch_res = requests.patch(
                                    f"{API_URL}/api/report/reports/{selected_id}/status",
                                    params={"status": new_status, "note": manager_note},
                                    headers=headers
                                )
                                if patch_res.status_code == 200:
                                    st.success("Đã cập nhật!")
                                    st.rerun()
                                else:
                                    st.error(f"Lỗi: {patch_res.text}")

# --- ĐIỀU HƯỚNG CHÍNH ---
if current_role == "MANAGER":
    render_manager_interface()
else:
    render_user_interface()