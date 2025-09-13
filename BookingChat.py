import streamlit as st
import datetime
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== Load .env để lấy thông tin gửi mail =====
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# ===== Hàm gửi mail xác nhận =====
def send_confirmation_email(to_email, name, date, time, package):
    subject = "Xác nhận lịch khám của bạn"
    body = f"""
    Xin chào {name},

    Bạn đã đặt lịch khám vào ngày {date} lúc {time} 
    cho gói khám: {package}.

    Vui lòng đến đúng giờ hẹn. Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi.

    Trân trọng,
    Phòng khám
    """

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False


# ===== Hàm tạo các khung giờ 30 phút (5h - 17h, nghỉ trưa 11h30-13h) =====
def generate_time_slots():
    slots = []
    start = datetime.time(5, 0)
    end = datetime.time(17, 0)
    current = datetime.datetime.combine(datetime.date.today(), start)
    end_dt = datetime.datetime.combine(datetime.date.today(), end)
    while current < end_dt:
        t = current.time()
        next_t = (current + datetime.timedelta(minutes=60)).time()
        if not (datetime.time(11,30) <= t < datetime.time(13,0)):
            slots.append(f"{t.strftime('%H:%M')} - {next_t.strftime('%H:%M')}")
        current += datetime.timedelta(minutes=60)
    return slots

time_slots = generate_time_slots()

# ===== Cấu hình giao diện =====
st.set_page_config(page_title="Chatbot Đặt lịch khám", page_icon="🤖")
st.title("🤖 Chatbot Đặt lịch khám")

# ===== Quản lý trạng thái hội thoại =====
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.step = "form"
    st.session_state.form_data = {}

# ===== Hiển thị hội thoại cũ =====
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ===== GIAI ĐOẠN 1: FORM ĐẶT LỊCH =====
if st.session_state.step == "form":
    with st.chat_message("assistant"):
        st.write("📋 Mời bạn nhập thông tin để đặt lịch khám:")

        today = datetime.date.today()
        min_date = today + datetime.timedelta(days=1)
        max_date = today + datetime.timedelta(days=15)

        with st.form("booking_form"):
            name = st.text_input("Họ tên")
            email = st.text_input("Email")
            date = st.date_input("Ngày khám", min_value=min_date, max_value=max_date)
            time = st.selectbox("Giờ khám", time_slots)
            package = st.selectbox("Gói khám", ["Tổng quát", "Tim mạch", "Tai mũi họng", "Răng hàm mặt"])
            submitted = st.form_submit_button("Gửi thông tin")

        if submitted:
            st.session_state.form_data = {
                "name": name,
                "email": email,
                "date": date,
                "time": time,
                "package": package
            }
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"📝 Bạn đã chọn:\n- **Họ tên**: {name}\n- **Email**: {email}\n- **Ngày**: {date.strftime('%d/%m/%Y')}\n- **Giờ**: {time}\n- **Gói khám**: {package}\n\nBạn có muốn xác nhận lịch hẹn này không?"
            })
            st.session_state.step = "confirm"
            st.rerun()


# ===== GIAI ĐOẠN 2: XÁC NHẬN LỊCH =====
elif st.session_state.step == "confirm":
    with st.chat_message("assistant"):
        col1, col2 = st.columns(2)
        if col1.button("✅ Yes"):
            # Gửi mail xác nhận
            data = st.session_state.form_data
            send_confirmation_email(data["email"], data["name"], data["date"].strftime('%d/%m/%Y'), data["time"], data["package"])

            st.session_state.messages.append({
                "role": "assistant",
                "content": f"✅ Bạn đã đặt lịch vào ngày **{data['date'].strftime('%d/%m/%Y')}** lúc **{data['time']}** cho gói **{data['package']}**.\n\nBạn có thể chọn **Cancel** để hủy hoặc **Reschedule** để đặt lại lịch."
            })
            st.session_state.step = "final"
            st.rerun()
        if col2.button("❌ No"):
            st.session_state.messages.append({"role": "assistant", "content": "❌ Đã hủy thông tin, vui lòng nhập lại."})
            st.session_state.step = "form"
            st.rerun()


# ===== GIAI ĐOẠN 3: SAU KHI ĐÃ XÁC NHẬN =====
elif st.session_state.step == "final":
    with st.chat_message("assistant"):
        col1, col2 = st.columns(2)
        if col1.button("🛑 Cancel"):
            st.session_state.messages.append({"role": "assistant", "content": "🛑 Lịch hẹn của bạn đã được hủy."})
            st.session_state.step = "form"
            st.rerun()
        if col2.button("🔁 Reschedule"):
            st.session_state.messages.append({"role": "assistant", "content": "🔁 Vui lòng nhập lại thông tin để đổi lịch."})
            st.session_state.step = "form"
            st.rerun()
