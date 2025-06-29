document.addEventListener('DOMContentLoaded', function() {
    // Function to generate a slug from a given string
    const createSlug = (text) => {
        return text.trim()
            .toLowerCase()
            .replace(/\s+/g, '-')           // Replace spaces with -
            .replace(/[^\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\w-]+/g, '') // Remove all non-word chars except Persian
            .replace(/--+/g, '-');          // Replace multiple - with single -
    };

    // Slug generation for product forms
    const productNameField = document.querySelector('#id_name');
    const productSlugField = document.querySelector('#id_slug');

    if (productNameField && productSlugField) {
        productNameField.addEventListener('input', function() {
            productSlugField.value = createSlug(this.value);
        });
    }

    // Slug generation for blog category forms
    const categoryNameField = document.querySelector('#id_name'); // Assuming same ID for category name
    const categorySlugField = document.querySelector('#id_slug'); // Assuming same ID for category slug

    if (categoryNameField && categorySlugField && document.URL.includes('blog/categories/')) {
         categoryNameField.addEventListener('input', function() {
            categorySlugField.value = createSlug(this.value);
        });
    }

    // Slug generation for blog post forms
    const postTitleField = document.querySelector('#id_title');
    const postSlugField = document.querySelector('#id_slug');

    if (postTitleField && postSlugField) {
        postTitleField.addEventListener('input', function() {
            postSlugField.value = createSlug(this.value);
        });
    }
}); 