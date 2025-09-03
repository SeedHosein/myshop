document.addEventListener("DOMContentLoaded", function () {
    // --- Product Gallery Logic ---
    const mainImage = document.getElementById('main-product-image');
    const mainVideo = document.getElementById('main-product-video');
    const thumbnails = document.querySelectorAll('.thumbnail-item');

    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            thumbnails.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const type = this.dataset.type;
            const src = this.dataset.src;

            if (type === 'image') {
                mainImage.src = src;
                mainImage.classList.remove('hidden');
                mainVideo.classList.add('hidden');
                mainVideo.src = ''; // Stop video from playing in background
            } else if (type === 'video') {
                mainVideo.src = src;
                mainVideo.classList.remove('hidden');
                mainImage.classList.add('hidden');
            }
        });
    });

    // --- Star Rating Display & Input ---
    // Display average rating
    document.querySelectorAll('.star-rating-display').forEach(starDisplay => {
        const rating = parseFloat(starDisplay.dataset.rating);
        const percentage = (rating / 5) * 100;
        starDisplay.querySelector('.star-rating-display-filled').style.width = `${percentage+(percentage/100)}%`;
    });

    // Handle star rating input
    const starRatingInput = document.querySelector('.star-rating-input');
    if (starRatingInput) {
        const stars = starRatingInput.querySelectorAll('i');
        const ratingValueInput = document.getElementById('rating-value');

        stars.forEach(star => {
            star.addEventListener('click', function() {
                const ratingValue = this.dataset.value;
                ratingValueInput.value = ratingValue;
                stars.forEach(s => {
                    s.classList.toggle('selected', s.dataset.value <= ratingValue);
                });
            });
            star.addEventListener('mouseover', function() {
                stars.forEach(s => {
                    s.style.color = s.dataset.value <= this.dataset.value ? '#facc15' : '#d1d5db';
                });
            });
        });
        starRatingInput.addEventListener('mouseout', function() {
            const currentRating = ratingValueInput.value;
            stars.forEach(s => {
                s.style.color = s.dataset.value <= currentRating ? '#facc15' : '#d1d5db';
            });
        });
    }


    const variant_options = document.querySelectorAll('.variant-option');
    const variant_name = document.getElementById('variant-name');

    variant_options.forEach(variant_option => {
        variant_option.addEventListener('click', function() {
            variant_options.forEach(vo => vo.classList.remove('variant-selected'));
            if (variant_name && variant_option.dataset.variantName) {
                variant_name.textContent = variant_option.dataset.variantName;
            };
            variant_option.classList.add('variant-selected');
        });
    });


    // --- Product Details Tabs Logic ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabLinks.forEach(link => {
        link.addEventListener('click', function() {
            const tabId = this.dataset.tab;

            // Deactivate all links and panels
            tabLinks.forEach(l => l.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));

            // Activate the clicked link and corresponding panel
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });


    // --- Add to Cart Logic ---
    const cartContainers = document.querySelectorAll('.add-to-cart-container');
    const csrftoken = getCookie('csrftoken'); // Assuming getCookie is in base_scripts.js

    cartContainers.forEach(container => {
        const productId = container.dataset.productId;
        const productStock = parseInt(container.dataset.productStock);
        const addUrl = container.dataset.addUrl;

        let RemoveUrl = container.dataset.removeUrl;
        let UpdateUrl = container.dataset.updateUrl;
        const baseRemoveUrl = container.dataset.baseRemoveUrl;
        const baseUpdateUrl = container.dataset.baseUpdateUrl;

        const addButton = container.querySelector('.btn-add-to-cart');
        const quantityController = container.querySelector('.quantity-controller');
        const plusBtn = quantityController.querySelector('.plus');
        const minusBtn = quantityController.querySelector('.minus');
        const trashBtn = quantityController.querySelector('.trash-btn');
        const quantityValue = quantityController.querySelector('.quantity-value');

        addButton.addEventListener('click', async () => {
            const item_id = await handleCartUpdate(addUrl, { product_id: productId, quantity: 1 }, container, 1);
            console.log(item_id);
            if (item_id && (item_id != "error")) {
                RemoveUrl = baseRemoveUrl + item_id + "/";
                UpdateUrl = baseUpdateUrl + item_id + "/";
                console.log("UpdateUrl", UpdateUrl);
            }
        });

        plusBtn.addEventListener('click', async () => {
            let currentQuantity = parseInt(quantityValue.textContent);
            if (currentQuantity < productStock) {
                const newQuantity = currentQuantity + 1;
                await handleCartUpdate(UpdateUrl, { product_id: productId, quantity: newQuantity }, container, newQuantity);
            }
        });

        minusBtn.addEventListener('click', async () => {
            let currentQuantity = parseInt(quantityValue.textContent);
            if (currentQuantity > 1) {
                const newQuantity = currentQuantity - 1;
                await handleCartUpdate(UpdateUrl, { product_id: productId, quantity: newQuantity }, container, newQuantity);
            } else {
                const item_id = await handleCartUpdate(RemoveUrl, { product_id: productId }, container, 0);
                if (!item_id) {
                    RemoveUrl = baseRemoveUrl;
                    UpdateUrl = baseUpdateUrl;
                    console.log("UpdateUrl", UpdateUrl);
                }
            }
        });
        
        trashBtn.addEventListener('click', async () => {
            const item_id = await handleCartUpdate(RemoveUrl, { product_id: productId }, container, 0);
            if (!item_id) {
                RemoveUrl = baseRemoveUrl;
                UpdateUrl = baseUpdateUrl;
                console.log("UpdateUrl", UpdateUrl);
            }
        });
    });

    async function handleCartUpdate(url, bodyData, container, newQuantity) {
        const formData = new FormData();
        for (const key in bodyData) {
            formData.append(key, bodyData[key]);
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();

            if (data.status === 'success') {
                updateCartUI(container, newQuantity);
                updateNavbarCartCount(data.cart_total_items);
                return data.item_id; // Correctly returns the value after fetch is done
            } else {
                alert(data.message || 'خطایی رخ داد.');
                return "error";
            }
        } catch (error) {
            console.error('Error:', error);
            return "error";
        }
    }

    function updateCartUI(container, quantity) {
        const quantityValue = container.querySelector('.quantity-value');
        if (quantity > 0) {
            container.classList.add('in-cart');
            quantityValue.textContent = quantity;
        } else {
            container.classList.remove('in-cart');
            quantityValue.textContent = 1; // Reset for next time
        }
    }

    function updateNavbarCartCount(totalItems) {
        const cartCountElement = document.getElementById('cart-item-count');
        if (cartCountElement) {
            cartCountElement.textContent = totalItems;
        }
    }

    // Helper function to get CSRF token (should be in your base script)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});