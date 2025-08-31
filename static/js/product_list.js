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


    // --- Price Range Slider Logic ---
    const rangeMinInput = document.querySelector(".price-range-min");
    const rangeMaxInput = document.querySelector(".price-range-max");
    const numberMinInput = document.getElementById("min-price");
    const numberMaxInput = document.getElementById("max-price");
    const progress = document.querySelector(".price-slider-progress");
    
    const priceGap = 100000; // Minimum gap between min and max price

    function updateSliderProgress() {
        const minVal = parseInt(rangeMinInput.value);
        const maxVal = parseInt(rangeMaxInput.value);
        const range = parseInt(rangeMaxInput.max) - parseInt(rangeMaxInput.min);

        const rightPercent = ((minVal - rangeMinInput.min) / range) * 100;
        const leftPercent = 100 - ((maxVal - rangeMinInput.min) / range) * 100;
        
        progress.style.right = rightPercent + "%";
        progress.style.left = leftPercent + "%";
    }

    function updateNumberInputs() {
        numberMinInput.value = rangeMinInput.value;
        numberMaxInput.value = rangeMaxInput.value;
    }

    if (rangeMinInput && rangeMaxInput && progress) {
        updateSliderProgress(); // Initial update

        [rangeMinInput, rangeMaxInput].forEach(input => {
            input.addEventListener("input", () => {
                let minVal = parseInt(rangeMinInput.value);
                let maxVal = parseInt(rangeMaxInput.value);

                if (maxVal - minVal < priceGap) {
                    if (input.classList.contains("price-range-min")) {
                        rangeMinInput.value = maxVal - priceGap;
                    } else {
                        rangeMaxInput.value = minVal + priceGap;
                    }
                }
                updateSliderProgress();
                updateNumberInputs();
            });
        });

        [numberMinInput, numberMaxInput].forEach(input => {
            input.addEventListener("change", () => {
                let minVal = parseInt(numberMinInput.value);
                let maxVal = parseInt(numberMaxInput.value);

                if (maxVal >= minVal + priceGap && maxVal <= rangeMaxInput.max && minVal >= rangeMinInput.min) {
                     rangeMinInput.value = minVal;
                     rangeMaxInput.value = maxVal;
                     updateSliderProgress();
                }
            });
        });
    }

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