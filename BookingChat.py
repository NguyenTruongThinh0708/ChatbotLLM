import streamlit as st
import datetime
import re

st.set_page_config(page_title="Đặt lịch khám", layout="centered")
st.title("🤖 Đặt lịch khám Bệnh viện Hehe")

# ---------------------------
# Session state init
# ---------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "form"      # form -> confirm -> done -> canceled
if "booking" not in st.session_state:
    st.session_state.booking = None
if "email_saved" not in st.session_state:
    st.session_state.email_saved = None
if "want_contact" not in st.session_state:
    st.session_state.want_contact = False
if "cancel_reason" not in st.session_state:
    st.session_state.cancel_reason = None

# ---------------------------
# Utils
# ---------------------------

# Hàm tạo time slots
# def generate_time_slots():
#     slots = []
#     start = datetime.time(5, 0)
#     end = datetime.time(17, 0)
#     current = datetime.datetime.combine(datetime.date.today(), start)
#     end_dt = datetime.datetime.combine(datetime.date.today(), end)
#     while current <= end_dt:
#         t = current.time()
#         # loại giờ nghỉ trưa 11:30 - 13:00
#         if not (datetime.time(11, 30) <= t < datetime.time(13, 0)):
#             slots.append(t.strftime("%H:%M"))
#         current += datetime.timedelta(minutes=30)
#     return slots

