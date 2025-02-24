import os
import subprocess
import time
import difflib
import textgrid
import requests
import io
import random

from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

def run_command(command_list):
    print("Chạy lệnh:", " ".join(command_list))
    start_time = time.time()
    subprocess.run(command_list, check=True)
    end_time = time.time()
    print(f"Thời gian: {end_time - start_time:.2f} giây")

def download_models():
    """Tải acoustic model và dictionary của MFA."""
    # run_command(["mfa", "model", "download", "acoustic", "english_us_arpa"])
    # run_command(["mfa", "model", "download", "dictionary", "english_us_arpa"])

def create_corpus():
    """
    Tạo thư mục corpus, file audio và transcript (.lab) cho từ "failings".
    Thay vì sử dụng gTTS trực tiếp, audio được lấy thông qua endpoint /tts của web server.
    """
    corpus_dir = os.path.expanduser("~/mfa_data/my_corpus/")
    os.makedirs(corpus_dir, exist_ok=True)
    
    text = "continue"
    # Gửi yêu cầu TTS tới webserver tại endpoint /tts
    response = requests.post("http://localhost:5000/tts", json={"text": text, "lang": "en"})
    if response.status_code != 200:
        raise Exception("TTS service failed: " + response.text)
    
    audio_file = os.path.join(corpus_dir, "audio1.wav")
    with open(audio_file, "wb") as f:
        f.write(response.content)
    print("Đã tạo file audio1.wav trong thư mục:", corpus_dir)
    
    lab_file = os.path.join(corpus_dir, "audio1.lab")
    with open(lab_file, "w", encoding="utf8") as f:
        f.write(text)
    
    return corpus_dir, audio_file, lab_file

def run_alignment(corpus_dir, audio_file, lab_file):
    """
    Sử dụng lệnh mfa align_one để căn chỉnh file duy nhất.
    Kết quả (TextGrid) được lưu vào OUTPUT_PATH.
    """
    aligned_dir = os.path.expanduser("~/mfa_data/my_corpus_aligned")
    run_command(["rm", "-rf", aligned_dir])
    os.makedirs(aligned_dir, exist_ok=True)
    
    output_file = os.path.join(aligned_dir, "audio1.TextGrid")
    run_command([
        "mfa", "align_one",
        audio_file,         # SOUND_FILE_PATH
        lab_file,           # TEXT_FILE_PATH
        "english_us_arpa",  # DICTIONARY_PATH
        "english_us_arpa",  # ACOUSTIC_MODEL_PATH
        output_file,        # OUTPUT_PATH
        "--single_speaker",
        "--disable_speaker_adaptation",
        "--clean"
    ])
    return output_file

def parse_textgrid_phonemes(textgrid_path):
    """
    Đọc file TextGrid sử dụng thư viện 'textgrid' và trích xuất danh sách âm vị từ tier có tên chứa "phone".
    """
    tg = textgrid.TextGrid.fromFile(textgrid_path)
    phones_tier = None
    for tier in tg.tiers:
        if "phone" in tier.name.lower():
            phones_tier = tier
            break
    if phones_tier is None:
        raise Exception("Không tìm thấy tier chứa thông tin âm vị trong file TextGrid.")
    
    phonemes = []
    for interval in phones_tier.intervals:
        mark = interval.mark.strip()
        if mark:
            phonemes.append(mark)
    return phonemes

def compare_phonemes(expected, actual):
    """
    So sánh chuỗi âm vị dự kiến và chuỗi nhận được.
    Trả về danh sách các khác biệt (tuple: expected_segment, actual_segment).
    """
    remove_tokens = {"SIL"}

    expected_filtered = [p for p in expected if p.upper() not in remove_tokens]
    actual_filtered = [p for p in actual if p.upper() not in remove_tokens]

    s = difflib.SequenceMatcher(None, expected_filtered, actual_filtered)
    print("Simiarity percent:::::::::", s.ratio() * 100)
    mismatches = []
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag != 'equal':
            mismatches.append((expected_filtered[i1:i2], actual_filtered[j1:j2]))
    return mismatches

