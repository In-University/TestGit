import wave
import json
from vosk import Model, KaldiRecognizer

# Đường dẫn tới mô hình Vosk đã tải (ví dụ: model-small)
model = Model("./local_model/vosk-model")

# Mở file audio
wf = wave.open("audio.wav", "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file phải có định dạng PCM mono.")
    exit(1)

# Khởi tạo recognizer với sample rate của file audio
rec = KaldiRecognizer(model, wf.getframerate())
# Kích hoạt xuất kết quả word-level
rec.SetWords(True)

# Đọc và xử lý file audio theo từng khối
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        # Kiểm tra và in ra thông tin timestamp cho từng từ nếu có
        if "result" in result:
            for word in result["result"]:
                print(f"{word['word']} | {word['start']} - {word['end']}")
    else:
        # Có thể in ra kết quả tạm thời (partial) nếu cần
        partial = json.loads(rec.PartialResult())
        # print(partial)

# Xử lý kết quả cuối cùng
final_result = json.loads(rec.FinalResult())
if "result" in final_result:
    for word in final_result["result"]:
        print(f"{word['word']} | {word['start']} - {word['end']}")
