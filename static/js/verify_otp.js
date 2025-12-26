const countdownElement = document.getElementById('countdown');
const resendBtn = document.getElementById('resend-btn');

const timer = setInterval(() => {
    timeLeft--;
    const minutes = String(Math.floor(timeLeft / 60)).padStart(2, '0');
    const seconds = String(timeLeft % 60).padStart(2, '0');
    countdownElement.textContent = `${minutes}:${seconds}`;

    if (timeLeft <= 0) {
        clearInterval(timer);
        countdownElement.textContent = "00:00";
        resendBtn.disabled = false;
        resendBtn.classList.add('enabled');
        resendBtn.textContent = "بازگشت به ثبت‌نام";
    }
}, 1000);

// Autofocus to next input
const inputs = document.querySelectorAll('.otp-input');

inputs.forEach((input, index) => {
    input.addEventListener('input', (e) => {
        // Just accept the number.
        e.target.value = e.target.value.replace(/[^0-9]/g, '');

        if (e.target.value && index < inputs.length - 1) {
            inputs[index + 1].focus();
        }
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !e.target.value && index > 0) {
            inputs[index - 1].focus();
        }
    });

    // Initial focus on the first input
    if (index === 0) input.focus();
});
