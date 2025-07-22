document.addEventListener('DOMContentLoaded', function() {
    // --- CSRF Token for AJAX POST Requests --- //
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
    const csrftoken = getCookie('csrftoken');

    // --- Add to Cart (from product pages) --- //
    const addToCartForms = document.querySelectorAll('.add-to-cart-form'); // Forms on product_detail, product_list etc.
    
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(form);
            const url = form.action;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest' 
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update cart item count in navbar
                    const cartItemCountElement = document.getElementById('cart-item-count');
                    if (cartItemCountElement && data.cart_total_items !== undefined) {
                        cartItemCountElement.textContent = data.cart_total_items;
                    }
                    // Show a success message (e.g., a toast notification)
                    alert(data.message || 'Product added to cart!'); // Replace with a better notification
                    console.log('Add to cart success:', data);
                } else {
                    alert(data.message || 'Error adding product to cart.'); // Replace with better error handling
                    console.error('Add to cart error:', data);
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                alert('An unexpected error occurred. Please try again.');
            });
        });
    });

    // --- Cart Detail Page AJAX (Update Quantity, Remove, Save for Later) --- //
    // This section is more complex as it involves updating parts of the cart_detail page itself.
    // For simplicity, the cart_detail.html currently uses standard form submissions for these actions.
    // To make them fully AJAX:
    // 1. Add event listeners to 'Update', 'Remove', 'Save for Later' buttons/forms.
    // 2. Prevent default form submission.
    // 3. Make fetch requests to the respective views.
    // 4. On success, update the DOM dynamically:
    //    - Change quantity displayed.
    //    - Update item subtotal.
    //    - Update cart grand total and item count.
    //    - Remove item row from the table.
    //    - Move item between active/saved lists.

    // Example: AJAX for Remove From Cart on cart_detail.html
    document.querySelectorAll('.remove-from-cart-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            if (!confirm("Are you sure you want to remove this item?")) return;

            const url = form.action;
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById(`cart-item-row-${data.removed_item_id}`)?.remove();
                    updateCartSummary(data.cart_total_items, data.cart_total_price);
                    alert(data.message);
                } else {
                    alert(data.message || 'Error removing item.');
                }
            })
            .catch(error => console.error('Fetch error:', error));
        });
    });
    
    // Example: AJAX for Update Quantity on cart_detail.html
    document.querySelectorAll('.update-quantity-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const url = form.action;
            const formData = new FormData(form);
            const itemId = form.querySelector('.quantity-input').dataset.itemId;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    document.querySelector(`.item-subtotal-${itemId}`).textContent = `${parseFloat(data.item_total_price).toFixed(0)} Toman`;
                    updateCartSummary(data.cart_total_items, data.cart_total_price);
                    alert(data.message);
                } else {
                     alert(data.message || 'Error updating quantity.');
                }
            })
            .catch(error => console.error('Fetch error:', error));
        });
    });

    function updateCartSummary(totalItems, totalPrice) {
        const cartItemCountNav = document.getElementById('cart-item-count');
        const cartSubtotalEl = document.getElementById('cart-subtotal');
        const cartGrandTotalEl = document.getElementById('cart-grand-total');

        if (cartItemCountNav) cartItemCountNav.textContent = totalItems;
        if (cartSubtotalEl) cartSubtotalEl.textContent = `${parseFloat(totalPrice).toFixed(0)} Toman`;
        if (cartGrandTotalEl) cartGrandTotalEl.textContent = `${parseFloat(totalPrice).toFixed(0)} Toman`;
    }

    // Note: Save For Later AJAX would be similar: make a POST, then on success, move the item row in the DOM.
}); 