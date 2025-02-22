import os
import subprocess
import time
import difflib
from gtts import gTTS
from praatio import textgrid

def run_command(command_list):
    """
    Hàm chạy lệnh qua subprocess và in ra thời gian thực hiện.
    """
    print("Chạy lệnh:", " ".join(command_list))
    start_time = time.time()
    subprocess.run(command_list, check=True)
    end_time = time.time()
    print(f"Thời gian: {end_time - start_time:.2f} giây")

def download_models():
    """
    Tải acoustic model và dictionary của MFA về.
    """
    # run_command(["mfa", "model", "download", "acoustic", "english_us_arpa"])
    # run_command(["mfa", "model", "download", "dictionary", "english_us_arpa"])

def create_corpus():
    """
    Tạo thư mục corpus, file audio và file transcript (.lab).
    """
    corpus_dir = os.path.expanduser("~/mfa_data/my_corpus/")
    os.makedirs(corpus_dir, exist_ok=True)
    
    # Tạo file audio từ văn bản "cat" bằng gTTS
    text = "house"
    tts = gTTS(text=text, lang='en')
    audio_file = os.path.join(corpus_dir, "audio1.wav")
    tts.save(audio_file)
    print("Đã tạo file audio1.wav trong thư mục:", corpus_dir)
    
    # Tạo file transcript (.lab)
    lab_file = os.path.join(corpus_dir, "audio1.lab")
    with open(lab_file, "w", encoding="utf8") as f:
        f.write(text)
    
    return corpus_dir

def run_alignment(corpus_dir):
    """
    Xóa thư mục kết quả căn chỉnh cũ (nếu có) và chạy lệnh align của MFA.
    Trả về đường dẫn file TextGrid tạo ra.
    """
    print(corpus_dir)
    aligned_dir = os.path.expanduser("~/mfa_data/my_corpus_aligned")
    run_command(["rm", "-rf", aligned_dir])
    output_file = os.path.join(aligned_dir, "audio1.TextGrid")

    run_command([
        "mfa", "align_one",
        corpus_dir + "/audio1.wav",                # SOUND_FILE_PATH
        corpus_dir + "/audio1.lab",                  # TEXT_FILE_PATH
        "english_us_arpa",         # DICTIONARY_PATH
        "english_us_arpa",         # ACOUSTIC_MODEL_PATH
        output_file,               # OUTPUT_PATH
        "--single_speaker",        # Buộc chia nhỏ theo utterance (và tắt speaker adaptation)
        "--disable_speaker_adaptation",  # Tắt speaker adaptation để tăng tốc
        "--use_mp",
        "--clean"                  # Xóa các file tạm của lần chạy trước
    ])
    
    # File TextGrid sẽ được tạo với tên trùng với file audio (audio1.TextGrid)
    tg_path = os.path.join(aligned_dir, "audio1.TextGrid")
    return tg_path

def parse_textgrid_phonemes(textgrid_path):
    """
    Mở file TextGrid và trích xuất danh sách âm vị từ tier có chứa "phone".
    """
    tg = textgrid.openTextgrid(textgrid_path, includeEmptyIntervals=False)
    tier_name = None
    for tName in tg.tierNameList:
        if "phone" in tName.lower():
            tier_name = tName
            break
    if tier_name is None:
        raise Exception("Không tìm thấy tier chứa thông tin âm vị trong file TextGrid.")
    
    phonemes = []
    for start, end, mark in tg.tierDict[tier_name].entryList:
        if mark.strip():
            phonemes.append(mark.strip())
    return phonemes

def compare_phonemes(expected, actual):
    """
    So sánh chuỗi âm vị dự kiến và chuỗi nhận được, trả về danh sách khác biệt.
    """
    s = difflib.SequenceMatcher(None, expected, actual)
    mismatches = []
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag != 'equal':
            mismatches.append((expected[i1:i2], actual[j1:j2]))
    return mismatches

def main():
    start_total = time.time()
    
    # 1. Tải acoustic model và dictionary của MFA
    download_models()
    
    # 2. Tạo file audio và transcript
    corpus_dir = create_corpus()
    
    # 3. Chạy MFA forced alignment
    tg_path = run_alignment(corpus_dir)
    print("MFA alignment hoàn thành. File TextGrid được lưu tại:", tg_path)
    
    # # 4. Phân tích file TextGrid để lấy danh sách âm vị
    try:
        # tg_path = "/home/codespace/mfa_data/my_corpus_aligned.TextGrid"
        actual_phonemes = parse_textgrid_phonemes(tg_path)
        print("Các âm vị nhận diện được:", actual_phonemes)
    except Exception as e:
        print("Lỗi khi phân tích file TextGrid:", e)
        return

    # # 5. Phân tích đúng/sai của phát âm so với chuẩn (MCU dictionary)
    # # Ví dụ, đối với từ "cat" theo CMU Dictionary: K, AE1, T
    expected_phonemes = ["K", "AE1", "T"]
    print("Âm vị dự kiến:", expected_phonemes)
    
    mismatches = compare_phonemes(expected_phonemes, actual_phonemes)
    if mismatches:
        print("Có sự khác biệt trong âm vị:")
        for exp, act in mismatches:
            print("  Dự kiến:", exp, " | Thực tế:", act)
    else:
        print("Phát âm của bạn khớp với chuẩn!")
    
    end_total = time.time()
    print(f"Tổng thời gian: {end_total - start_total:.2f} giây")

if __name__ == "__main__":
    main()
