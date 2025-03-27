# bluetooth_sender.py (Python 3.8 가상환경에서 실행)
import os
import time
from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY, advertise_service

def tail_f(file):
    """
    파일의 끝부터 새로 추가되는 라인을 계속 읽어내는 제너레이터 함수 (tail -f와 유사)
    """
    file.seek(0, 2)  # 파일 끝으로 이동
    while True:
        line = file.readline()
        if line:
            yield line.strip()
        else:
            time.sleep(0.1)

def main():
    # 바탕화면에 기록된 텍스트파일 경로 (운영체제에 따라 경로가 달라질 수 있음)
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, "max_temp.txt")
    
    # 블루투스 RFCOMM 서버 설정
    server_sock = BluetoothSocket(RFCOMM)
    server_sock.bind(("", PORT_ANY))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]
    
    # 서비스 광고 (UUID는 임의로 지정, 안드로이드 앱과 동일하게 설정해야 함)
    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
    advertise_service(server_sock, "TempService", service_id=uuid,
                      service_classes=[uuid, "SERIAL_PORT"],
                      profiles=["SERIAL_PORT"])
    
    print("블루투스 연결 대기중 (RFCOMM 채널:", port, ")")
    client_sock, client_info = server_sock.accept()
    print("클라이언트 연결됨:", client_info)
    
    # 텍스트파일을 열어 새 라인을 읽고 블루투스로 전송
    try:
        with open(file_path, "r") as f:
            for line in tail_f(f):
                # 안드로이드 어플리케이션에 온도 데이터를 전송 (문자열 + 줄바꿈)
                client_sock.send(line + "\n")
                print("전송된 온도:", line)
                time.sleep(1)  # 초당 한 번 전송
    except Exception as e:
        print("전송 중 오류 발생:", e)
    finally:
        client_sock.close()
        server_sock.close()
        print("블루투스 소켓 종료")

if __name__ == "__main__":
    main()
