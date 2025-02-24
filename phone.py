from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import torch
import librosa
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

processor = Wav2Vec2Processor.from_pretrained("./local_model", local_files_only=True)
model = Wav2Vec2ForCTC.from_pretrained("./local_model", local_files_only=True)
model.eval()  # Đặt model ở chế độ đánh giá

# Đọc file audio "play.wav" và resample về 16000 Hz
audio_input, sr = librosa.load("play.wav", sr=16000)

# Xử lý audio: cung cấp sampling_rate=16000
input_values = processor(audio_input, sampling_rate=sr, return_tensors="pt").input_values

# Lấy logits từ model
with torch.no_grad():
    logits = model(input_values).logits

# Lấy argmax và decode kết quả thành văn bản
predicted_ids = torch.argmax(logits, dim=-1)
transcription = processor.batch_decode(predicted_ids)

print("Transcription:", transcription)
