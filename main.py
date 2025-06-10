import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from page_home import Ui_MainWindow  # ⬅️ import the generated UI class
from page_settings import PageSettings
from PyQt5.QtWidgets import QFileDialog

class VideoPlaybackThread(QThread):
    frame_signal = pyqtSignal(np.ndarray)  # Signal to send frames to the main thread for display

    def __init__(self, video_file, fps, parent=None):
        super().__init__(parent)
        self.video_file = video_file
        self.fps = fps
        self.playback_cap = cv2.VideoCapture(video_file)

    def run(self):
        while self.playback_cap.isOpened():
            ret, frame = self.playback_cap.read()
            if not ret:
                break

            # Emit frame signal to the main thread
            self.frame_signal.emit(frame)

            # Delay based on FPS (to ensure smooth playback)
            QThread.msleep(int(1000 / self.fps))

        self.playback_cap.release()

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Setup camera and timer
        self.cap = cv2.VideoCapture(3)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Connect buttons
        self.btn_record_start.clicked.connect(self.start_recording)
        self.btn_record_stop.clicked.connect(self.stop_recording)
        self.btn_record_pause.clicked.connect(self.pause_recording)
        self.btn_record_play.clicked.connect(self.play_recording)

        self.second_window = None

        # VideoWriter for recording
        self.recording = False
        self.paused = False
        self.out = None

        # For playback
        self.playback_thread = None
        self.playback_fps = 20.0  # Default FPS for recorded video

        # Timer to control playback frame update
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.playback_update_frame)
        self.playback_frame_queue = []  # Queue to store frames for playback
        self.playback_index = 0  # Current index in the frame queue

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Save frames in BGR format for recording
            if self.recording and not self.paused:
                self.out.write(frame)

            # Convert the frame to RGB for display in the app
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.label_camera.setPixmap(pixmap)

    def start_recording(self):
         file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
         if file_path:
             self.second_window = PageSettings(file_path)
             self.second_window.show()
            #  if self.second_window is None:
            #      self.second_window = PageSettings()
            #      self.second_window.show()



        # """Start recording the video."""
        # self.recording = True
        # self.paused = False

        # # Create a VideoWriter object to save the video (BGR format, no RGB conversion)
        # fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # self.out = cv2.VideoWriter('output.avi', fourcc, self.playback_fps, (640, 480))  # Use playback FPS
        # print("Recording started")

    def stop_recording(self):
        """Stop recording the video and save the file."""
        self.recording = False
        if self.out:
            self.out.release()
        self.out = None
        print("Recording stopped")

    def pause_recording(self):
        """Pause the video recording."""
        if self.recording:
            self.paused = not self.paused
            print("Recording paused" if self.paused else "Recording resumed")

    def play_recording(self):
        """Play the recorded video."""
        print("Playing... Record")

        # Start playback in a separate thread to avoid blocking the UI
        self.playback_thread = VideoPlaybackThread('output.avi', self.playback_fps)
        self.playback_thread.frame_signal.connect(self.store_frame_for_playback)
        self.playback_thread.start()

        # Start the playback timer with an integer value
        self.playback_timer.start(int(1000 / self.playback_fps))  # Trigger the timer every 1/FPS ms

    def store_frame_for_playback(self, frame):
        """Store frames for playback."""
        self.playback_frame_queue.append(frame)

    def playback_update_frame(self):
        """Update the displayed frame in the UI."""
        if self.playback_frame_queue:
            # Get the next frame from the queue
            frame = self.playback_frame_queue[self.playback_index]
            self.playback_index += 1

            # If all frames have been played, stop the playback timer
            if self.playback_index >= len(self.playback_frame_queue):
                self.playback_timer.stop()

            # Convert the frame to RGB for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert the frame to QImage
            image = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], QImage.Format.Format_RGB888)
            
            # Convert the QImage to QPixmap and set it to the label
            pixmap = QPixmap.fromImage(image)
            self.label_camera.setPixmap(pixmap)

    def closeEvent(self, event):
        self.cap.release()
        if self.playback_thread:
            self.playback_thread.quit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())