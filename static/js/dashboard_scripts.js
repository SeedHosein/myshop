document.addEventListener('DOMContentLoaded', function() {
    const themeSwitcher = document.getElementById('theme-switcher');
    const body = document.body;
    const themeIcon = themeSwitcher.querySelector('i');

    // Load saved theme from localStorage
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        body.classList.add(currentTheme);
        if (currentTheme === 'theme-dark') {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
    } else {
        body.classList.add('theme-light'); // Default theme
    }

    themeSwitcher.addEventListener('click', function() {
        if (body.classList.contains('theme-light')) {
            body.classList.replace('theme-light', 'theme-dark');
            themeIcon.classList.replace('fa-moon', 'fa-sun');
            localStorage.setItem('theme', 'theme-dark');
        } else {
            body.classList.replace('theme-dark', 'theme-light');
            themeIcon.classList.replace('fa-sun', 'fa-moon');
            localStorage.setItem('theme', 'theme-light');
        }
    });
}); 