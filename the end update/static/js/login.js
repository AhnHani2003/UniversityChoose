// static/js/login.js
document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const scrollDown = document.querySelector(".scroll-down");
    let isOpened = false;

    window.addEventListener("scroll", () => {
        // Khi cuộn qua 1/3 chiều cao màn hình thì mở form
        if (window.scrollY > window.innerHeight / 3 && !isOpened) {
            isOpened = true;
            if (scrollDown) {
                scrollDown.style.display = "none";
            }
            // Thêm class để hiện form
            body.classList.add("is-loaded");
            // Thêm class để zoom ảnh nền
            body.classList.add("background-zoomed");
        }
    });
});