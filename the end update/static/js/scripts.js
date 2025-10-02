document.addEventListener('DOMContentLoaded', function () {
    // --- State Management ---
    let currentStep = 0;
    const FORM_DATA_KEY = 'careerFormData'; // Khóa để lưu dữ liệu trong localStorage

    // --- DOM Elements ---
    const formSteps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.progress-step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const form = document.getElementById('careerForm');

    // --- LƯU VÀ TẢI DỮ LIỆU FORM ---

    /**
     * Thu thập tất cả dữ liệu từ form và lưu vào localStorage.
     */
    function saveFormData() {
        const formData = {
            family_advice: document.getElementById('family_advice')?.value || '',
            financial_influence: document.getElementById('financial_influence')?.value || '',
            family_industry: document.getElementById('family_industry')?.value || '',
            family_industry_select: document.getElementById('family_industry_select')?.value || '',
            mbti: document.getElementById('mbti')?.value || '',
            subjects: Array.from(document.querySelectorAll('input[name="subjects"]:checked')).map(cb => cb.value),
            strengths: Array.from(document.querySelectorAll('input[name="strengths"]:checked')).map(cb => cb.value),
            interests: Array.from(document.querySelectorAll('input[name="interests"]:checked')).map(cb => cb.value),
        };
        localStorage.setItem(FORM_DATA_KEY, JSON.stringify(formData));
    }

    /**
     * Tải dữ liệu từ localStorage và cập nhật giao diện form.
     */
    function loadFormData() {
        const savedData = localStorage.getItem(FORM_DATA_KEY);
        if (!savedData) return;

        const formData = JSON.parse(savedData);

        // --- CẬP NHẬT LOGIC KHÔI PHỤC BUTTON ---
        // Hàm trợ giúp mới, ổn định hơn để cập nhật button group
        const updateButtonGroup = (inputId, value) => {
            if (!value) return;
            const input = document.getElementById(inputId);
            if (!input) return;
            
            input.value = value;
            const buttonGroup = input.closest('.form-group').querySelector('.button-group');
            if (!buttonGroup) return;

            const buttons = buttonGroup.querySelectorAll('button');
            let buttonToSelect = null;

            buttons.forEach(btn => {
                btn.classList.remove('selected');
                const onclickString = btn.getAttribute('onclick') || '';
                
                // Ưu tiên 1: Tìm chính xác giá trị trong hàm setAnswer()
                if (onclickString.includes(`setAnswer('${inputId}', '${value}'`)) {
                    buttonToSelect = btn;
                }
                // Ưu tiên 2: Tìm theo text content (dự phòng)
                else if (!buttonToSelect && btn.textContent.trim() === value) {
                    buttonToSelect = btn;
                }
            });

            if (buttonToSelect) {
                buttonToSelect.classList.add('selected');
            }
        };

        const updateToggleGroup = (inputId, value) => {
            if (!value) return;
             const input = document.getElementById(inputId);
            if (!input) return;
            
            input.value = value;
            const buttonGroup = input.closest('.form-group').querySelector('.button-group');
            if (!buttonGroup) return;

            const buttons = buttonGroup.querySelectorAll('button');
            buttons.forEach(btn => {
                btn.classList.remove('selected');
                 const onclickString = btn.getAttribute('onclick') || '';
                 if (value === 'Yes' && onclickString.includes("toggleFields('yes'")){
                     btn.classList.add('selected');
                 } else if (value === 'No' && onclickString.includes("toggleFields('no'")){
                     btn.classList.add('selected');
                 }
            });
        }


        // Khôi phục các lựa chọn button
        updateButtonGroup('family_advice', formData.family_advice);
        updateButtonGroup('financial_influence', formData.financial_influence);
        
        // Xử lý riêng cho 'family_industry' vì nó có ẩn/hiện
        if (formData.family_industry) {
            updateToggleGroup('family_industry', formData.family_industry);
            const fieldsContainer = document.getElementById('fields-container_3');
            if (fieldsContainer) {
                fieldsContainer.style.display = formData.family_industry === 'Yes' ? 'block' : 'none';
                if(formData.family_industry_select) {
                    document.getElementById('family_industry_select').value = formData.family_industry_select;
                }
            }
        }

        // Khôi phục MBTI
        if (formData.mbti) {
            document.getElementById('mbti').value = formData.mbti;
        }

        // Khôi phục checkboxes
        const updateCheckboxes = (name, values) => {
            if (values && values.length > 0) {
                values.forEach(value => {
                    // Cần escape các ký tự đặc biệt trong value nếu có
                    const escapedValue = value.replace(/ /g, '-').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
                    const checkbox = document.querySelector(`input[name="${name}"][value="${value}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
            }
        };

        updateCheckboxes('subjects', formData.subjects);
        updateCheckboxes('strengths', formData.strengths);
        updateCheckboxes('interests', formData.interests);
        
        // Cập nhật lại phần hiển thị text các môn đã chọn
        updateSelectedSubjectsDisplay();
    }
    
    // --- Logic Form Nhiều Bước ---
    function showStep(stepIndex) {
        formSteps.forEach(step => step.classList.remove('active'));
        formSteps[stepIndex].classList.add('active');
        updateProgressBar(stepIndex);
        updateNavButtons(stepIndex);
    }

    function updateProgressBar(stepIndex) {
        progressSteps.forEach((step, idx) => {
            step.classList.toggle('active', idx <= stepIndex);
        });
        const progressBar = document.querySelector('.progress-bar');
        const activeSteps = document.querySelectorAll('.progress-step.active');
        const width = ((activeSteps.length - 1) / (progressSteps.length - 1)) * 100;
        progressBar.style.setProperty('--progress-width', `${width}%`);
    }

    function updateNavButtons(stepIndex) {
        prevBtn.style.display = stepIndex === 0 ? 'none' : 'inline-block';
        if (stepIndex === formSteps.length - 1) {
            nextBtn.textContent = 'Get Results';
            validateForm();
        } else {
            nextBtn.textContent = 'Next';
            nextBtn.disabled = false;
        }
    }
    
    showStep(currentStep);

    // --- Event Listeners ---
    nextBtn.addEventListener('click', () => {
        if (currentStep < formSteps.length - 1) {
            currentStep++;
            showStep(currentStep);
        } else {
            form.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });

    prevBtn.addEventListener('click', () => {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
        }
    });
    
    form.addEventListener('change', saveFormData);

    // --- Logic Accordion ---
    const accordions = document.querySelectorAll('.accordion-header');
    accordions.forEach(accordion => {
        accordion.addEventListener('click', () => {
            const content = accordion.nextElementSibling;
            content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
        });
    });
    
    // --- Các hàm gốc (cho onclick nội tuyến) ---
    window.setAnswer = function (inputId, value, button) {
        const inputElement = document.getElementById(inputId);
        if (!inputElement) return;
        inputElement.value = value;
        const buttons = button.closest('.button-group').querySelectorAll('button');
        buttons.forEach(btn => btn.classList.remove('selected'));
        button.classList.add('selected');
        saveFormData();
    };

    window.toggleFields = function (option, inputId, button) {
        const fieldsContainer = document.getElementById('fields-container_3');
        if (!fieldsContainer) return;
        window.setAnswer(inputId, option === 'yes' ? 'Yes' : 'No', button);
        fieldsContainer.style.display = option === 'yes' ? 'block' : 'none';
    };

    // --- Cập nhật hiển thị môn học đã chọn ---
    const subjectCheckboxes = document.querySelectorAll('input[name="subjects"]');
    const selectedSubjectsSpan = document.getElementById('selected-subjects');

    function updateSelectedSubjectsDisplay() {
         const selected = Array.from(subjectCheckboxes)
                                .filter(i => i.checked)
                                .map(i => i.value);
        selectedSubjectsSpan.textContent = selected.length > 0 ? selected.join(', ') : 'None';
    }

    subjectCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedSubjectsDisplay);
    });

    // --- Logic Gửi Form ---
    form.addEventListener('submit', function (event) {
        event.preventDefault();
        
        if (confirm('Are you sure you want to submit your information for suggestions?')) {
            // ... (phần còn lại của hàm gửi form giữ nguyên)
            const allStrengths = Array.from(document.querySelectorAll('input[name="strengths"]:checked')).map(input => input.value);
            const allInterests = Array.from(document.querySelectorAll('input[name="interests"]:checked')).map(input => input.value);

            const data = {
                family_advice: document.getElementById('family_advice')?.value || '',
                financial_influence: document.getElementById('financial_influence')?.value || '',
                family_industry: document.getElementById('family_industry')?.value || '',
                family_industry_select: document.getElementById('family_industry_select')?.value || '',
                mbti: document.getElementById('mbti')?.value || '',
                subjects: Array.from(document.querySelectorAll('input[name="subjects"]:checked')).map(input => input.value),
                mainstrengths: allStrengths.slice(0, 2),
                strengths: allStrengths,
                maininterests: allInterests.slice(0, 2),
                interests: allInterests,
            };

            localStorage.removeItem(FORM_DATA_KEY);
            form.style.display = 'none';
            const resultsContainer = document.getElementById('results');
            resultsContainer.innerHTML = '<div class="loading">⏳ Analyzing and generating the best suggestions for you...</div>';

            fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(responseData => {
                displayResults(responseData);
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                resultsContainer.innerHTML = '<div class="error">❌ An error occurred during processing. Please try again.</div>';
            });
        }
    });

    // --- Logic Xác thực Form ---
    function validateForm() {
        const mbtiSelected = document.getElementById('mbti').value !== '';
        const subjectsChecked = Array.from(document.querySelectorAll('input[name="subjects"]:checked')).length > 0;
        const strengthsChecked = Array.from(document.querySelectorAll('input[name="strengths"]:checked')).length > 0;
        const interestsChecked = Array.from(document.querySelectorAll('input[name="interests"]:checked')).length > 0;

        nextBtn.disabled = !(mbtiSelected && subjectsChecked && strengthsChecked && interestsChecked);
    }
    
    form.addEventListener('change', () => {
        if (currentStep === formSteps.length - 1) {
            validateForm();
        }
    });

    // --- Hàm Hiển thị Kết quả ---
    function displayResults(data) {
        // ... (hàm này giữ nguyên)
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = '';
        const header = document.createElement('h2');
        header.textContent = 'Here are the suggestions for you';
        resultsContainer.appendChild(header);
        if (!data || data.length === 0) {
            const noResultMessage = document.createElement('p');
            noResultMessage.className = 'error';
            noResultMessage.textContent = 'Sorry, no suitable suggestions were found based on your choices.';
            resultsContainer.appendChild(noResultMessage);
            return;
        }
        const gridContainer = document.createElement('div');
        gridContainer.className = 'results-grid';
        resultsContainer.appendChild(gridContainer);
        data.forEach(item => {
            const resultCard = document.createElement('div');
            resultCard.className = 'result-card';
            const scoreHTML = `<div class="score-badge">${item.score}</div>`;
            const careerHTML = `<h3>${item.career}</h3>`;
            resultCard.innerHTML = scoreHTML + careerHTML;
            gridContainer.appendChild(resultCard);
        });
    }

    // --- GỌI HÀM TẢI DỮ LIỆU KHI TRANG SẴN SÀNG ---
    loadFormData();
});