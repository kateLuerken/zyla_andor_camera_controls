import cv2

def find_available_camera(max_index=3):
    for index in range(max_index):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            cap.release()
            return index
        
    return None

if __name__ == "__main__":
    found = find_available_camera()
    print(f"Cameras found: {found}")