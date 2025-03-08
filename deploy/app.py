from flask import Flask, request, render_template_string
import os
import torch
import librosa
import base64
import tempfile
import editdistance
import eng_to_ipa as ipa
import wave
import json
import torchaudio
import torchaudio.transforms as T
import soundfile as sf
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# Thiết lập chế độ offline (nếu cần)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# Load model và processor từ thư mục cục bộ
# facebook/wav2vec2-xlsr-53-espeak-cv-ft
processor = Wav2Vec2Processor.from_pretrained("./local_model", local_files_only=True)
model = Wav2Vec2ForCTC.from_pretrained("./local_model", local_files_only=True)
model.eval()

app = Flask(__name__)

# HTML giao diện (đã thêm tùy chọn audio type)
HTML_TEMPLATE = '''
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Phonetic Transcription</title>
  </head>
  <body>
    <h1>Phát âm tiếng Anh: Upload hoặc ghi âm audio</h1>
    <h2>Upload file WAV</h2>
    <form method="POST" action="/upload" enctype="multipart/form-data">
      <input type="text" name="target_word" placeholder="Nhập từ muốn đọc" required>
      <br>
      <label for="audio_type">Chọn kiểu audio:</label>
      <select name="audio_type">
        <option value="single">Từ đơn (Single Word)</option>
        <option value="sentence">Câu (Sentence)</option>
      </select>
      <br>
      <input type="file" name="audio_file" accept="audio/wav">
      <br>
      <button type="submit">Gửi</button>
    </form>
    
    <h2>Hoặc ghi âm trực tiếp</h2>
    <button id="recordButton">Bắt đầu ghi âm</button>
    <button id="stopButton" disabled>Dừng ghi âm</button>
    <p id="recordStatus"></p>
    <form id="recordForm" method="POST" action="/upload">
      <input type="text" name="target_word" placeholder="Nhập từ muốn đọc" required>
      <br>
      <label for="audio_type">Chọn kiểu audio:</label>
      <select name="audio_type">
        <option value="single">Từ đơn (Single Word)</option>
        <option value="sentence">Câu (Sentence)</option>
      </select>
      <br>
      <input type="hidden" name="audio_blob" id="audio_blob">
      <button type="submit">Gửi ghi âm</button>
    </form>
    
    <script>
      let mediaRecorder;
      let audioChunks = [];
      const recordButton = document.getElementById("recordButton");
      const stopButton = document.getElementById("stopButton");
      const recordStatus = document.getElementById("recordStatus");
      const audioBlobInput = document.getElementById("audio_blob");

      recordButton.onclick = async () => {
          if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
              const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
              mediaRecorder = new MediaRecorder(stream);
              mediaRecorder.start();
              recordStatus.innerText = "Đang ghi âm...";
              audioChunks = [];

              mediaRecorder.ondataavailable = event => {
                  audioChunks.push(event.data);
              };

              mediaRecorder.onstop = () => {
                  const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                  const reader = new FileReader();
                  reader.readAsDataURL(audioBlob);
                  reader.onloadend = () => {
                      audioBlobInput.value = reader.result;
                  };
                  recordStatus.innerText = "Ghi âm đã dừng.";
              };

              recordButton.disabled = true;
              stopButton.disabled = false;
          } else {
              alert("Trình duyệt của bạn không hỗ trợ ghi âm.");
          }
      };

      stopButton.onclick = () => {
          mediaRecorder.stop();
          recordButton.disabled = false;
          stopButton.disabled = true;
      };
    </script>
  </body>
</html>
'''

# Hàm loại bỏ dấu trọng âm từ IPA
def remove_stress_marks(ipa_str):
    ipa_str = ipa_str.strip('/')
    return ipa_str.replace('ˈ', '').replace('ˌ', '')

# Hàm nhận dạng audio cho trường hợp single word (không tách file)
def transcribe_audio_file(file_path):
    print("file path::::::", file_path)
    audio_input, sr = librosa.load(file_path, sr=16000)
    input_values = processor(audio_input, sampling_rate=sr, return_tensors="pt").input_values
    with torch.no_grad():
        logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)
    return transcription[0]