def generate_time_slots():
    slots = []
    for hour in range(7, 19):
        start = datetime.time(hour, 0)
        end = datetime.time(hour+1, 0)
        # Bỏ các khung giờ nằm trong khoảng 11:00–13:00
        if start >= datetime.time(11, 0) and start < datetime.time(13, 0):
            continue
        slots.append(f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
    return slots

time_slots = generate_time_slots()

# Hàm tạo chi nhánh slots
def generate_location_slots():
    # Có thể mở rộng list từ DB 
    return [
        "Thủ Đức",
        "Quận 1",
        "Quận 2",
        "Quận 7",
        "Bình Thạnh",
        "Gò Vấp",
        "Tân Bình"
    ]

location_slots = generate_location_slots()

# Hàm tạo lý do hủy lịch slots
def generate_cancel_slots():
    # Có thể mở rộng list từ DB 
    return [
        "",
        "Công việc đột xuất",
        "Vấn đề tài chính",
        "Triệu chứng cải thiện hoặc không còn cấp bách",
        "Nhầm lẫn thông tin đặt lịch",
        "Khác",
    ]

cancel_slots = generate_cancel_slots()

# Hàm kiểm tra họ tên có hợp lệ không
def is_valid_name(name: str) -> bool:
    """
    Kiểm tra họ tên:
    - Không được rỗng
    - Độ dài tối thiểu 2 ký tự
    - Chỉ chứa chữ cái Unicode, khoảng trắng, dấu nháy đơn, chấm và gạch nối
    """
    if not name or not name.strip():
        return False
    name = name.strip()
    if len(name.strip()) < 2:
        return False
    pattern = r"^[^\W\d_](?:[^\W\d_]|[ \.'-])*[^\W\d_]$"
    return re.match(pattern, name, re.UNICODE) is not None

# Hàm kiểm tra mail có đúng cú pháp không
def is_valid_email(email: str) -> bool:
    # regex cơ bản kiểm tra email
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

# Phần gửi mail thông báo
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from email_settings import from_email_default, password_default, HOST, PORT

def send_email(to_email, from_email, password, subject, body):
    # Create server & Try to login
    server = smtplib.SMTP(HOST, PORT)
    server.starttls()
    try:
        server.login(from_email, password)
    except smtplib.SMTPAuthenticationError as e:
        print("Error! Invalid Sender Email or Password!")
        server.quit()
        return

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_email

    message.attach(MIMEText(body, 'plain'))

    server.sendmail(from_email, to_email, message.as_string())
    server.quit()

def write_confirm_email(data):
    email_subject = "Xác nhận đặt lịch khám tại Bệnh viện {TenBenhVien} - Mã: {MaDatLich}"

    email_template = """
    Kính gửi: {HoTen},

    Cảm ơn Quý khách đã lựa chọn Bệnh viện {TenBenhVien}.
    Chúng tôi xin thông báo đặt lịch khám của Quý khách đã được xác nhận với thông tin chi tiết như sau:

    Thông tin đặt lịch
    - Mã đặt lịch: {MaDatLich}
    - Họ và tên: {HoTen}
    - Ngày: {Ngay}
    - Giờ: {Gio}
    - Chi nhánh/Địa chỉ: {ChiNhanh} - {DiaChi}

    Trước khi tới khám
    - Vui lòng có mặt trước ít nhất 15-30 phút để làm thủ tục tiếp nhận.
    - Mang theo: CMND/CCCD/Hộ chiếu, thẻ BHYT (nếu sử dụng), các kết quả xét nghiệm/phiếu khám trước (nếu có).
    - Nếu lịch khám bao gồm xét nghiệm yêu cầu nhịn ăn hoặc chuẩn bị đặc biệt, chúng tôi sẽ có thông báo riêng - vui lòng tuân thủ để kết quả chính xác.
    - Thanh toán: hỗ trợ tiền mặt, thẻ nội địa/quốc tế, và áp dụng BHYT theo quy định (nếu có).

    Hủy / đổi lịch
    - Nếu Quý khách cần hủy hoặc thay đổi lịch, vui lòng liên hệ trước ít nhất 24 giờ (nếu có thể) để chúng tôi sắp xếp.
    - Đổi / hủy qua: Hotline: {Hotline} - Email: {EmailCSKH} - Zalo/Chat: {ZaloChatLink} - Hoặc truy cập đường dẫn: {LinkDoiHuy}

    Lưu ý chăm sóc sức khỏe & an toàn
    - Nếu Quý khách có triệu chứng nhiễm trùng hô hấp (sốt, ho, khó thở), vui lòng thông báo trước để nhân viên sắp xếp khu vực khám phù hợp.
    - Bệnh viện tuân thủ các quy định an toàn y tế; Quý khách vui lòng mang khẩu trang và tuân thủ hướng dẫn của nhân viên.

    Nếu Quý khách cần hỗ trợ thêm, xin vui lòng liên hệ:
    Bệnh viện {TenBenhVien} - Hotline: {Hotline} - Email: {EmailCSKH}
    Thời gian làm việc: {GioLamViec}

    Một lần nữa xin cảm ơn Quý khách. Kính chúc Quý khách sức khỏe và mong được phục vụ!

    Trân trọng,
    Đội ngũ Chăm sóc Khách hàng
    Bệnh viện {TenBenhVien}
    Địa chỉ: {DiaChi} | Website: {Website}
    """

    subject = email_subject.format(**data)
    body = email_template.format(**data)

    return subject, body

def write_cancel_email(data):
    email_subject = "Xác nhận HỦY lịch khám tại Bệnh viện {TenBenhVien} - Mã: {MaDatLich}"

    email_template = """
    Kính gửi: {HoTen},

    Bệnh viện {TenBenhVien} xin xác nhận rằng lịch khám của Quý khách với thông tin sau đã được HỦY:

    Thông tin đặt lịch (đã hủy):
    - Mã đặt lịch: {MaDatLich}
    - Họ và tên: {HoTen}
    - Ngày: {Ngay}
    - Giờ: {Gio}
    - Chi nhánh/Địa chỉ: {ChiNhanh} - {DiaChi}

    Thông tin hủy
    - Lý do (nếu có): {LyDoHuy}
    - Ngày hủy: {NgayHuy}

    Nếu quý khách hủy nhầm hoặc muốn đặt lại lịch, vui lòng liên hệ qua:
    - Hotline: {Hotline}
    - Email: {EmailCSKH}
    - Zalo/Chat: {ZaloChatLink}
    - Hoặc truy cập đường dẫn: {LinkDoiHuy}

    Lưu ý:
    - Nếu lịch có yêu cầu hoàn/hoãn thanh toán hoặc chính sách huỷ riêng, nhân viên CSKH sẽ liên hệ để hướng dẫn cụ thể.
    - Thời gian làm việc CSKH: {GioLamViec}.

    Nếu Quý khách cần hỗ trợ thêm, xin vui lòng liên hệ:
    Bệnh viện {TenBenhVien} - Hotline: {Hotline} - Email: {EmailCSKH}
    Thời gian làm việc: {GioLamViec}

    Một lần nữa xin cảm ơn Quý khách. Kính chúc Quý khách sức khỏe và mong được phục vụ!

    Trân trọng,
    Đội ngũ Chăm sóc Khách hàng
    Bệnh viện {TenBenhVien}
    Địa chỉ: {DiaChi} | Website: {Website}
    """

    subject = email_subject.format(**data)
    body = email_template.format(**data)

    return subject, body



# ---------------------------
# Stage: FORM - chọn ngày giờ
# ---------------------------
if st.session_state.stage == "form":
    st.markdown("### Xin chào 👋, vui lòng điền thông tin để đặt lịch khám:")
    with st.form("booking_form", clear_on_submit=False):
        # Tên
        name = st.text_input(
            "Họ tên",
            value=st.session_state.get("user_name", ""),
            placeholder="Nhập họ tên (bắt buộc)"
        )
        # Ngày
        today = datetime.date.today()
        min_day = today + datetime.timedelta(days=1)
        max_day = today + datetime.timedelta(days=15)
        date = st.date_input("Chọn ngày khám (Trong vòng 2 tuần)",  min_value=min_day, max_value=max_day)
        # Giờ
        time = st.selectbox("Chọn giờ khám", time_slots)
        # Chi nhánh
        location = st.selectbox("Chọn chi nhánh", location_slots)
        submitted = st.form_submit_button("Xác nhận")

    if submitted:
        # Kiểm tra họ tên có hợp lệ không
        if not is_valid_name(name):
            st.error("⚠️ Họ tên không hợp lệ. Vui lòng nhập lại.")
        else:
            # lưu booking tạm
            st.session_state.booking = {
                "name": name,
                "date": date,
                "time": time,
                "location": location,
                "status": "pending"  # pending -> confirmed -> canceled
            }
            st.session_state.email_saved = None
            st.session_state.stage = "contact"
            st.rerun()

# ---------------------------
# Stage: CONTACT - thông tin liên hệ
# ---------------------------
elif st.session_state.stage == "contact":
    b = st.session_state.booking
    if not b:
        # fallback quay về form nếu không có booking
        st.session_state.stage = "form"
        st.rerun()

    st.markdown("### Thông tin đặt lịch")
    st.markdown(
        "📅 Thông tin lịch khám dự kiến:\n\n"
        f"**Ngày khám:** {b['date'].strftime('%d/%m/%Y')} lúc {b['time']}\n\n"
        f"**Địa điểm:** Bệnh viện Hehe chi nhánh {b['location']}\n\n"
    )
    
    # Khi muốn thêm liên hệ
    if st.session_state.want_contact:
        st.markdown("Cách bạn muốn nhận thông báo:")
        col_mail, col_zalo, col_sms, col_back = st.columns(4)

        # Thông báo qua mail
        if col_mail.button("Email"):
            st.session_state.stage = "email"
            st.rerun()

        if col_mail.button("Zalo"):
            st.session_state.stage = "email"
            st.rerun()

        if col_mail.button("SMS"):
            st.session_state.stage = "email"
            st.rerun()

        if col_back.button("Quay lại"):
            st.session_state.stage = "contact"
            st.session_state.want_contact = False
            st.rerun()

    if not st.session_state.want_contact:
        # Có/Không muốn thêm liên hệ
        st.markdown("Bạn có muốn **thêm thông tin liên hệ** để chúng tôi gửi thông báo nhắc bạn khi gần tới lịch hẹn không?")
        col_yes, col_no = st.columns(2)
        if col_yes.button("Có"):
            st.session_state.want_contact = True
            st.rerun()

        if col_no.button("Không"):
            st.session_state.want_contact = False
            st.session_state.stage = "confirm"
            st.rerun()


# ---------------------------
# Stage: EMAIL - nhập email để nhận thông báo
# ---------------------------
elif st.session_state.stage == "email":
    st.markdown("### ✉️ Nhập email để nhận thông báo")
    with st.form("email_form"):
        email = st.text_input("Email nhận thông báo", value=st.session_state.email_saved or "")
        submit_email = st.form_submit_button("Lưu email")
        cancel_email = st.form_submit_button("Hủy")

    if submit_email:
        if is_valid_email(email):
            st.session_state.email_saved = email
            st.success(f"Đã lưu: {email}. Chúng tôi sẽ gửi thông báo nhắc trước.")
            # quay lại trang done để hiển thị lựa chọn khác
            st.session_state.stage = "confirm"
            st.rerun()
        else:
            st.error("⚠️ Email không hợp lệ. Vui lòng nhập lại.")

    if cancel_email:
        st.session_state.stage = "contact"
        st.rerun()

# ---------------------------
# Stage: CONFIRM - xác nhận có/không
# ---------------------------
elif st.session_state.stage == "confirm":
    b = st.session_state.booking
    if not b:
        # fallback quay về form nếu không có booking
        st.session_state.stage = "form"
        st.rerun()

    st.markdown("### Xác nhận đặt lịch")
    st.markdown(
        "Thông tin lịch hẹn khám dự kiến của bạn:\n\n"
        f"**Ngày khám:** {b['date'].strftime('%d/%m/%Y')} lúc {b['time']}\n\n"
        f"**Địa điểm:** Bệnh viện Hehe chi nhánh {b['location']}\n\n"
        f"**Thông báo sẽ gửi qua email:** {st.session_state.email_saved}\n\n"
        "Hãy xác nhận thông tin trên có chính xác không? Nếu có sai sót bạn hãy chọn 'Thay đổi' nhé!"
    )

    col_yes, col_no = st.columns(2)
    if col_yes.button("Xác nhận"):
        st.session_state.booking["status"] = "confirmed"
        st.session_state.stage = "done"
        st.rerun()

    if col_no.button("Thay đổi"):
        # đưa về lại bước 1 (form). xóa booking tạm
        st.session_state.booking = None
        st.session_state.stage = "form"
        st.rerun()

# ---------------------------
# Stage: DONE - đã xác nhận -> chọn hành động (mail / hủy / đổi)
# ---------------------------
elif st.session_state.stage == "done":
    b = st.session_state.booking
    st.markdown("### ✅ Lịch đã được xác nhận")
    if st.session_state.email_saved == None:
        st.markdown(
            "**Đã xác nhận** lịch hẹn khám của bạn:\n\n"
            f"**Ngày khám:** {b['date'].strftime('%d/%m/%Y')} lúc {b['time']}\n\n"
            f"**Địa điểm:** Bệnh viện Hehe chi nhánh {b['location']}\n\n"
            "Vui lòng **đến trước giờ hẹn 15 tới 30 phút** để làm thủ tục bạn nhé!\n\n"
            "Quy trình đặt lịch khám đã hoàn tất, bạn có thể an tâm đến khám 😊"
        )
    else:
        st.markdown(
            "**Đã xác nhận** lịch hẹn khám của bạn:\n\n"
            f"**Ngày khám:** {b['date'].strftime('%d/%m/%Y')} lúc {b['time']}\n\n"
            f"**Địa điểm:** Bệnh viện Hehe chi nhánh {b['location']}\n\n"
            f"**Thông báo sẽ gửi qua email:** {st.session_state.email_saved}\n\n"
            f"Chúng tôi sẽ gửi thông báo nhắc bạn trước 1 ngày qua kênh liên lạc ở trên.\n\n"
            "Vui lòng **đến trước giờ hẹn 15 tới 30 phút** để làm thủ tục bạn nhé!\n\n"
            "Quy trình đặt lịch khám đã hoàn tất, bạn có thể an tâm đến khám 😊"
        )

    data = {
        "TenBenhVien": "Hehe",
        "MaDatLich": f"HEHE-{b['date'].strftime('%Y%m%d')}-00001",
        "HoTen": f"{b['name']}",
        "Ngay": f"{b['date'].strftime('%d/%m/%Y')}",
        "Gio": f"{b['time']}",
        "ChiNhanh": f"{b['location']}",
        "DiaChi": "123 Đường ABC, Quận Thủ Đức, TP.HCM",
        "Hotline": "1900 1234",
        "EmailCSKH": "cskh@bvhehe.vn",
        "ZaloChatLink": "https://zalo.me/19001234",
        "LinkDoiHuy": "https://benhvienhehe.vn/doi-huy",
        "GioLamViec": "07:00 - 19:00 (Thứ 2 - CN)",
        "Website": "https://benhvienhehe.vn"
    }

    subject, body = write_confirm_email(data)
    send_email(st.session_state.email_saved, from_email_default, password_default, subject, body)

    # st.markdown("Bạn muốn thực hiện hành động nào tiếp theo?")
    col_change, col_cancel = st.columns(2)

    # Đổi lịch
    if col_change.button("Đổi lịch hẹn"):
        # quay về bước 1 để chọn lại (xóa booking hiện tại hoặc giữ tạm tuỳ bạn; ở đây ta xóa)
        st.session_state.booking = None
        st.session_state.stage = "form"
        st.rerun()

    # Hủy lịch
    if col_cancel.button("Hủy lịch hẹn"):
        st.session_state.booking["status"] = "cancelling"
        st.session_state.stage = "cancelling"
        st.rerun()


# ---------------------------
# Stage: CANCELLING - Xác nhận hủy
# ---------------------------
elif st.session_state.stage == "cancelling":
    b = st.session_state.booking or {}
    st.markdown("### Xác nhận HỦY lịch khám")
    if b:
        st.markdown(
            "Thông tin lịch hẹn khám đã đặt của bạn:\n\n"
            f"**Ngày khám:** {b['date'].strftime('%d/%m/%Y')} lúc {b['time']}\n\n"
            f"**Địa điểm:** Bệnh viện Hehe chi nhánh {b['location']}\n\n"
            f"**Thông báo sẽ gửi qua email:** {st.session_state.email_saved}\n\n"
            "Bạn có chắc chắn muốn hủy lịch không? Nếu được, bạn có thể cho chúng tôi biết lý do hủy lịch được không?"
        )
    else:
        st.markdown("Lịch trước đó đã bị huỷ.")
    
    reason_select = st.selectbox("Lý do hủy lịch khám", cancel_slots)
    reason_other = ""
    if reason_select == "Khác":
        reason_other = st.text_input(
            "Vui lòng ghi rõ lý do khác",
            placeholder="Nhập lý do cụ thể..."
        )

    col_yes, col_no = st.columns(2)

    # Hủy lịch
    if col_yes.button("Hủy lịch"):
        # Kiểm tra hợp lệ: nếu chọn Khác thì phải nhập lý do
        if reason_select == "Khác" and (not reason_other or reason_other.strip() == ""):
            st.error("Vui lòng nhập lý do hủy chi tiết khi chọn 'Khác'.")
        else:
            # Chuẩn hoá
            reason_final = reason_other.strip() if reason_select == "Khác" else reason_select

            # Lưu thông tin huỷ
            st.session_state.cancel_reason = reason_final
            st.session_state.booking["status"] = "canceled"
            st.session_state.stage = "canceled"
            st.rerun()

    # Quay lại
    if col_no.button("Quay lại"):
        st.session_state.stage = "done"
        st.rerun()

# ---------------------------
# Stage: CANCELED - hiển thị đã hủy
# ---------------------------
elif st.session_state.stage == "canceled":
    b = st.session_state.booking or {}
    st.markdown("### ✖️ Lịch của bạn đã bị hủy")
    if b:
        st.markdown(
            "Thông tin lịch hẹn khám đã HỦY của bạn:\n\n"
            f"**Ngày khám:** {b['date'].strftime('%d/%m/%Y')} lúc {b['time']}\n\n"
            f"**Địa điểm:** Bệnh viện Hehe chi nhánh {b['location']}\n\n"
            f"**Thông báo sẽ gửi qua email:** {st.session_state.email_saved}\n\n"
            "Chúng tôi sẽ gửi thông tin xác nhận hủy lịch qua thông tin liên hệ trên."
        )
    else:
        st.markdown("Lịch trước đó đã bị huỷ.")

    data = {
        "TenBenhVien": "Hehe",
        "MaDatLich": f"HEHE-{b['date'].strftime('%Y%m%d')}-00001",
        "LyDoHuy": f"{st.session_state.cancel_reason}",
        "NgayHuy": f"{datetime.datetime.now()}",
        "HoTen": f"{b['name']}",
        "Ngay": f"{b['date'].strftime('%d/%m/%Y')}",
        "Gio": f"{b['time']}",
        "ChiNhanh": f"{b['location']}",
        "DiaChi": "123 Đường ABC, Quận Thủ Đức, TP.HCM",
        "Hotline": "1900 1234",
        "EmailCSKH": "cskh@bvhehe.vn",
        "ZaloChatLink": "https://zalo.me/19001234",
        "LinkDoiHuy": "https://benhvienhehe.vn/doi-huy",
        "GioLamViec": "07:00 - 19:00 (Thứ 2 - CN)",
        "Website": "https://benhvienhehe.vn"
    }

    subject, body = write_cancel_email(data)
    send_email(st.session_state.email_saved, from_email_default, password_default, subject, body)
    
    # Cung cấp nút để đặt lịch mới
    if st.button("Đặt lịch mới"):
        st.session_state.booking = None
        st.session_state.stage = "form"
        st.rerun()


# ---------------------------
# (Optional) Small status panel (luôn hiển thị)
# ---------------------------
st.divider()
st.markdown("#### Trạng thái hiện tại (debug):")
st.write({
    "stage": st.session_state.stage,
    "booking": {
        k: (v.strftime("%d/%m/%Y") if isinstance(v, datetime.date) else v)
        for k, v in (st.session_state.booking or {}).items()
    },
    "email_saved": st.session_state.email_saved
})
