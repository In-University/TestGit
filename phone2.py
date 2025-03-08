from flask import Flask, request, render_template_string
import os
import torch
import librosa
import base64
import tempfile
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import eng_to_ipa as ipa
import editdistance

# Thiết lập chế độ offline (nếu cần)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# Load model và processor từ thư mục cục bộ
# facebook/wav2vec2-xlsr-53-espeak-cv-ft
processor = Wav2Vec2Processor.from_pretrained("./local_model", local_files_only=True)
model = Wav2Vec2ForCTC.from_pretrained("./local_model", local_files_only=True)
model.eval()

app = Flask(__name__)

# HTML giao diện
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
      <input type="file" name="audio_file" accept="audio/wav">
      <button type="submit">Gửi</button>
    </form>
    
    <h2>Hoặc ghi âm trực tiếp</h2>
    <button id="recordButton">Bắt đầu ghi âm</button>
    <button id="stopButton" disabled>Dừng ghi âm</button>
    <p id="recordStatus"></p>
    <form id="recordForm" method="POST" action="/upload">
      <input type="text" name="target_word" placeholder="Nhập từ muốn đọc" required>
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

# Hàm xử lý audio
def process_audio_file(file_path):
    audio_input, sr = librosa.load(file_path, sr=16000)
    input_values = processor(audio_input, sampling_rate=sr, return_tensors="pt").input_values
    with torch.no_grad():
        logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)
    return transcription[0]


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    # Lấy từ mục tiêu từ người dùng
    target_word = request.form.get('target_word', '').strip()
    if not target_word:
        return "Vui lòng nhập từ muốn đọc."

    # Xử lý audio từ file upload
    if 'audio_file' in request.files and request.files['audio_file'].filename != '':
        audio_file = request.files['audio_file']
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name
        transcription = process_audio_file(tmp_path)
        os.remove(tmp_path)
    # Xử lý audio từ ghi âm (base64)
    elif 'audio_blob' in request.form and request.form['audio_blob'] != '':
        audio_data = request.form['audio_blob']
        header, encoded = audio_data.split(',', 1)
        audio_bytes = base64.b64decode(encoded)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        transcription = process_audio_file(tmp_path)
        os.remove(tmp_path)
    else:
        return "Không nhận được audio."

    # return "hihi"
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