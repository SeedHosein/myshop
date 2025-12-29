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

    // --- Chat Pop-up Logic --- //
    const chatFabButton = document.getElementById('chat-fab');
    const chatPopupContainer = document.getElementById('chat-popup-container');
    const chatCloseButton = document.getElementById('chat-close-button');
    const chatLog = document.getElementById('chat-log');
    const messageInput = document.getElementById('chat-message-input');
    const messageSubmit = document.getElementById('chat-message-submit');

    // These variables are set in base.html's script tag
    // window.CHAT_SESSION_ID
    // window.CURRENT_USER_EMAIL
    // window.CURRENT_USER_IS_STAFF

    function formatTimestamp(isoString) {
        const date = new Date(isoString);
        return date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
    }

    function appendMessage(data) {
        const messageType = data.type;
        const messageText = data.message;
        const senderEmail = data.sender_email;
        const senderIsStaff = data.sender_is_staff;
        const timestamp = data.timestamp;
        const formattedTime = formatTimestamp(timestamp);

        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message');

        if (messageType === 'chat_message') {
            if (senderEmail === window.CURRENT_USER_EMAIL) {
                messageElement.classList.add('user-message');
            } else { // Assuming any other sender is the agent in this customer chat
                messageElement.classList.add('agent-message');
            }
            messageElement.innerHTML = `<div>${messageText}</div><span class="message-meta">${formattedTime} - ${senderEmail}</span>`;
        } else if (messageType === 'system_message') {
            messageElement.classList.add('system-message');
            messageElement.textContent = `${messageText} (${formattedTime})`;
        }
        
        chatLog.appendChild(messageElement);
        chatLog.scrollTop = chatLog.scrollHeight; // Auto-scroll to bottom
    }

    if (chatFabButton && chatPopupContainer && chatCloseButton && chatLog && messageInput && messageSubmit) {
        let chatSocket = null;

        const connectWebSocket = () => {
            if (window.CHAT_SESSION_ID && (!chatSocket || chatSocket.readyState === WebSocket.CLOSED)) {
                chatSocket = new WebSocket(
                    'ws://'
                    + window.location.host
                    + '/ws/chat/'
                    + window.CHAT_SESSION_ID
                    + '/'
                );

                chatSocket.onopen = function(e) {
                    console.log('Chat socket opened successfully');
                    // messageInput.focus();
                };

                chatSocket.onmessage = function(e) {
                    const data = JSON.parse(e.data);
                    appendMessage(data);
                };

                chatSocket.onclose = function(e) {
                    console.error('Chat socket closed unexpectedly', e);
                    // Attempt to reconnect after a delay
                    setTimeout(() => {
                        console.log("Attempting to reconnect chat socket...");
                        connectWebSocket();
                    }, 3000); // Try to reconnect every 3 seconds
                };

                chatSocket.onerror = function(e) {
                    console.error('Chat socket error:', e);
                };
            }
        };

        chatFabButton.addEventListener('click', function() {
            if (!window.CHAT_SESSION_ID) {
                alert("برای شروع گفتگو باید وارد حساب کاربری خود شوید."); // Or redirect to login
                return;
            }
            if (chatPopupContainer.classList.contains('hidden')) {
            chatPopupContainer.classList.remove('hidden'); // Make it visible for animation
            setTimeout(() => chatPopupContainer.classList.add('active'), 10); // Trigger transition
            connectWebSocket(); // Establish WebSocket connection when chat opens
            messageInput.focus();
            } else {
                chatCloseButton.click();
            }
        });

        chatCloseButton.addEventListener('click', function() {
            chatPopupContainer.classList.remove('active');
            setTimeout(() => chatPopupContainer.classList.add('hidden'), 300); // Hide after transition
            if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.close(); // Close WebSocket when chat pop-up is hidden
            }
        });

        // Close pop-up if clicking outside the content (on the overlay)
        chatPopupContainer.addEventListener('click', function(event) {
            if (event.target === chatPopupContainer) {
                chatCloseButton.click();
            }
        });

        messageInput.onkeyup = function(e) {
            if (e.key === 'Enter') {
                messageSubmit.click();
            }
        };

        messageSubmit.onclick = function(e) {
            const message = messageInput.value;
            if (message.trim() === '') return;

            if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify({
                    'message': message
                }));
                messageInput.value = '';
            } else {
                console.error("WebSocket is not open. Cannot send message.");
                alert("خطا در اتصال به چت. لطفا صفحه را رفرش کنید.");
            }
        };
    } else {
        chatFabButton.addEventListener('click', function() {
            if (!window.CHAT_SESSION_ID) {
                alert("برای شروع گفتگو باید وارد حساب کاربری خود شوید."); // Or redirect to login
                return;
            }
            if (chatPopupContainer.classList.contains('hidden')) {
            chatPopupContainer.classList.remove('hidden'); // Make it visible for animation
            setTimeout(() => chatPopupContainer.classList.add('active'), 10); // Trigger transition
            } else {
                chatCloseButton.click();
            }
        });

        chatCloseButton.addEventListener('click', function() {
            chatPopupContainer.classList.remove('active');
            setTimeout(() => chatPopupContainer.classList.add('hidden'), 300); // Hide after transition
        });

        // Close pop-up if clicking outside the content (on the overlay)
        chatPopupContainer.addEventListener('click', function(event) {
            if (event.target === chatPopupContainer) {
                chatCloseButton.click();
            }
        });
    }
});
