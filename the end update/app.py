from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import pandas as pd
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import os

# === Flask app initialization ===
BASE_DIR = Path(__file__).parent
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))

# load .env
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
app.secret_key = SECRET_KEY

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === File paths ===
file_path_backend = str(BASE_DIR / "data/Sorted_Ngành_Nghề.xlsx")  # Backend data Excel file
file_path_frontend = str(BASE_DIR / "data/Book1.xlsx")             # Frontend data Excel file
file_path_family = str(BASE_DIR / "data/FamilyFactor.xlsx")
file_path_forecasting = str(BASE_DIR / "data/generate/bang_xep_hang_nganh_nghe_AAGR_2025_2028.xlsx")

# === Load datasets ===
data_backend = pd.read_excel(file_path_backend)
data_frontend = pd.read_excel(file_path_frontend)
family_data = pd.read_excel(file_path_family)
forecasting_data = pd.read_excel(file_path_forecasting)

# === Helpers ===
def clean_brackets(column):
    cleaned_data = []
    for entry in column:
        try:
            cleaned_data.append(" ".join(ast.literal_eval(entry)))
        except (ValueError, SyntaxError):
            cleaned_data.append(str(entry).replace("[", "").replace("]", ""))
    return cleaned_data

def clean_commas(input_data):
    """Tách chuỗi dựa trên dấu phẩy và làm sạch khoảng trắng."""
    if not isinstance(input_data, str):
        return []
    elements = input_data.split(',')
    cleaned_data = [element.strip() for element in elements if element.strip()]
    return cleaned_data

def yn_to_bool(v):
    """Chuyển 'yes'/'no', 'Có'/'Không', true/false,… sang bool."""
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    yes_set = {"yes", "y", "true", "1", "có", "co", "x"}
    no_set  = {"no", "n", "false", "0", "không", "khong"}
    if s in yes_set:
        return True
    if s in no_set:
        return False
    return False

# === Ensure required columns exist on backend data ===
for col in ['Khả năng và Điểm mạnh', 'Sở thích và Đam mê', 'MBTI', 'Tổ hợp môn']:
    if col not in data_backend.columns:
        print(f"Warning: Column '{col}' is missing in the backend data. Adding empty placeholder.")
        data_backend[col] = ""

# === Clean specific columns for TF-IDF ===
data_backend['MAIN STRENGTHS'] = clean_brackets(data_backend['MAIN STRENGTHS'])
data_backend['Khả năng và Điểm mạnh'] = clean_brackets(data_backend['Khả năng và Điểm mạnh'])
data_backend['MAIN INTERESTEDS'] = clean_brackets(data_backend['MAIN INTERESTEDS'])
data_backend['Sở thích và Đam mê'] = clean_brackets(data_backend['Sở thích và Đam mê'])

# === Combine relevant columns for TF-IDF processing ===
data_backend['Combined'] = (
    data_backend['MBTI'].fillna("") + " " +
    data_backend['Tổ hợp môn'].fillna("") + " " +
    data_backend['MAIN STRENGTHS'].fillna("") + " " +
    data_backend['Khả năng và Điểm mạnh'].fillna("") + " " +
    data_backend['MAIN INTERESTEDS'].fillna("") + " " +
    data_backend['Sở thích và Đam mê'].fillna("")
)

# === Vectorize the combined data using TF-IDF ===
tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(data_backend['Combined'])

# === Clean forecasting columns and build CAGR lookup ===
forecasting_data.columns = forecasting_data.columns.str.strip()
cagr_dict = forecasting_data.set_index('nganh_nghe')['AAGR (%)'].to_dict()

# === Console logger for Top 10 details ===
def log_top_10_career_details(top_10_suggestions):
    print("\n🏆 TOP 10 NGÀNH NGHỀ ĐƯỢC ĐỀ XUẤT 🏆")
    print("="*70)
    for idx, (career, details) in enumerate(top_10_suggestions, start=1):
        print(f"#{idx} - 📚 Ngành: {career}")
        print(f"🔹 MBTI Score: {details['mbti_score']:.2f}")
        print(f"🔹 Subjects Score: {details['subjects_score']:.2f}")
        print(f"🔹 Strengths Score: {details['strengths_score']:.2f}")
        print(f"🔹 Interests Score: {details['interests_score']:.2f}")
        print(f"🔹 PF Score (Tổng điểm cá nhân): {details['PF_score']:.2f}")
        print(f"🔹 Family Score (Điểm gia đình): {details['family_score']:.2f}")
        print(f"🔹 Social Factor Score (Điểm xã hội): {details['social_factor_score']:.2f}")
        print(f"🏆 Final Score (Tổng điểm cuối cùng): {details['final_score']:.2f}")
        print("="*70)

