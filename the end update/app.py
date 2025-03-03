from flask import Flask, request, jsonify, render_template
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import os

# Flask app initialization
app = Flask(__name__)

# File paths
file_path_backend = './data/Sorted_Ngành_Nghề.xlsx'  # Backend data Excel file
file_path_frontend = './data/Book1.xlsx'  # Frontend data Excel file
file_path_family = './data/FamilyFactor.xlsx'
file_path_university = './data/Truong_theo_nganh.xlsx'
file_path_forecasting = './data/generate/bang_xep_hang_nganh_nghe_AAGR_2025_2028.xlsx'

# Load datasets
data_backend = pd.read_excel(file_path_backend)
data_frontend = pd.read_excel(file_path_frontend)
family_data = pd.read_excel(file_path_family)
university_data = pd.read_excel(file_path_university)
forecasting_data = pd.read_excel(file_path_forecasting)

# Function to clean and process bracketed columns
def clean_brackets(column):
    cleaned_data = []
    for entry in column:
        try:
            cleaned_data.append(" ".join(ast.literal_eval(entry)))
        except (ValueError, SyntaxError):
            cleaned_data.append(str(entry).replace("[", "").replace("]", ""))
    return cleaned_data

def clean_commas(input_data):
    """
    Tách chuỗi dữ liệu dựa trên dấu phẩy và làm sạch khoảng trắng.
    """
    if not isinstance(input_data, str):
        return []
    
    # Tách chuỗi dựa trên dấu phẩy
    elements = input_data.split(',')
    
    # Làm sạch từng phần tử và loại bỏ phần tử rỗng
    cleaned_data = [element.strip() for element in elements if element.strip()]
    
    return cleaned_data



# Ensure required columns exist, fill missing columns with empty strings
for col in ['Khả năng và Điểm mạnh', 'Sở thích và Đam mê', 'MBTI', 'Tổ hợp môn']:
    if col not in data_backend.columns:
        print(f"Warning: Column '{col}' is missing in the backend data. Adding empty placeholder.")
        data_backend[col] = ""


# Clean specific columns
data_backend['MAIN STRENGTHS'] = clean_brackets(data_backend['MAIN STRENGTHS'])
data_backend['Khả năng và Điểm mạnh'] = clean_brackets(data_backend['Khả năng và Điểm mạnh'])
data_backend['MAIN INTERESTEDS'] = clean_brackets(data_backend['MAIN INTERESTEDS'])
data_backend['Sở thích và Đam mê'] = clean_brackets(data_backend['Sở thích và Đam mê'])
university_data['Top trường đại học'] = university_data['Top trường đại học'].apply(
    lambda x: clean_commas(x) if pd.notnull(x) else []
)

# Combine relevant columns for TF-IDF processing
data_backend['Combined'] = (
    data_backend['MBTI'].fillna("") + " " +
    data_backend['Tổ hợp môn'].fillna("") + " " +
    data_backend['MAIN STRENGTHS'].fillna("") + " " +
    data_backend['Khả năng và Điểm mạnh'].fillna("") + " " +
    data_backend['MAIN INTERESTEDS'].fillna("") + " " +
    data_backend['Sở thích và Đam mê'].fillna("")
)

# Vectorize the combined data using TF-IDF
tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(data_backend['Combined'])

# Làm sạch tên cột trong DataFrame
forecasting_data.columns = forecasting_data.columns.str.strip()

# Build a CAGR lookup dictionary
cagr_dict = forecasting_data.set_index('nganh_nghe')['AAGR (%)'].to_dict()


# Xuất thông tin chi tiết ra console cho Top 10
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



