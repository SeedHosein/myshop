// This is a placeholder for base_scripts.js
console.log("base_scripts.js loaded"); 
document.addEventListener('DOMContentLoaded', function () {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileNav = document.getElementById('mobile-nav');

    if (mobileMenuButton && mobileNav) {
        mobileMenuButton.addEventListener('click', function () {
            mobileNav.classList.toggle('hidden');
        });
    }
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


    const alerts = document.querySelectorAll('.messages .alert');

    alerts.forEach(function (alert) {
        // Set a 5-second timer for automatic closing
        const autoCloseTimer = setTimeout(function () {
            closeAlert(alert);
        }, 5000);

        // If the user hits the close button, cancel the timer and close.
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                clearTimeout(autoCloseTimer);
                closeAlert(alert);
            });
        }
    });

    // Exit animation and removal from DOM
    function closeAlert(alertElement) {
        alertElement.style.animation = 'slideUp 0.4s ease-out forwards';
        alertElement.addEventListener('animationend', function () {
            if (alertElement.parentNode) {
                alertElement.parentNode.removeChild(alertElement);
            }
        });
    }
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideUp {
            to {
                opacity: 0;
                transform: translateY(-30px);
            }
        }
    `;
    document.head.appendChild(style);


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
});