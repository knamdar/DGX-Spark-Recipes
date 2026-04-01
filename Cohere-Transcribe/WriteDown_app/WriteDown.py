"""
Developer: Ernest (Khashayar) Namdar
Email: ernest.namdar@gmail.com
"""
import sys
import os
import wave
import tempfile
from pathlib import Path

import requests
import numpy as np
import sounddevice as sd
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QCheckBox, QFileDialog, QMessageBox, QGroupBox, QStackedWidget,
    QGridLayout
)

DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1E1E2E;
}
QLabel, QCheckBox {
    color: #CDD6F4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    background: transparent;
}
QGroupBox {
    color: #89B4FA;
    font-weight: bold;
    font-size: 14px;
    border: 1px solid #45475A;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px;
    background-color: #1E1E2E;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #181825;
    color: #CDD6F4;
    border: 1px solid #313244;
    border-radius: 5px;
    padding: 5px;
    font-size: 13px;
    selection-background-color: #89B4FA;
}
QTextEdit {
    font-family: "Consolas", monospace;
    font-size: 14px;
}
QPushButton {
    background-color: #89B4FA;
    color: #11111B;
    font-weight: bold;
    font-size: 13px;
    border-radius: 5px;
    padding: 7px 15px;
    border: none;
}
QPushButton:hover {
    background-color: #B4BEFE;
}
QPushButton:pressed {
    background-color: #74C7EC;
}
QPushButton:disabled {
    background-color: #45475A;
    color: #A6ADC8;
}
"""

class RealtimeWorker(QThread):
    text_segment_signal = Signal(str)
    error_signal = Signal(str)
    
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_recording = True
        self.samplerate = 16000
        self.buffer = []
        
    def audio_callback(self, indata, frames, time, status):
        if status:
            pass
        if self.is_recording:
            self.buffer.append(indata.copy())

    def run(self):
        try:
            stream = sd.InputStream(samplerate=self.samplerate, channels=1, callback=self.audio_callback, dtype='int16')
            with stream:
                while self.is_recording:
                    QThread.sleep(3) # Process in 3 second windows for pseudo-realtime buffering
                    if not self.buffer: continue
                    
                    frames = list(self.buffer)
                    self.buffer.clear()
                    recording = np.concatenate(frames, axis=0)
                    
                    fd, path = tempfile.mkstemp(suffix=".wav", prefix="wd_rt_")
                    os.close(fd)
                    with wave.open(path, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(self.samplerate)
                        wf.writeframes(recording.tobytes())
                    
                    headers = {}
                    if self.params.get('api_key'):
                        headers["Authorization"] = f"Bearer {self.params['api_key']}"
                    data = {"model": self.params.get('model')}
                    if self.params.get('language'):
                        data["language"] = self.params['language']
                    
                    with open(path, "rb") as f:
                        files = {"file": ("chunk.wav", f, "audio/wav")}
                        response = requests.post(self.params['url'], headers=headers, files=files, data=data, timeout=15)
                    
                    try:
                        os.remove(path)
                    except:
                        pass
                        
                    if response.status_code == 200:
                        text = response.json().get('text', '')
                        if text.strip():
                            self.text_segment_signal.emit(text.strip())
        except Exception as e:
            self.error_signal.emit(f"Realtime Error: {str(e)}")

    def stop(self):
        self.is_recording = False

class BatchWorker(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)
    
    def __init__(self, file_path, params):
        super().__init__()
        self.file_path = file_path
        self.params = params
        
    def run(self):
        try:
            headers = {}
            if self.params.get('api_key'):
                headers["Authorization"] = f"Bearer {self.params['api_key']}"
            data = {"model": self.params.get('model')}
            if self.params.get('language'):
                data["language"] = self.params['language']
            
            with open(self.file_path, "rb") as f:
                mod_filename = Path(self.file_path).name
                mime="audio/wav"
                if mod_filename.endswith(".mp3"): mime="audio/mpeg"
                if mod_filename.endswith(".flac"): mime="audio/flac"
                if mod_filename.endswith(".m4a"): mime="audio/mp4"

                files = {"file": (mod_filename, f, mime)}
                response = requests.post(self.params['url'], headers=headers, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                text = response.json().get('text', '')
                self.finished_signal.emit(text)
            else:
                self.error_signal.emit(f"Server error: {response.status_code} - {response.text}")
        except Exception as e:
            self.error_signal.emit(f"Transcription Failed: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Write Down")
        self.resize(850, 650)
        
        logo_path = os.path.join(os.path.dirname(__file__), "wd_logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
            
        self.setStyleSheet(DARK_QSS)
        
        self.samplerate = 16000
        self.rec_buffer = []
        self.is_manual_recording = False
        self.active_worker = None
        self.selected_file_path = None
        self.manual_wav_path = None
        
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)
        
        # --- Config Box ---
        cfg_box = QGroupBox("Server Configuration")
        cfg_layout = QGridLayout(cfg_box)
        
        cfg_layout.addWidget(QLabel("Server URL:"), 0, 0)
        self.url_edit = QLineEdit("http://localhost:8000/v1/audio/transcriptions")
        cfg_layout.addWidget(self.url_edit, 0, 1)
        
        cfg_layout.addWidget(QLabel("API Key:"), 0, 2)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Optional")
        cfg_layout.addWidget(self.api_key_edit, 0, 3)
        
        cfg_layout.addWidget(QLabel("Model:"), 1, 0)
        self.model_edit = QLineEdit("CohereLabs/cohere-transcribe-03-2026")
        cfg_layout.addWidget(self.model_edit, 1, 1)
        
        cfg_layout.addWidget(QLabel("Language:"), 1, 2)
        self.lang_options = {
            "English": "en", "German": "de", "French": "fr", "Italian": "it",
            "Spanish": "es", "Portuguese": "pt", "Greek": "el", "Dutch": "nl",
            "Polish": "pl", "Arabic": "ar", "Vietnamese": "vi",
            "Chinese (Mandarin)": "zh", "Japanese": "ja", "Korean": "ko"
        }
        self.lang_box = QComboBox()
        self.lang_box.addItems(list(self.lang_options.keys()))
        cfg_layout.addWidget(self.lang_box, 1, 3)
        
        main_layout.addWidget(cfg_box)
        
        # --- Workflow Selection ---
        wf_box = QGroupBox("Transcription Mode")
        wf_layout = QVBoxLayout(wf_box)
        
        wf_top = QHBoxLayout()
        wf_top.addWidget(QLabel("Select Mode:"))
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["File Upload", "Manual Recording", "Realtime Microphone"])
        self.mode_selector.currentIndexChanged.connect(self.switch_mode)
        wf_top.addWidget(self.mode_selector)
        wf_top.addStretch()
        wf_layout.addLayout(wf_top)
        
        self.stack = QStackedWidget()
        
        # Page 0: File Upload
        page_file = QWidget()
        l_file = QHBoxLayout(page_file)
        self.btn_select_file = QPushButton("Select Audio File")
        self.btn_select_file.clicked.connect(self.select_file)
        self.lbl_file_path = QLabel("No file selected.")
        self.btn_transcribe_file = QPushButton("Transcribe File")
        self.btn_transcribe_file.setEnabled(False)
        self.btn_transcribe_file.clicked.connect(self.transcribe_file)
        l_file.addWidget(self.btn_select_file)
        l_file.addWidget(self.lbl_file_path, stretch=1)
        l_file.addWidget(self.btn_transcribe_file)
        self.stack.addWidget(page_file)
        
        # Page 1: Manual Record
        page_rec = QWidget()
        l_rec = QHBoxLayout(page_rec)
        self.btn_rec_start = QPushButton("Start Recording")
        self.btn_rec_start.clicked.connect(self.start_manual_record)
        self.btn_rec_stop = QPushButton("Stop Recording")
        self.btn_rec_stop.setEnabled(False)
        self.btn_rec_stop.clicked.connect(self.stop_manual_record)
        self.btn_transcribe_rec = QPushButton("Transcribe Recording")
        self.btn_transcribe_rec.setEnabled(False)
        self.btn_transcribe_rec.clicked.connect(self.transcribe_recording)
        l_rec.addWidget(self.btn_rec_start)
        l_rec.addWidget(self.btn_rec_stop)
        l_rec.addWidget(self.btn_transcribe_rec)
        l_rec.addStretch()
        self.stack.addWidget(page_rec)
        
        # Page 2: Realtime
        page_rt = QWidget()
        l_rt = QHBoxLayout(page_rt)
        self.btn_rt_start = QPushButton("Start Realtime Stream")
        self.btn_rt_start.clicked.connect(self.start_realtime)
        self.btn_rt_stop = QPushButton("Stop Stream")
        self.btn_rt_stop.setEnabled(False)
        self.btn_rt_stop.clicked.connect(self.stop_realtime)
        l_rt.addWidget(self.btn_rt_start)
        l_rt.addWidget(self.btn_rt_stop)
        l_rt.addStretch()
        self.stack.addWidget(page_rt)
        
        wf_layout.addWidget(self.stack)
        main_layout.addWidget(wf_box)
        
        # --- Output Area ---
        out_header_layout = QHBoxLayout()
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #A6E3A1; font-weight: bold;")
        out_header_layout.addWidget(self.lbl_status)
        out_header_layout.addStretch()
        
        self.btn_copy = QPushButton("Copy Text")
        self.btn_copy.clicked.connect(self.copy_transcript)
        out_header_layout.addWidget(self.btn_copy)
        
        self.btn_clear = QPushButton("Clear Screen")
        self.btn_clear.clicked.connect(self.clear_transcript)
        out_header_layout.addWidget(self.btn_clear)
        
        main_layout.addLayout(out_header_layout)
        
        self.out_box = QTextEdit()
        self.out_box.setPlaceholderText("Transcription output will appear here...")
        main_layout.addWidget(self.out_box)
        
        # --- Autosave Area ---
        save_box = QGroupBox("Export Configuration")
        save_layout = QHBoxLayout(save_box)
        self.chk_autosave = QCheckBox("Enable Autosave")
        save_layout.addWidget(self.chk_autosave)
        
        save_layout.addWidget(QLabel("Output Directory:"))
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcripts")
        self.save_dir_edit = QLineEdit(default_dir)
        save_layout.addWidget(self.save_dir_edit, stretch=1)
        
        self.btn_browse_save = QPushButton("Browse...")
        self.btn_browse_save.clicked.connect(self.browse_save)
        save_layout.addWidget(self.btn_browse_save)
        main_layout.addWidget(save_box)

    def clear_transcript(self):
        self.out_box.clear()
        self.active_autosave_file = None
        self.lbl_status.setText("Screen cleared.")

    def copy_transcript(self):
        text = self.out_box.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.lbl_status.setText("Transcript copied to clipboard!")

    def switch_mode(self, idx):
        self.stack.setCurrentIndex(idx)
        
    def get_params(self):
        return {
            'url': self.url_edit.text().strip(),
            'api_key': self.api_key_edit.text().strip(),
            'model': self.model_edit.text().strip(),
            'language': self.lang_options.get(self.lang_box.currentText(), "")
        }

    def append_transcript(self, text):
        if text.strip():
            self.out_box.append(text)
            self.do_autosave(text)

    def generate_autosave_path(self):
        from datetime import datetime
        base_dir = self.save_dir_edit.text().strip()
        os.makedirs(base_dir, exist_ok=True)
        filename = f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return os.path.join(base_dir, filename)

    def do_autosave(self, content):
        if self.chk_autosave.isChecked():
            try:
                if not hasattr(self, 'active_autosave_file') or not self.active_autosave_file:
                    self.active_autosave_file = self.generate_autosave_path()
                
                with open(self.active_autosave_file, "a", encoding="utf-8") as f:
                    f.write(content + "\n")
            except Exception as e:
                self.lbl_status.setText(f"Autosave warning: {str(e)}")

    def browse_save(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Autosave Directory", self.save_dir_edit.text())
        if directory:
            self.save_dir_edit.setText(directory)

    def handle_error(self, err_msg):
        self.lbl_status.setText("Error!")
        QMessageBox.critical(self, "Error", err_msg)
        self.cleanup_ui()

    def cleanup_ui(self):
        self.btn_rt_start.setEnabled(True)
        self.btn_rt_stop.setEnabled(False)
        self.btn_transcribe_file.setEnabled(bool(self.selected_file_path))
        self.btn_select_file.setEnabled(True)
        self.btn_rec_start.setEnabled(True)
        self.btn_transcribe_rec.setEnabled(bool(self.manual_wav_path))
        self.lang_box.setEnabled(True)

    # --- Mode 0: File Upload
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav *.mp3 *.flac *.m4a *.mp4);;All Files (*.*)")
        if path:
            self.selected_file_path = path
            self.lbl_file_path.setText(Path(path).name)
            self.btn_transcribe_file.setEnabled(True)

    def transcribe_file(self):
        if not self.selected_file_path: return
        self.lbl_status.setText("Uploading and Transcribing File...")
        self.btn_transcribe_file.setEnabled(False)
        self.btn_select_file.setEnabled(False)
        
        self.active_worker = BatchWorker(self.selected_file_path, self.get_params())
        self.active_worker.finished_signal.connect(self.on_batch_done)
        self.active_worker.error_signal.connect(self.handle_error)
        self.active_worker.start()

    def on_batch_done(self, text):
        self.lbl_status.setText("Transcription Complete")
        self.out_box.append("\n[File Transcript]:\n" + text)
        self.active_autosave_file = None
        self.do_autosave("[File Transcript]:\n" + text)
        self.cleanup_ui()

    # --- Mode 1: Manual Record
    def manual_audio_cb(self, indata, frames, time, status):
        if self.is_manual_recording:
            self.rec_buffer.append(indata.copy())

    def start_manual_record(self):
        self.rec_buffer = []
        self.is_manual_recording = True
        try:
            self.rec_stream = sd.InputStream(samplerate=self.samplerate, channels=1, callback=self.manual_audio_cb, dtype='int16')
            self.rec_stream.start()
            self.lbl_status.setText("Recording manual segment...")
            self.btn_rec_start.setEnabled(False)
            self.btn_rec_stop.setEnabled(True)
            self.btn_transcribe_rec.setEnabled(False)
        except Exception as e:
            self.handle_error(str(e))

    def stop_manual_record(self):
        self.is_manual_recording = False
        if hasattr(self, 'rec_stream'):
            self.rec_stream.stop()
            self.rec_stream.close()
        
        self.btn_rec_stop.setEnabled(False)
        self.btn_rec_start.setEnabled(True)
        
        if not self.rec_buffer: return
        
        recording = np.concatenate(self.rec_buffer, axis=0)
        fd, path = tempfile.mkstemp(suffix=".wav", prefix="wd_man_")
        os.close(fd)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(recording.tobytes())
            
        self.manual_wav_path = path
        self.lbl_status.setText("Recording saved. Ready to transcribe.")
        self.btn_transcribe_rec.setEnabled(True)

    def transcribe_recording(self):
        if not self.manual_wav_path: return
        self.lbl_status.setText("Transcribing manual recording...")
        self.btn_transcribe_rec.setEnabled(False)
        self.btn_rec_start.setEnabled(False)
        
        self.active_worker = BatchWorker(self.manual_wav_path, self.get_params())
        self.active_worker.finished_signal.connect(self.on_man_done)
        self.active_worker.error_signal.connect(self.handle_error)
        self.active_worker.start()
        
    def on_man_done(self, text):
        self.lbl_status.setText("Transcription Complete")
        self.out_box.append("\n[Recording]:\n" + text)
        self.active_autosave_file = None
        self.do_autosave("[Recording]:\n" + text)
        self.cleanup_ui()

    # --- Mode 2: Realtime
    def start_realtime(self):
        self.lbl_status.setText("Streaming Realtime Transcription...")
        self.btn_rt_start.setEnabled(False)
        self.btn_rt_stop.setEnabled(True)
        self.lang_box.setEnabled(False)
        
        self.active_autosave_file = self.generate_autosave_path() if self.chk_autosave.isChecked() else None
        
        self.active_worker = RealtimeWorker(self.get_params())
        self.active_worker.text_segment_signal.connect(self.append_transcript)
        self.active_worker.error_signal.connect(self.handle_error)
        self.active_worker.start()

    def stop_realtime(self):
        if isinstance(self.active_worker, RealtimeWorker):
            self.active_worker.stop()
        self.lbl_status.setText("Realtime Streaming Stopped")
        self.cleanup_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())