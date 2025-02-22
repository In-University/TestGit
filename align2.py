import os
import subprocess
import time
import difflib
from gtts import gTTS
import textgrid

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
    Tạo thư mục corpus, file audio và transcript (.lab) cho từ "cat".
    Audio được tạo bằng gTTS.
    """
    corpus_dir = os.path.expanduser("~/mfa_data/my_corpus/")
    os.makedirs(corpus_dir, exist_ok=True)
    
    text = "continue"
    tts = gTTS(text=text, lang='en')
    audio_file = os.path.join(corpus_dir, "audio1.wav")
    tts.save(audio_file)
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
    mismatches = []
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag != 'equal':
            mismatches.append((expected_filtered[i1:i2], actual_filtered[j1:j2]))
    return mismatches


def main():
    start_total = time.time()
    
    # 1. Tải acoustic model và dictionary của MFA
    download_models()
    
    # 2. Tạo file audio và transcript
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

    # 5. So sánh phát âm với chuẩn (ví dụ: từ "cat" theo CMU Dictionary: K, AE1, T)
    expected_phonemes = ["K", "AE1", "T"]
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

if __name__ == "__main__":
    main()