# ================== SAVE endpoint ==================
@app.route('/save', methods=['POST'])
def save_route():
    if request.content_type != 'application/json':
        return jsonify({"error": "Invalid content type"}), 415

    data = request.get_json() or {}
    print("📥 Payload nhận được từ FE:", data)   # LOG PAYLOAD

    # Cho phép FE gửi save_only để chỉ lưu (không tính gợi ý)
    is_save_only = bool(
        data.get('save_only') or data.get('action') == 'save' or data.get('source') == 'save_btn'
    )

    # --- chat_id from session ---
    chat_id = session.get("username")
    print("👤 chat_id từ session:", chat_id)     # LOG CHAT_ID
    if not chat_id:
        return jsonify({"error": "Chưa đăng nhập (thiếu session username)."}), 401

    # --- Read selections ---
    financial_influence_raw = data.get('financial_influence')   # "yes"/"no" | "Có"/"Không"
    family_has_industry_raw = data.get('family_has_industry')   # "yes"/"no" | "Có"/"Không"

    financial_influence_bool = yn_to_bool(financial_influence_raw)
    family_has_industry_bool = yn_to_bool(family_has_industry_raw)

    family_advice = (data.get('family_advice') or '').strip()
    if not family_advice:
        family_advice = "Có" if family_has_industry_bool else "Không"

    family_industry_select = (data.get('family_industry_select') or '').strip()
    if not family_has_industry_bool:
        family_industry_select = ""

    mbti = (data.get('mbti') or '').strip().upper()
    subjects = [s.strip().upper() for s in (data.get('subjects') or [])]
    mainstrengths = set(data.get('mainstrengths') or [])
    strengths     = set(data.get('strengths') or [])
    maininterests = set(data.get('maininterests') or [])
    interests     = set(data.get('interests') or [])

    # --- Update/Insert UserProfile ---
    if supabase:
        update_fields = {
            "MBTI": mbti,
            "SUBJECT": ", ".join(subjects),
            "STRENGTHS": ", ".join(sorted(set(list(mainstrengths) + list(strengths)))),
            "INTERESTEDS": ", ".join(sorted(set(list(maininterests) + list(interests)))),
            "family_advice": family_advice,
            "family_industry": family_industry_select,
            "financial_influence": financial_influence_bool  # bool trong DB
        }
        try:
            print("[DEBUG] save_route chat_id =", chat_id)
            # 1) UPDATE theo chat_id
            res_upd = supabase.table("UserProfile").update(update_fields).eq("chat_id", chat_id).execute()
            updated_rows = getattr(res_upd, "data", []) or []
            print("[DEBUG] UPDATE UserProfile rows:", updated_rows)

            # 2) Nếu chưa có dòng nào -> UPSERT (insert theo chat_id)
            if not updated_rows:
                payload = {"chat_id": chat_id, **update_fields}
                res = supabase.table("UserProfile").upsert(payload, on_conflict="chat_id").execute()
                print("[DEBUG] UPSERT UserProfile:", getattr(res, "data", None))

            if is_save_only:
                return jsonify({
                    "ok": True,
                    "message": "Đã lưu hồ sơ.",
                    "updated": updated_rows
                }), 200

        except Exception as e:
            import traceback
            print("[ERROR] update/insert UserProfile:", e)
            traceback.print_exc()
            if is_save_only:
                return jsonify({"ok": False, "error": "Không thể lưu hồ sơ."}), 500
    else:
        print("[WARN] Supabase chưa cấu hình, bỏ qua update UserProfile.")
        if is_save_only:
            return jsonify({"ok": False, "error": "Supabase chưa cấu hình."}), 500

    # --- Scoring (khi không save_only) ---
    mainstrengths_vector = tfidf_vectorizer.transform([" ".join(mainstrengths)]) if mainstrengths else None
    strengths_vector     = tfidf_vectorizer.transform([" ".join(strengths)]) if strengths else None
    maininterests_vector = tfidf_vectorizer.transform([" ".join(maininterests)]) if maininterests else None
    interests_vector     = tfidf_vectorizer.transform([" ".join(interests)]) if interests else None

    high_tuition_careers = family_data['Top học phí'].dropna().unique()

    suggestions = []
    for i in range(len(data_backend)):
        row = data_backend.iloc[i]

        backend_mbtis = {m.strip().upper() for m in str(row['MBTI']).split(',')}
        mbti_score = 1.0 if mbti and mbti in backend_mbtis else 0.0

        backend_subjects = {subject.strip().upper() for subject in str(row['Tổ hợp môn']).split(',')}
        subjects_score = 1.0 if any(sub in backend_subjects for sub in subjects) else 0.0

        main_strengths_score = cosine_similarity(
            mainstrengths_vector, tfidf_vectorizer.transform([row['MAIN STRENGTHS']])
        ).flatten()[0] if mainstrengths_vector is not None else 0.0

        remaining_strengths_score = cosine_similarity(
            strengths_vector, tfidf_vectorizer.transform([row['Khả năng và Điểm mạnh']])
        ).flatten()[0] if strengths_vector is not None else 0.0

        strengths_score = main_strengths_score * 0.35 + remaining_strengths_score * 0.65

        main_interests_score = cosine_similarity(
            maininterests_vector, tfidf_vectorizer.transform([row['MAIN INTERESTEDS']])
        ).flatten()[0] if maininterests_vector is not None else 0.0

        remaining_interests_score = cosine_similarity(
            interests_vector, tfidf_vectorizer.transform([row['Sở thích và Đam mê']])
        ).flatten()[0] if interests_vector is not None else 0.0

        interests_score = main_interests_score * 0.35 + remaining_interests_score * 0.65

        PF_score = (
            mbti_score * 0.2391 +
            subjects_score * 0.2457 +
            strengths_score * 0.2609 +
            interests_score * 0.2543
        )

        family_score = 0.5456
        if financial_influence_bool and row['Ngành'] in high_tuition_careers:
            family_score -= 0.2

        if family_advice == 'Có' and row['Lĩnh vực'] == family_industry_select:
            family_score += 0.4544
        elif family_advice == 'Có, nhưng không nhiều' and row['Lĩnh vực'] == family_industry_select:
            family_score += 0.303
        elif family_advice == 'Không' and row['Lĩnh vực'] == family_industry_select:
            family_score += 0.2

        cagr = cagr_dict.get(row['Ngành'], 0)
        social_factor_score = 1 + (cagr / 100) if cagr > 0 else 0

        final_score = PF_score * 0.5702 + family_score * 0.2936 + social_factor_score * 0.1362

        suggestions.append((row['Ngành'], {
            'mbti_score': mbti_score,
            'subjects_score': subjects_score,
            'strengths_score': strengths_score,
            'interests_score': interests_score,
            'PF_score': PF_score,
            'family_score': family_score,
            'social_factor_score': social_factor_score,
            'final_score': final_score
        }))

    top_10_suggestions = sorted(suggestions, key=lambda x: x[1]['final_score'], reverse=True)[:10]
    log_top_10_career_details(top_10_suggestions)

    # Dạng FE cần hiển thị
    final_output = []
    for career, details in top_10_suggestions:
        final_output.append({
            "career": career,
            "score": f"{details['final_score'] * 100:.2f}%"
        })

    # --- Ghi vào Top10Major theo định dạng "Tên ngành: 62.77%" ---
    if supabase:
        try:
            # Nếu bảng Top10Major.chat_id là int8, ta thử cast
            chat_id_numeric = None
            try:
                chat_id_numeric = int(chat_id)
            except Exception:
                pass  # Nếu không cast được, có thể bảng dùng varchar. Tuỳ schema của bạn.

            # Xây payload "Top_i" -> "Career: 62.77%"
            top_payload = {"chat_id": chat_id_numeric if chat_id_numeric is not None else chat_id}
            for i, item in enumerate(final_output[:10], start=1):
                top_payload[f"Top_{i}"] = f"{item['career']}: {item['score']}"

            res_top = supabase.table("Top10Major").upsert(top_payload, on_conflict="chat_id").execute()
            print("[DEBUG] UPSERT Top10Major:", getattr(res_top, "data", None))
        except Exception as e:
            import traceback
            print("[ERROR] update Top10Major:", e)
            traceback.print_exc()

    return jsonify(final_output), 200