# Cập nhật vòng lặp tính toán trong /submit
@app.route('/submit', methods=['POST'])
def submit():
    if request.content_type != 'application/json':
        return jsonify({"error": "Invalid content type"}), 415

    data = request.get_json()
    family_advice = data.get('family_advice', '')
    family_industry_select = data.get('family_industry_select', '')
    financial_influence = data.get('financial_influence', '')

    mbti = data.get('mbti', '').strip().upper()
    subjects = [subject.strip().upper() for subject in data.get('subjects', [])]
    mainstrengths = set(data.get('mainstrengths', []))
    strengths = set(data.get('strengths', []))
    maininterests = set(data.get('maininterests', []))
    interests = set(data.get('interests', []))

    mainstrengths_vector = tfidf_vectorizer.transform([" ".join(mainstrengths)]) if mainstrengths else None
    strengths_vector = tfidf_vectorizer.transform([" ".join(strengths)]) if strengths else None
    maininterests_vector = tfidf_vectorizer.transform([" ".join(maininterests)]) if maininterests else None
    interests_vector = tfidf_vectorizer.transform([" ".join(interests)]) if interests else None

    high_tuition_careers = family_data['Top học phí'].dropna().unique()
    top_social_careers = forecasting_data['nganh_nghe'].dropna().unique()

    suggestions = []
    for i in range(len(data_backend)):
        row = data_backend.iloc[i]
        backend_mbtis = {mbti.strip() for mbti in str(row['MBTI']).split(',')}
        mbti_score = 1.0 if mbti in backend_mbtis else 0.0

        backend_subjects = {subject.strip() for subject in str(row['Tổ hợp môn']).split(',')}
        subjects_score = 1.0 if any(subject in backend_subjects for subject in subjects) else 0.0

        main_strengths_score = cosine_similarity(mainstrengths_vector, tfidf_vectorizer.transform([row['MAIN STRENGTHS']])).flatten()[0] if mainstrengths_vector is not None else 0
        remaining_strengths_score = cosine_similarity(strengths_vector, tfidf_vectorizer.transform([row['Khả năng và Điểm mạnh']])).flatten()[0] if strengths_vector is not None else 0
        strengths_score = main_strengths_score * 0.35 + remaining_strengths_score * 0.65

        main_interests_score = cosine_similarity(maininterests_vector, tfidf_vectorizer.transform([row['MAIN INTERESTEDS']])).flatten()[0] if maininterests_vector is not None else 0
        remaining_interests_score = cosine_similarity(interests_vector, tfidf_vectorizer.transform([row['Sở thích và Đam mê']])).flatten()[0] if interests_vector is not None else 0
        interests_score = main_interests_score * 0.35 + remaining_interests_score * 0.65

        PF_score = mbti_score * 0.2391 + subjects_score * 0.2457 + strengths_score * 0.2609 + interests_score * 0.2543

        family_score = 0.5456
        if financial_influence == "Có" and row['Ngành'] in high_tuition_careers:
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

    # Chỉ lấy Top 10
    top_10_suggestions = sorted(suggestions, key=lambda x: x[1]['final_score'], reverse=True)[:10]

    # Xuất chi tiết Top 10 ra console
    log_top_10_career_details(top_10_suggestions)

    final_output = []
    for career, details in top_10_suggestions:
        # Lấy danh sách trường đại học và xử lý dấu phẩy
        matched_universities = university_data[university_data['Ngành'] == career]['Top trường đại học'].dropna().tolist()

        # Xử lý từng mục trong danh sách
        processed_universities = []
        for entry in matched_universities:
            if isinstance(entry, str):
                # Nếu là chuỗi, tách bằng dấu phẩy và làm sạch từng trường
                universities = entry.split(',')
                processed_universities.extend([univ.strip() for univ in universities if univ.strip()])
            elif isinstance(entry, list):
                # Nếu là danh sách, làm sạch từng mục
                processed_universities.extend([univ.strip() for univ in entry if isinstance(univ, str) and univ.strip()])

        # Đảm bảo kết quả cuối cùng là một danh sách sạch
        matched_universities = processed_universities

        # Debug kiểm tra kết quả
        print("✅ Matched Universities:", matched_universities)

        matched_colleges = university_data[university_data['Ngành'] == career]['Top trường Trường cao đẳng'].dropna().tolist()

        final_output.append({
            "career": career,
            "score": f"{details['final_score'] * 100:.2f}%",
            "universities": matched_universities,
            "colleges": matched_colleges
        })

    return jsonify(final_output), 200



 

@app.route('/')
def index():
    # Sắp xếp dữ liệu trước khi gửi đến giao diện
    mbti_options = sorted(data_frontend['MBTI'].dropna().unique())
    subject_combination_options = sorted(data_frontend['Tổ hợp môn'].dropna().unique())
    strengths_options = sorted(data_frontend['Khả năng và Điểm mạnh'].dropna().unique())
    interests_options = sorted(data_frontend['Sở thích và Đam mê'].dropna().unique())
    field_options = sorted(data_frontend['Lĩnh vực'].dropna().unique())

    return render_template(
        'index.html',
        mbti_options=mbti_options,
        subject_combination_options=subject_combination_options,
        strengths_options=strengths_options,
        interests_options=interests_options,
        fields=field_options
    )

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)