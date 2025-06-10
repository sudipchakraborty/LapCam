import cv2

# Replace with your camera stream URL
ip_camera_url = "http://192.168.3.68:8080/video"  # Likely correct for IP Webcam

cap = cv2.VideoCapture(ip_camera_url)

if not cap.isOpened():
    print("Error: Cannot open stream")
    exit()

print("Streaming from IP Camera. Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow("IP Camera Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