# Hàm xử lý audio kiểu câu: tách theo từng từ rồi nhận dạng
def process_sentence_audio(file_path):
    from vosk import Model as VoskModel, KaldiRecognizer
    from pydub import AudioSegment
    import subprocess
    import wave
    import json
    import os

    # Sử dụng ffmpeg để chuyển đổi file đầu vào sang WAV chuẩn
    converted_path = file_path + "_converted.wav"
    try:
        subprocess.run(["ffmpeg", "-y", "-i", file_path, converted_path], check=True)
    except Exception as e:
        print("Lỗi khi chuyển đổi file:", e)
        raise

    # Đọc file audio đã chuyển đổi bằng PyDub
    try:
        audio = AudioSegment.from_file(converted_path, format="wav")
    except Exception as e:
        print("Lỗi khi giải mã audio sau chuyển đổi:", e)
        raise

    # Mở file WAV đã chuyển đổi để lấy thông tin sample rate
    wf = wave.open(converted_path, "rb")
    # Tải mô hình Vosk (chỉnh sửa đường dẫn cho phù hợp)
    vosk_model = VoskModel("./local_model/vosk-model")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(True)

    word_timestamps = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if "result" in result:
                word_timestamps.extend(result["result"])
    final_result = json.loads(rec.FinalResult())
    # print(final_result)

    if "result" in final_result:
        word_timestamps.extend(final_result["result"])

    word_transcriptions = []
    for idx, word_info in enumerate(word_timestamps):
        start_ms = int(word_info["start"] * 1000)
        end_ms = int(word_info["end"] * 1000)
        # Cắt đoạn audio chứa từ đó
        word_audio = audio[start_ms:end_ms]
        temp_filename = f"temp_word_{idx}.wav"
        word_audio.export(temp_filename, format="wav")
        # Nhận dạng từng từ
        transcription = transcribe_audio_file(temp_filename)
        word_transcriptions.append(transcription)
        os.remove(temp_filename)

    # Xóa file chuyển đổi sau khi xử lý
    os.remove(converted_path)
    
    # Ghép các từ lại thành câu
    return " ".join(word_transcriptions)


# Hàm xử lý audio tổng hợp: chọn chế độ dựa vào tham số mode
def process_audio_file(file_path, mode="single"):
    if mode == "single":
        return transcribe_audio_file(file_path)
    elif mode == "sentence":
        return process_sentence_audio(file_path)
    else:
        # Mặc định nhận dạng single word
        return transcribe_audio_file(file_path)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    # Lấy từ mục tiêu từ người dùng
    target_word = request.form.get('target_word', '').strip()
    if not target_word:
        return "Vui lòng nhập từ muốn đọc."
    
    # Lấy lựa chọn kiểu audio: "single" hoặc "sentence"
    audio_type = request.form.get('audio_type', 'single')
    
    # Xử lý audio từ file upload
    if 'audio_file' in request.files and request.files['audio_file'].filename != '':
        audio_file = request.files['audio_file']
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name
        transcription = process_audio_file(tmp_path, mode=audio_type)
        os.remove(tmp_path)
    # Xử lý audio từ ghi âm (base64)
    elif 'audio_blob' in request.form and request.form['audio_blob'] != '':
        audio_data = request.form['audio_blob']
        header, encoded = audio_data.split(',', 1)
        audio_bytes = base64.b64decode(encoded)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        transcription = process_audio_file(tmp_path, mode=audio_type)
        os.remove(tmp_path)
    else:
        return "Không nhận được audio."

    # Chuyển từ mục tiêu thành IPA và loại bỏ trọng âm
    target_ipa = ipa.convert(target_word)
    if target_ipa.startswith('*') and target_ipa.endswith('*'):
        return f"Không tìm thấy IPA cho từ '{target_word}'."
    target_ipa_no_stress = remove_stress_marks(target_ipa)

    # Loại bỏ trọng âm từ phiên âm audio
    transcription_no_stress = remove_stress_marks(transcription)

    # Tính điểm tương đồng bằng khoảng cách Levenshtein
    distance = editdistance.eval(transcription_no_stress.replace(" ", ""), target_ipa_no_stress.replace(" ", ""))
    max_len = max(len(transcription_no_stress), len(target_ipa_no_stress))
    similarity = 1 - (distance / max_len) if max_len > 0 else 1.0

    # Trả về kết quả
    return render_template_string('''
    <h1>Kết quả</h1>
    <p>Từ mục tiêu: {{ target_word }}</p>
    <p>IPA của từ mục tiêu (không trọng âm): {{ target_ipa_no_stress }}</p>
    <p>Phiên âm từ audio: {{ transcription }}</p>
    <p>Phiên âm từ audio (không trọng âm): {{ transcription_no_stress }}</p>
    <p>Độ tương đồng: {{ "%.2f" % similarity }}</p>
    <a href='/'>Thử lại</a>
    ''', target_word=target_word, target_ipa_no_stress=target_ipa_no_stress,
       transcription=transcription, transcription_no_stress=transcription_no_stress,
       similarity=similarity)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
