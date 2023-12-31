import threading
import time

# Tạo một Lock để đồng bộ hóa
lock = threading.Lock()

def download_emails():
    global lock
    while True:
        # Kiểm tra và khóa lock
        with lock:
            print("Đang download emails...")
            time.sleep(5)  # Giả sử quá trình download mất 5 giây
            print("Hoàn tất download.")
        
        # Chờ 60 giây trước khi thực hiện download tiếp theo
        time.sleep(10)

def user_interaction():
    global lock
    while True:
        with lock:
            cmd_input = input("Nhập lệnh của bạn (nhập 'exit' để thoát): ")
            if cmd_input.lower() == 'exit':
                return
        time.sleep(15)

if __name__ == "__main__":
    # Khởi tạo tiến trình download
    download_thread = threading.Thread(target=download_emails)
    download_thread.start()

    # Tiến trình chính cho tương tác với người dùng
    user_interaction()

    # Khi thoát khỏi vòng lặp, đảm bảo tiến trình download kết thúc trước khi thoát
    download_thread.join()
    print("Chương trình đã kết thúc!")
