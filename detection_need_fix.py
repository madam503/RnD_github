# detection.py (Python 3.11 가상환경에서 실행)
import os
import time
import random  # 실제 센서/영상 처리 대신 임의의 온도 값을 사용

def get_max_temp():
    # 실제 센서 또는 영상 처리 결과로부터 최대 온도를 계산하는 부분으로 교체하세요.
    return round(random.uniform(20.0, 50.0), 1)

def main():
    # 바탕화면 경로에 텍스트 파일 생성 (운영체제에 따라 경로가 달라질 수 있음)
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, "max_temp.txt")
    
    # 기존 파일이 있다면 삭제
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 새 파일 생성
    with open(file_path, "w") as f:
        f.write("")
    
    print("영상 처리 및 온도 기록 시작 (파일:", file_path, ")")
    
    try:
        while True:
            # 여기에 영상 처리, 인공지능 판별 등 필요한 작업을 수행하세요.
            # 그 후 센서 또는 영상에서 계산한 최대 온도 값을 받아옵니다.
            max_temp = get_max_temp()
            
            # 온도 데이터를 텍스트 파일에 기록 (한 줄씩 추가)
            with open(file_path, "a") as f:
                f.write(f"{max_temp}\n")
            
            print(f"기록된 온도: {max_temp} C")
            time.sleep(1)  # 초당 한 번 기록
    except KeyboardInterrupt:
        print("프로그램 종료.")

if __name__ == "__main__":
    main()
