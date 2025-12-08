import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64 # <--- MỚI THÊM

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

# Hàm chuyển file ảnh thành chuỗi Base64
def image_to_base64(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        # Tạo định dạng Data URI (VD: data:image/png;base64,...)
        return f"data:{uploaded_file.type};base64,{base64_str}"
    except Exception as e:
        return None

st.set_page_config(page_title="Hệ thống Báo cáo Sự cố", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🔐 Giả lập Đăng nhập")
current_user_id = st.sidebar.text_input("UserID của bạn", value="SV12345")
current_role = st.sidebar.selectbox("Vai trò (Role)", ["USER", "MANAGER"], index=0)

headers = {
    "user-id": current_user_id,
    "X-Role": current_role
}

st.title("🚧 Cổng Thông tin Sự cố Hạ tầng Đô thị")

tab1, tab2, tab3 = st.tabs(["📝 Gửi Báo Cáo Mới", "📋 Danh Sách & Xử Lý", "📢 Tra Cứu Khiếu Nại"])

# === TAB 1: TẠO BÁO CÁO (ĐÃ SỬA UPLOAD ẢNH) ===
with tab1:
    st.header("Gửi báo cáo sự cố mới")
    col1, col2 = st.columns(2)
    with col1:
        incident_key = st.selectbox(
            "Loại sự cố (*)", 
            options=list(INCIDENT_TYPES.keys()),
            format_func=lambda x: INCIDENT_TYPES[x]
        )
        content = st.text_area("Mô tả chi tiết (*)", height=100)
        
        # --- THAY ĐỔI Ở ĐÂY: Dùng File Uploader ---
        uploaded_file = st.file_uploader("Chọn ảnh/video minh họa (*)", type=['png', 'jpg', 'jpeg'])
        media_url_to_send = ""
        
        if uploaded_file is not None:
            # Hiển thị ảnh xem trước (Preview)
            st.image(uploaded_file, caption="Ảnh đã chọn", width=200)
            # Chuyển đổi sang chuỗi Base64 để gửi đi
            media_url_to_send = image_to_base64(uploaded_file)
        else:
            # Cho phép nhập link nếu không muốn upload file (Optional)
            media_url_to_send = st.text_input("Hoặc dán đường dẫn ảnh (URL) tại đây:")
        # ------------------------------------------
    
    with col2:
        st.subheader("📍 Địa điểm sự cố")
        detail = st.text_input("Số nhà, ngõ ngách")
        street = st.text_input("Tên đường")
        ward = st.text_input("Phường/Xã")
        district = st.text_input("Quận/Huyện")
        city = st.selectbox("Tỉnh/Thành phố", ["TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Khác"])

    if st.button("Gửi Báo Cáo", type="primary"):
        # Validate ảnh
        if not media_url_to_send:
            st.error("Vui lòng chọn ảnh hoặc nhập link ảnh!")
        else:
            payload = {
                "IncidentType": INCIDENT_TYPES[incident_key], 
                "Content": content,
                "MediaURL": media_url_to_send, # Gửi chuỗi Base64 siêu dài này đi
                "Address": {
                    "Detail": detail,
                    "Street": street,
                    "Ward": ward,
                    "District": district,
                    "City": city
                }
            }
            try:
                res = requests.post(f"{API_URL}/api/report/reports", json=payload, headers=headers)
                if res.status_code == 200:
                    st.success(f"✅ Gửi thành công! Mã báo cáo: {res.json()['data']['ReportId']}")
                    st.json(res.json())
                else:
                    st.error(f"❌ Lỗi: {res.text}")
            except Exception as e:
                st.error(f"Không kết nối được Server: {e}")

# === TAB 2: DANH SÁCH & XỬ LÝ (GIỮ NGUYÊN) ===
with tab2:
    st.header("Danh sách báo cáo")
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        filter_mode = st.radio("Chế độ xem:", ["Của tôi", "Tất cả (Manager)"], horizontal=True)
    with col_filter2:
        if st.button("🔄 Tải lại danh sách"): pass

    try:
        if filter_mode == "Của tôi":
            params = {"reporter_id": current_user_id}
            res = requests.get(f"{API_URL}/api/report/reports", params=params, headers=headers)
        else:
            res = requests.get(f"{API_URL}/api/report/reports", headers=headers)
        
        if res.status_code == 200:
            reports = res.json()
            if not reports:
                st.info("Không có dữ liệu.")
            else:
                df = pd.DataFrame(reports)
                st.dataframe(df[["ReportId", "Title", "Status", "Created_at", "ReporterID"]], use_container_width=True)
                st.divider()
                st.subheader("🛠️ Chi tiết & Xử lý")
                selected_report_id = st.selectbox("Chọn Mã Báo Cáo:", [r["ReportId"] for r in reports], key="select_report_main")
                report_detail = next((r for r in reports if r["ReportId"] == selected_report_id), None)

                if report_detail:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"### {report_detail['Title']}")
                        st.write(f"**Nội dung:** {report_detail.get('Content', '')}")
                        status_color = "blue"
                        if report_detail['Status'] == "COMPLETED": status_color = "green"
                        elif report_detail['Status'] == "REJECTED": status_color = "red"
                        st.markdown(f"**Trạng thái:** :{status_color}[{report_detail['Status']}]")
                        
                        # Hiển thị ảnh (Streamlit tự hiểu chuỗi Base64)
                        if report_detail.get('MediaURL'):
                            st.image(report_detail['MediaURL'], caption="Ảnh hiện trường", width=400)
                    
                    with c2:
                        st.write("**📍 Địa chỉ:**")
                        st.json(report_detail['Address'])
                        st.write("---")
                        st.write("**📝 Ghi chú từ quản lý (Note):**")
                        if report_detail.get("Note"): st.info(report_detail["Note"])
                        else: st.text("Chưa có ghi chú.")

                    st.divider()
                    if current_role == "MANAGER":
                        st.warning("👮 **Khu vực Quản lý (Manager Zone)**")
                        m_col1, m_col2 = st.columns(2)
                        with m_col1:
                            new_status = st.selectbox("Cập nhật trạng thái:", ["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"], index=["WAITING", "IN_PROGRESS", "COMPLETED", "REJECTED"].index(report_detail['Status']))
                        with m_col2:
                            manager_note = st.text_input("Ghi chú/Lý do:")
                        if st.button("💾 Lưu Trạng Thái & Ghi Chú"):
                            patch_params = {"status": new_status, "note": manager_note}
                            patch_res = requests.patch(f"{API_URL}/api/report/reports/{selected_report_id}/status", params=patch_params, headers=headers)
                            if patch_res.status_code == 200:
                                st.success("✅ Cập nhật thành công!")
                                st.rerun()
                            else: st.error(f"❌ Lỗi: {patch_res.text}")

                    if current_role == "USER" and report_detail['Status'] == "COMPLETED":
                        st.error("📢 **Bạn chưa hài lòng với kết quả?**")
                        with st.form("complaint_form"):
                            complaint_content = st.text_area("Nhập lý do khiếu nại:")
                            submitted = st.form_submit_button("Gửi Khiếu Nại")
                            if submitted:
                                comp_payload = {"Content": complaint_content}
                                comp_res = requests.post(f"{API_URL}/api/complaint/report/{selected_report_id}", json=comp_payload, headers=headers)
                                if comp_res.status_code == 200:
                                    st.success(f"✅ Đã gửi khiếu nại! Mã: {comp_res.json()['data']['ComplaintId']}")
                                    st.info("Hệ thống đã tự động mở lại báo cáo (IN_PROGRESS) để nhân viên kiểm tra lại.")
                                    st.rerun()
                                else: st.error(f"❌ Lỗi: {comp_res.text}")
        else: st.error(f"Lỗi tải danh sách: {res.status_code}")
    except Exception as e: st.error(f"Lỗi kết nối: {e}")

# === TAB 3: TRA CỨU KHIẾU NẠI (GIỮ NGUYÊN) ===
with tab3:
    st.write("Tra cứu lịch sử khiếu nại của một báo cáo")
    search_id = st.text_input("Nhập Report ID (VD: RPSV12301)")
    if st.button("Tra cứu"):
        try:
            res = requests.get(f"{API_URL}/api/complaint/report/{search_id}", headers=headers)
            if res.status_code == 200:
                complaints = res.json()
                if complaints:
                    st.success(f"Tìm thấy {len(complaints)} khiếu nại.")
                    for c in complaints:
                        with st.expander(f"🕒 {c['Created_at']} - {c['Status']}"):
                            st.write(f"**Nội dung:** {c['Content']}")
                            st.write(f"**ID:** {c['ComplaintId']}")
                else: st.warning("Không có khiếu nại nào cho báo cáo này.")
            else: st.error("Không tìm thấy báo cáo hoặc lỗi server.")
        except: st.error("Lỗi kết nối.")