def main():
    start_total = time.time()
    
    # 1. Tải acoustic model và dictionary của MFA
    download_models()
    
    # 2. Tạo file audio và transcript (sử dụng endpoint /tts để tạo file audio)
    corpus_dir, audio_file, lab_file = create_corpus()
    
    # 3. Chạy MFA forced alignment (sử dụng align_one để tối ưu cho file duy nhất)
    tg_path = run_alignment(corpus_dir, audio_file, lab_file)
    print("MFA alignment hoàn thành. File TextGrid được lưu tại:", tg_path)
    
    # 4. Phân tích file TextGrid để lấy danh sách âm vị
    try:
        actual_phonemes = parse_textgrid_phonemes(tg_path)
        print("Các âm vị nhận diện được:", actual_phonemes)
    except Exception as e:
        print("Lỗi khi phân tích file TextGrid:", e)
        return

    # 5. So sánh phát âm với chuẩn (hard-coded expected phonemes)
    expected_phonemes = ["M", "EY1", "L", "IH0", "NG", "Z"]

    print("Âm vị dự kiến:", expected_phonemes)
    
    mismatches = compare_phonemes(expected_phonemes, actual_phonemes)
    print("mismatch:::", mismatches)
    if mismatches:
        print("Có sự khác biệt trong âm vị:")
        for exp, act in mismatches:
            print("  Dự kiến:", exp, " | Thực tế:", act)
    else:
        print("Phát âm của bạn khớp với chuẩn!")
    
    end_total = time.time()
    print(f"Tổng thời gian: {end_total - start_total:.2f} giây")

# ------------------------------------------------
# Endpoint cho TTS (giữ nguyên logic cũ)
# ------------------------------------------------
@app.route('/tts', methods=['POST'])
def tts_endpoint():
    """
    Endpoint nhận JSON với khóa "text" và "lang", chuyển văn bản thành âm thanh.
    Âm thanh được tạo bằng gTTS (đầu ra mp3 chuyển đổi sang WAV bằng pydub).
    """
    data = request.get_json()
    text = data.get("text")
    lang = data.get("lang", "en")
    if not text:
        return jsonify({"error": "Missing text parameter"}), 400
    from gtts import gTTS
    tts_obj = gTTS(text=text, lang=lang)
    mp3_fp = io.BytesIO()
    tts_obj.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    # Chuyển đổi từ mp3 sang wav sử dụng pydub
    from pydub import AudioSegment
    audio = AudioSegment.from_file(mp3_fp, format="mp3")
    wav_fp = io.BytesIO()
    audio.export(wav_fp, format="wav")
    wav_fp.seek(0)
    return send_file(wav_fp, mimetype="audio/wav", as_attachment=False, download_name="audio.wav")

# ------------------------------------------------
# Endpoint để chạy toàn bộ quy trình alignment (sử dụng TTS tạo file)
# ------------------------------------------------
@app.route('/align', methods=['GET'])
def align_endpoint():
    """
    Khi gọi endpoint này, quy trình:
      - download_models
      - create_corpus (gọi endpoint /tts để tạo file audio)
      - run_alignment
      - parse TextGrid và so sánh âm vị
    sẽ được thực hiện. Output (stdout) được trả về dạng JSON.
    """
    from io import StringIO
    import sys
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    try:
        main()
    except Exception as e:
        sys.stdout = old_stdout
        return jsonify({"error": str(e)}), 500
    sys.stdout = old_stdout
    output = mystdout.getvalue()
    return jsonify({"result": output})

# ------------------------------------------------
# Hàm xử lý audio từ file upload/recorded (không thay đổi logic căn chỉnh)
# ------------------------------------------------
def process_uploaded_audio(prompt, audio_data, original_filename):
    corpus_dir = os.path.expanduser("~/mfa_data/my_corpus_upload/")
    run_command(["rm", "-rf", corpus_dir])
    os.makedirs(corpus_dir, exist_ok=True)
    
    ext = os.path.splitext(original_filename)[1].lower()
    if ext != ".wav":
        from pydub import AudioSegment
        try:
            # Sử dụng định dạng (loại bỏ dấu chấm) nếu có, mặc định là "webm"
            fmt = ext[1:] if ext else "webm"
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=fmt)
        except Exception as e:
            # Nếu lỗi, cố gắng chuyển sang webm
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        audio_file = os.path.join(corpus_dir, "audio1.wav")
        audio.export(audio_file, format="wav")
    else:
        audio_file = os.path.join(corpus_dir, "audio1.wav")
        with open(audio_file, "wb") as f:
            f.write(audio_data)
    
    lab_file = os.path.join(corpus_dir, "audio1.lab")
    with open(lab_file, "w", encoding="utf8") as f:
        f.write(prompt)
    
    tg_path = run_alignment(corpus_dir, audio_file, lab_file)
    try:
        actual_phonemes = parse_textgrid_phonemes(tg_path)
    except Exception as e:
        actual_phonemes = []
    expected_phonemes = ["F", "EY1", "L", "IH0", "NG", "Z"]
    mismatches = compare_phonemes(expected_phonemes, actual_phonemes)
    result_log = f"Prompt: {prompt}\nExpected: {expected_phonemes}\nActual: {actual_phonemes}\nMismatches: {mismatches}\n"
    return result_log

