document.addEventListener("DOMContentLoaded", function () {
    // --- Category Accordion Logic ---
    const categoryArrows = document.querySelectorAll(".category-item.has-children .category-arrow");
    categoryArrows.forEach(arrow => {
        arrow.addEventListener("click", () => {
            const parentItem = arrow.closest('.category-item');
            parentItem.classList.toggle("open");
        });
    });

    // --- Active Category Link Logic ---
    const filterLinks = document.querySelectorAll('.filter-link');
    filterLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.classList.contains('active')) {
                e.preventDefault();
            };
            filterLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
});