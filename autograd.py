#pip install PyMuPDF
#pip install openai

import fitz  # PyMuPDF
import argparse
import os, json
from openai import OpenAI
import base64
import pandas as pd

#client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
client = OpenAI(api_key="OPENAI_API_KEY_HERE")

def convert_pdf_to_images(pdf_path, output_folder):
    images = fitz.open(pdf_path)
    image_paths = []

    for i, image in enumerate(images):
        pix = image.get_pixmap()
        image_path = os.path.join(output_folder, f'page_{i + 1}.png')
        pix.save(image_path)#, 'PNG')
        image_paths.append(image_path)

    return image_paths

def check_file_type_by_extension(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
        return "Image"
    elif ext == '.pdf':
        return "PDF"
    else:
        return "Unknown"

def extract_image(path, output_folder):
    output_folder=output_folder+"/output-img"
    os.makedirs(output_folder, exist_ok=True)
    # Gantikan path file yang ingin diproses
    file_path = path
    file_type=check_file_type_by_extension(file_path)
    if file_type == "PDF":
        image_paths = convert_pdf_to_images(file_path,output_folder)
    elif file_type == "Image":
        image_paths = [file_path]
    else:
        raise ValueError("Unsupported file type. Please provide a PDF or image file.")
    return image_paths

# ----------Extract numbered answers dynamically from images ----------
# Output: {"items":[{"no":"1","answer":"..."}, ...]}
extract_schema = {
    "name": "extract_schema",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "no": {"type": "string"},
                        "question": {"type": "string"},
                        "answer": {"type": "string"}
                    },
                    "required": ["no", "question", "answer"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["items"],
        "additionalProperties": False
    }
}

def extract_numbered_answers_from_images(image_paths: list[str], output_folder: str, kind: str) -> dict:
    content = [{
        "type": "text",
        "text": f"""
Baca dokumen ujian dalam bentuk gambar ({kind}).
Tugas:
- Identifikasi nomor soal/jawaban yang ada (contoh: 1,2,3... atau 1a,1b).
- Untuk setiap nomor, ambil teks jawaban yang terkait nomor tersebut.
- Output HARUS JSON sesuai schema (items: no, answer).
Catatan:
- Jika jawaban untuk suatu nomor tidak ada, jangan buat itemnya.
- Jangan menambahkan field lain.
"""
    }]

    image_contents = []
    for p in image_paths:
        with open(p, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_contents.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        #content.append(image_contents)
        content.extend(image_contents)

    resp = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": content}],
        temperature=0.0,
        response_format={"type": "json_schema", "json_schema": extract_schema},
    )
    data_struct= json.loads(resp.choices[0].message.content)
    with open(output_folder+"/"+kind+".json", "w", encoding="utf-8") as f:
            json.dump(data_struct, f, indent=4, ensure_ascii=False)
    return data_struct

def struct_key_answer(path_key):
    if path_key is not None:
        try:
            print("Extracting key answer...")
            kunci_imgs = extract_image(path_key, output_folder="key-answer")
            kunci_struct = extract_numbered_answers_from_images(kunci_imgs, output_folder="key-answer", kind="kunci")
        except Exception as e:
            print(f"Failed to extract key answer. Please check the oath file and try again. Error: {e}")
    else:
        print("Reading key answer from file...")
        with open("key-answer/kunci.json", "r", encoding="utf-8") as f:
            kunci_struct = json.load(f)    
    return kunci_struct

def struct_student_answer(path_student):
    mhs_imgs = extract_image(path_student, output_folder="student-answer")
    mhs_struct = extract_numbered_answers_from_images(mhs_imgs, output_folder="student-answer", kind="mahasiswa")
    return mhs_struct

# ---------- Grade per number 0-100 (dynamic count), compute final in Python ----------
grading_schema = {
    "name": "grading_schema_dynamic",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "no": {"type": "string"},
                        "score_0_100": {"type": "number"},
                        "rationale": {"type": "string"},
                        "feedback": {"type": "string"},
                        "missing_points": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["no", "score_0_100", "rationale", "feedback", "missing_points"],
                    "additionalProperties": False
                }
            },
            "flags": {
                "type": "object",
                "properties": {
                    "too_short": {"type": "boolean"},
                    "possible_off_topic": {"type": "boolean"}
                },
                "required": ["too_short", "possible_off_topic"],
                "additionalProperties": False
            }
        },
        "required": ["items", "flags"],
        "additionalProperties": False
    }
}

rubric = """
Nilai tiap nomor dalam skala 0-100 berdasarkan kesesuaian dengan kunci:
- 90-100: tepat & lengkap + istilah kunci + argumen jelas (contoh jika relevan)
- 70-89 : mayoritas benar tapi kurang kedalaman/istilah kunci/contoh
- 50-69 : pemahaman parsial, ada bagian salah/kurang penting
- 0-49  : salah konsep / sangat tidak lengkap / tidak menjawab
Aturan:
- Jangan menganggap ada poin jika tidak tertulis.
- Jika konsep inti salah, skor maksimal 49 meski tulisannya panjang.
"""

def grade_dynamic(key_items: list[dict], student_items: list[dict]) -> dict:
    # map by no
    key_map = {it["no"].strip(): it["answer"] for it in key_items}
    stu_map = {it["no"].strip(): it["answer"] for it in student_items}

    # grade only numbers that exist in KEY
    nos = sorted(key_map.keys())
    pairs = [{"no": no, "key": key_map.get(no, ""), "student": stu_map.get(no, "")} for no in nos]

    prompt = f"""
Kamu penilai ujian yang sangat teliti.
Nilai berdasarkan KUNCI & RUBRIK saja.

RUBRIK:
{rubric}

DATA (JSON):
{json.dumps(pairs, ensure_ascii=False)}

Tugas:
- Beri skor 0-100 untuk tiap nomor (no).
- Beri rationale singkat, feedback singkat, dan missing_points.
- Jangan hitung nilai akhir.
"""

    resp = client.chat.completions.create(
        #model="gpt-5.2",
        #model="gpt-4.1-mini",
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_schema", "json_schema": grading_schema},
    )

    result = json.loads(resp.choices[0].message.content)

    # compute final score in Python (average across key items)
    scores = [it["score_0_100"] for it in result["items"]]
    final = sum(scores) / len(scores) if scores else 0.0
    result["overall_score_0_100"] = round(final, 2)
    return result

def save_to_excel(grading_result: dict, output_path: str):
    df = pd.DataFrame(grading_result["items"])

    df["missing_points"] = df["missing_points"].apply(lambda x: "; ".join(x))

    df.loc[len(df)] = {
    "no": "Overall",
    "score_0_100": grading_result["overall_score_0_100"],
    "rationale": "",
    "feedback": "",
    "missing_points": ""
    }

    # Export to Excel
    df.to_excel(output_path, index=False)


    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student_answer", type=str, required=True)
    parser.add_argument("--key_answer", type=str, required=False)
    args = parser.parse_args()

    path_student=args.student_answer
    path_key=args.key_answer 

    # Extract key answer
    kunci_struct = struct_key_answer(path_key)   
    mhs_struct = struct_student_answer(path_student)

    graded = grade_dynamic(kunci_struct["items"], mhs_struct["items"])
    with open("grading_result.json", "w", encoding="utf-8") as f:
            json.dump(graded, f, indent=4, ensure_ascii=False)
    print("Grading completed. Result saved to grading_result.json")
  
    save_to_excel(graded, output_path="grading_result.xlsx")
    print("Grading result also saved to grading_result.xlsx")

if __name__ == "__main__":
    main()