# ------------------------------------------------
# Endpoint nhận file audio (upload hoặc ghi âm trực tiếp từ trình duyệt)
# ------------------------------------------------
@app.route('/process_audio', methods=['POST'])
def process_audio_endpoint():
    if 'audio' not in request.files:
         return jsonify({"error": "No audio file provided"}), 400
    file = request.files['audio']
    prompt = request.form.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    audio_data = file.read()
    try:
        result_log = process_uploaded_audio(prompt, audio_data, file.filename)
    except Exception as e:
         return jsonify({"error": str(e)}), 500
    return jsonify({"result": result_log})

# ------------------------------------------------
# Giao diện HTML cho người dùng
# ------------------------------------------------
@app.route('/')
def index():
    prompts = [
        "plays"
    ]
    prompt = random.choice(prompts)
    # Lưu ý: Sử dụng {{ }} cho JS được escape trong format()
    return '''
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Voice Alignment Interface</title>
    </head>
    <body>
      <h1>Voice Alignment Interface</h1>
      <p>Please read the following text:</p>
      <h2>{prompt}</h2>
      
      <h3>Record your voice:</h3>
      <button id="start">Start Recording</button>
      <button id="stop" disabled>Stop Recording</button>
      <p id="recordStatus"></p>
      
      <h3>Or Upload a WAV file:</h3>
      <form id="uploadForm" enctype="multipart/form-data">
         <input type="file" name="audio" accept="audio/*" required>
         <input type="hidden" name="prompt" value="{prompt}">
         <button type="submit">Upload and Process</button>
      </form>
      
      <h3>Result:</h3>
      <pre id="result"></pre>
      
      <script>
        let mediaRecorder;
        let recordedChunks = [];
        
        document.getElementById("start").onclick = async function() {{
          recordedChunks = [];
          let stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
          mediaRecorder = new MediaRecorder(stream);
          mediaRecorder.ondataavailable = function(e) {{
            if (e.data.size > 0) {{
              recordedChunks.push(e.data);
            }}
          }};
          mediaRecorder.onstop = function(e) {{
            let blob = new Blob(recordedChunks, {{ type: 'audio/webm' }});
            let formData = new FormData();
            formData.append("audio", blob, "recording.webm");
            formData.append("prompt", "{prompt}");
            fetch("/process_audio", {{
              method: "POST",
              body: formData
            }})
            .then(response => response.json())
            .then(data => {{
              document.getElementById("result").innerText = JSON.stringify(data, null, 2);
            }});
          }};
          mediaRecorder.start();
          document.getElementById("recordStatus").innerText = "Recording...";
          document.getElementById("start").disabled = true;
          document.getElementById("stop").disabled = false;
        }};
        
        document.getElementById("stop").onclick = function() {{
          mediaRecorder.stop();
          document.getElementById("recordStatus").innerText = "Processing...";
          document.getElementById("start").disabled = false;
          document.getElementById("stop").disabled = true;
        }};
        
        // Handle upload form submission
        document.getElementById("uploadForm").onsubmit = function(e) {{
          e.preventDefault();
          let formData = new FormData(document.getElementById("uploadForm"));
          fetch("/process_audio", {{
            method: "POST",
            body: formData
          }})
          .then(response => response.json())
          .then(data => {{
            document.getElementById("result").innerText = JSON.stringify(data, null, 2);
          }});
        }};
      </script>
    </body>
    </html>
    '''.format(prompt=prompt)

if __name__ == "__main__":
    # Chạy Flask server (chế độ đa luồng để xử lý đồng thời các request, tránh deadlock khi gọi nội bộ /tts)
    app.run(host="0.0.0.0", port=5000, threaded=True)
