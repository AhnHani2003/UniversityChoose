// Đảm bảo DOM được tải đầy đủ trước khi chạy script
document.addEventListener('DOMContentLoaded', function () {
  // ===================== Helpers UI =====================
  // Gắn hàm vào window để dùng qua onclick cho Câu 1 (giữ nguyên theo HTML của bạn)
  window.setAnswer = function (inputId, value, button) {
    const inputElement = document.getElementById(inputId);
    if (!inputElement) {
      console.error(`Không tìm thấy phần tử với ID: ${inputId}`);
      return;
    }
    inputElement.value = value;

    // Đổi màu cho nút đã chọn
    if (button && button.parentElement) {
      const buttons = button.parentElement.querySelectorAll('button');
      buttons.forEach(btn => btn.classList.remove('selected'));
      button.classList.add('selected');
    }
  };

  // option: "yes" | "no" -> ẩn/hiện lĩnh vực gia đình + lưu vào input hidden (yes/no)
  window.toggleFields = function (option, inputId, button) {
    const fieldsContainer = document.getElementById('fields-container_3'); // khu chọn lĩnh vực gia đình
    const inputElement = document.getElementById(inputId);

    if (!inputElement) {
      console.error('Không tìm thấy input ẩn để lưu yes/no:', inputId);
      return;
    }

    // đổi trạng thái nút
    if (button && button.parentElement) {
      const buttons = button.parentElement.querySelectorAll('button');
      buttons.forEach(btn => btn.classList.remove('selected'));
      button.classList.add('selected');
    }

    // chỉ hiển thị #fields-container_3 khi toggle của family_has_industry = yes
    if (option === 'yes') {
      if (fieldsContainer && inputId === 'family_has_industry') fieldsContainer.style.display = 'block';
      inputElement.value = 'yes';
    } else {
      if (fieldsContainer && inputId === 'family_has_industry') fieldsContainer.style.display = 'none';
      inputElement.value = 'no';
    }
  };

  // Nếu bạn dùng .answer-button / .toggle-field-button qua data-attr
  const answerButtons = document.querySelectorAll('.answer-button');
  answerButtons.forEach(button => {
    button.addEventListener('click', function () {
      const inputId = button.dataset.input;
      const value   = button.dataset.value;
      setAnswer(inputId, value, button);
    });
  });

  const toggleFieldButtons = document.querySelectorAll('.toggle-field-button');
  toggleFieldButtons.forEach(button => {
    button.addEventListener('click', function () {
      const inputId = button.dataset.input; // 'financial_influence' hoặc 'family_has_industry'
      const value   = button.dataset.value; // "yes" | "no"
      toggleFields(value, inputId, button);
    });
  });

  // ===================== Lấy dữ liệu từ UI =====================
  function getSelectedMBTI() {
    const el = document.getElementById('mbti');
    return el ? el.value : '';
  }
  function getSelectedSubjects() {
    return Array.from(document.querySelectorAll('input[name="subjects"]:checked')).map(i => i.value);
  }
  function getSelectedStrengths() {
    return Array.from(document.querySelectorAll('input[name="strengths"]:checked')).map(i => i.value);
  }
  function getSelectedInterests() {
    return Array.from(document.querySelectorAll('input[name="interests"]:checked')).map(i => i.value);
  }
  // nếu bạn có nhóm "chính" trong HTML thì các hàm này sẽ lấy; không có thì trả mảng rỗng
  function getMainStrengths() {
    return Array.from(document.querySelectorAll('input[name="mainstrengths"]:checked')).map(i => i.value);
  }
  function getMainInterests() {
    return Array.from(document.querySelectorAll('input[name="maininterests"]:checked')).map(i => i.value);
  }

  // Hai input ẩn yes/no
  function getFinancialInfluence() {
    const el = document.getElementById('financial_influence'); // hidden
    return el ? (el.value || 'no') : 'no';
  }
  function getFamilyHasIndustry() {
    const el = document.getElementById('family_has_industry'); // hidden
    return el ? (el.value || 'no') : 'no';
  }

  function getFamilyIndustrySelect() {
    const el = document.getElementById('family_industry_select'); // select ngành gia đình
    return el ? el.value : '';
  }
  function getFamilyAdviceDetail() {
    // Câu 1 (Có/Có, nhưng không nhiều/Không) lưu text tiếng Việt
    const el = document.getElementById('family_advice');
    return el ? el.value : '';
  }

  // ===================== Validate để bật/tắt nút Lưu & Gợi ý =====================
  function validateForm() {
    const mbtiSelect      = document.getElementById('mbti');
    const subjectsInputs  = document.querySelectorAll('input[name="subjects"]');
    const strengthsInputs = document.querySelectorAll('input[name="strengths"]');
    const interestsInputs = document.querySelectorAll('input[name="interests"]');
    const buttonSave      = document.getElementById('save');

    if (!mbtiSelect || !buttonSave) {
      console.error('Không tìm thấy phần tử cần thiết để xác thực.');
      return;
    }

    const mbtiSelected     = mbtiSelect.value !== '';
    const subjectsChecked  = Array.from(subjectsInputs).some(input => input.checked);
    const strengthsChecked = Array.from(strengthsInputs).some(input => input.checked);
    const interestsChecked = Array.from(interestsInputs).some(input => input.checked);

    buttonSave.disabled = !(mbtiSelected && subjectsChecked && strengthsChecked && interestsChecked);
  }

  // Lắng nghe sự kiện thay đổi để xác thực
  const mbtiSelectEl       = document.getElementById('mbti');
  const subjectsInputsAll  = document.querySelectorAll('input[name="subjects"]');
  const strengthsInputsAll = document.querySelectorAll('input[name="strengths"]');
  const interestsInputsAll = document.querySelectorAll('input[name="interests"]');

  if (mbtiSelectEl) mbtiSelectEl.addEventListener('change', validateForm);
  subjectsInputsAll.forEach(input  => input.addEventListener('change', validateForm));
  strengthsInputsAll.forEach(input => input.addEventListener('change', validateForm));
  interestsInputsAll.forEach(input => input.addEventListener('change', validateForm));

  // Chạy lần đầu để set trạng thái nút
  validateForm();

  // ===================== Render kết quả Top 10 =====================
  function displayResults(data) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // clear

    const label = document.createElement('h3');
    label.textContent = 'Kết quả';
    label.style.textAlign = 'center';
    resultsContainer.appendChild(label);

    const card = document.createElement('div');
    card.style.border = '1px solid #ccc';
    card.style.padding = '20px';
    card.style.borderRadius = '8px';
    card.style.backgroundColor = '#f9f9f9';
    card.style.width = '50%';
    card.style.margin = '30px auto';
    card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';

    (data || []).forEach(item => {
      const row = document.createElement('div');
      row.style.display = 'flex';
      row.style.width = '100%';
      row.style.justifyContent = 'space-between';
      row.style.alignItems = 'center';
      row.style.padding = '10px 0';
      row.style.borderBottom = '1px solid #ddd';

      const careerCell = document.createElement('div');
      careerCell.textContent = item.career;
      careerCell.style.flex = '3';
      careerCell.style.textAlign = 'left';
      careerCell.style.paddingRight = '10px';

      const scoreCell = document.createElement('div');
      scoreCell.textContent = item.score;
      scoreCell.style.flex = '2';
      scoreCell.style.textAlign = 'center';

      row.appendChild(careerCell);
      row.appendChild(scoreCell);
      card.appendChild(row);
    });

    resultsContainer.appendChild(card);
  }

  // ===================== Gọi API /save khi bấm nút =====================
  const saveBtn = document.getElementById('save');   // <button type="button" id="save">Lưu & Gợi ý</button>
  const msgBox  = document.getElementById('saveMsg'); // tuỳ chọn: <div id="saveMsg"></div>

  async function saveAndRecommend() {
    // payload KHÔNG gửi save_only -> backend sẽ cập nhật DB + trả Top 10
    const payload = {
      mbti: getSelectedMBTI(),
      subjects: getSelectedSubjects(),
      strengths: getSelectedStrengths(),
      interests: getSelectedInterests(),
      // nhóm "chính" (nếu có trong UI)
      mainstrengths: getMainStrengths(),
      maininterests: getMainInterests(),
      // yes/no từ hidden
      financial_influence: getFinancialInfluence(), // "yes" | "no"
      family_has_industry: getFamilyHasIndustry(),  // "yes" | "no"
      // thông tin thêm
      family_industry_select: getFamilyIndustrySelect(),
      family_advice: getFamilyAdviceDetail()
    };

    // Nếu yêu cầu bắt buộc chọn lĩnh vực khi có industry:
    if (payload.family_has_industry === 'yes' && !payload.family_industry_select) {
      if (msgBox) msgBox.textContent = 'Vui lòng chọn lĩnh vực của gia đình.';
      return;
    }

    try {
      if (saveBtn) saveBtn.disabled = true;
      if (msgBox) msgBox.textContent = 'Đang xử lý...';

      const res = await fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      let data = null;
      try { data = await res.json(); } catch (_) {}

      if (!res.ok) {
        if (msgBox) msgBox.textContent = '❌ Lỗi máy chủ' + (data?.error ? `: ${data.error}` : '');
        console.error('Server error:', data);
        return;
      }

      // Trường hợp đúng kỳ vọng: /save trả về MẢNG kết quả top 10
      if (Array.isArray(data)) {
        if (msgBox) msgBox.textContent = '✅ Đã lưu hồ sơ & tạo gợi ý.';
        displayResults(data);
      } else if (data && data.ok) {
        // fallback nếu backend chỉ trả "ok" (ít gặp)
        if (msgBox) msgBox.textContent = '✅ ' + (data.message || 'Đã lưu hồ sơ.');
      } else {
        if (msgBox) msgBox.textContent = '❌ Phản hồi không đúng định dạng.';
        console.warn('Unexpected response:', data);
      }
    } catch (e) {
      if (msgBox) msgBox.textContent = '❌ Lỗi mạng khi lưu & gợi ý.';
      console.error(e);
    } finally {
      if (saveBtn) saveBtn.disabled = false;
      if (msgBox) setTimeout(() => (msgBox.textContent = ''), 3000);
    }
  }

  if (saveBtn) {
    // Nút là type="button", không cần chặn submit form
    saveBtn.addEventListener('click', saveAndRecommend);
  }
});