# ================== Routes ==================
@app.route("/home")
def home():
    mbti_options = sorted(data_frontend['MBTI'].dropna().unique())
    subject_combination_options = sorted(data_frontend['Tổ hợp môn'].dropna().unique())
    strengths_options = sorted(data_frontend['Khả năng và Điểm mạnh'].dropna().unique())
    interests_options = sorted(data_frontend['Sở thích và Đam mê'].dropna().unique())
    field_options = sorted(data_frontend['Lĩnh vực'].dropna().unique())

    if "username" not in session:
        return redirect(url_for("login"))
    return render_template(
        "home.html",
        username=session["username"],
        mbti_options=mbti_options,
        subject_combination_options=subject_combination_options,
        strengths_options=strengths_options,
        interests_options=interests_options,
        fields=field_options
    )

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not supabase:
            return render_template("login.html", message="❌ Supabase chưa cấu hình (check .env).")

        try:
            res = supabase.table("Account").select("chat_id,password").eq("chat_id", username).execute()
        except Exception as e:
            print("[ERROR] query Account:", e)
            res = None

        found = None
        if res and getattr(res, "data", None):
            found = res.data[0]

        if found:
            if found.get("password") == password:
                session["username"] = username
                return redirect(url_for("home"))
            else:
                return render_template("login.html", message="Sai mật khẩu.")
        else:
            return render_template("login.html", message="Không tìm thấy username.")

    return render_template("login.html")

# === Entrypoint ===
if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)
