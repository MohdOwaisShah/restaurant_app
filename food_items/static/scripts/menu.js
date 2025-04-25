
document.addEventListener('DOMContentLoaded', function () {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const sidebarClose = document.getElementById('sidebarClose');
    const mainContent = document.getElementById('mainContent');

    // Function to open sidebar
    function openSidebar() {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
        const mainContent = document.getElementById('mainContent');
        document.body.style.overflow = 'hidden'; // Prevent body scroll
    }

    // Function to close sidebar
    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        mainContent.classList.remove('blur');
        document.body.style.overflow = ''; // Restore body scroll
    }

    // Event listeners
    menuToggle.addEventListener('click', openSidebar);
    sidebarClose.addEventListener('click', closeSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);

    // Keep the profile dropdown functionality
    const profileIcon = document.getElementById('profileIcon');
    const profileInfo = document.getElementById('profileInfo');

    profileIcon.addEventListener('click', function (e) {
        e.stopPropagation();
        profileInfo.classList.toggle('show');
    });

    document.addEventListener('click', function (e) {
        if (!profileInfo.contains(e.target) && !profileIcon.contains(e.target)) {
            profileInfo.classList.remove('show');
        }
    });
});
$(document).ready(function () {
    // Initially hide all category sections
    $('.category-section').hide();
    $('.back-button').hide();

    // Category click handling
    $('.category-item').click(function () {
        const categoryId = $(this).data('category');

        // Hide category circles,home-main-product-container and show back button
        $('.category-circles').slideUp();
        $('.home-main-product-container').slideUp();
        $('.back-button').slideDown();

        // Hide all sections and show the selected one
        $('.category-section').hide();
        $(`#${categoryId}-section`).show();

        // Add active class to selected category
        $('.category-item').removeClass('active');
        $(this).addClass('active');

        // Hide search bar when showing category items
        $('.search-container').slideUp();
    });

    // Back button handling
    $('.back-button').click(function () {
        // Show category circles,home-main-product-container and hide back button
        $('.category-circles').slideDown();
        $('.home-main-product-container').slideDown();
        $(this).slideUp();

        // Hide all category sections
        $('.category-section').hide();

        // Show search bar
        $('.search-container').slideDown();

        // Remove active class from categories
        $('.category-item').removeClass('active');
    });

    // Search functionality for menu items 
    $('.search-input').on('input', function () {
        const searchTerm = $(this).val().toLowerCase();
        $('.menu-item').each(function () {
            const itemText = $(this).text().toLowerCase();
            $(this).toggle(itemText.includes(searchTerm));
        });
    });

    // Search functionality for categories
    $('.search-input').on('input', function () {
        const searchTerm = $(this).val().toLowerCase();
        $('.category-item').each(function () {
            const itemText = $(this).text().toLowerCase();
            $(this).toggle(itemText.includes(searchTerm));
        });
    });
});
document.addEventListener('DOMContentLoaded', function () {
    // Get current page URL
    const currentPath = window.location.pathname;

    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');

        // Add active class if href matches current path
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });
});


// ---------------------------------------------------------



document.addEventListener('DOMContentLoaded', function () {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const sidebarClose = document.getElementById('sidebarClose');
    const mainContent = document.getElementById('mainContent');

    function openSidebar() {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        mainContent.classList.remove('blur');
        document.body.style.overflow = '';
    }

    menuToggle.addEventListener('click', openSidebar);
    sidebarClose.addEventListener('click', closeSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);

    const profileIcon = document.getElementById('profileIcon');
    const profileInfo = document.getElementById('profileInfo');

    profileIcon.addEventListener('click', function (e) {
        e.stopPropagation();
        profileInfo.classList.toggle('show');
    });

    document.addEventListener('click', function (e) {
        if (!profileInfo.contains(e.target) && !profileIcon.contains(e.target)) {
            profileInfo.classList.remove('show');
        }
    });

    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });
});

$(document).ready(function () {
    $('.category-section').hide();
    $('.back-button').hide();

    $('.category-item').click(function () {
        const categoryId = $(this).data('category');
        $('.category-circles').slideUp();
        $('.back-button').slideDown();
        $('.category-section').hide();
        $(`#${categoryId}-section`).show();
        $('.category-item').removeClass('active');
        $(this).addClass('active');
        $('.search-container').slideUp();
    });

    $('.back-button').click(function () {
        $('.category-circles').slideDown();
        $(this).slideUp();
        $('.category-section').hide();
        $('.search-container').slideDown();
        $('.category-item').removeClass('active');
    });

    $('.search-input').on('input', function () {
        const searchTerm = $(this).val().toLowerCase();
        $('.menu-item').each(function () {
            const itemText = $(this).text().toLowerCase();
            $(this).toggle(itemText.includes(searchTerm));
        });
        $('.category-item').each(function () {
            const itemText = $(this).text().toLowerCase();
            $(this).toggle(itemText.includes(searchTerm));
        });
    });
});

let currentItemId = null;
let basePrice = 0;
let quantity = 1;

function showAddons(itemId, itemName, itemPrice, itemImage, itemDescription) {
    currentItemId = itemId;
    basePrice = itemPrice;
    quantity = 1;

    document.querySelector('.selected-item-name').textContent = itemName;
    document.querySelector('.selected-item-price').textContent = `₹${itemPrice}`;
    document.querySelector('.selected-item-description').textContent = itemDescription || 'No description available';

    const imageEl = document.querySelector('.selected-item-image');
    if (itemImage) {
        imageEl.src = itemImage;
        imageEl.style.display = 'block';
    } else {
        imageEl.style.display = 'none';
    }

    document.querySelector('.quantity').textContent = quantity;

    fetch(`/get-addons/${itemId}/`)
        .then(response => response.json())
        .then(data => {
            const addonsContainer = document.querySelector('.addons-container');
            addonsContainer.innerHTML = '';

            data.addons.forEach(addon => {
                const addonHtml = `
                    <div class="addon-item">
                        <label class="addon-checkbox">
                            <div>
                                <input type="checkbox" 
                                    class="addon-checkbox-input" 
                                    data-price="${addon.price}"
                                    data-id="${addon.id}">
                                <span class="addon-name">${addon.name}</span>
                            </div>
                            <span class="addon-price">+₹${addon.price}</span>
                        </label>
                    </div>
                `;
                addonsContainer.innerHTML += addonHtml;
            });

            document.querySelectorAll('.addon-checkbox-input').forEach(checkbox => {
                checkbox.addEventListener('change', updateTotalPrice);
            });

            updateTotalPrice();

            const modal = new bootstrap.Modal(document.getElementById('addonsModal'));
            modal.show();
        });
}

function updateQuantity(change) {
    quantity = Math.max(1, quantity + change);
    document.querySelector('.quantity').textContent = quantity;
    updateTotalPrice();
}

function updateTotalPrice() {
    let total = basePrice * quantity;
    document.querySelectorAll('.addon-checkbox-input:checked').forEach(checkbox => {
        total += parseFloat(checkbox.dataset.price) * quantity;
    });
    document.querySelector('.total-price').textContent = total.toFixed(2);
}

document.getElementById('confirmAddToCart').addEventListener('click', function () {
    const selectedAddons = Array.from(document.querySelectorAll('.addon-checkbox-input:checked'))
        .map(checkbox => ({
            id: checkbox.dataset.id,  // e.g., "1" for Salad
            name: checkbox.nextElementSibling.textContent,  // e.g., "Salad"
            price: parseFloat(checkbox.dataset.price)  // e.g., 10.0
        }));

    console.log('Adding to cart:', { itemId: currentItemId, quantity: quantity, addons: selectedAddons });

    fetch(`/add-to-cart/${currentItemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            addons: selectedAddons,
            quantity: quantity
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('addonsModal')).hide();
                updateCartCount(data.cart_count);
                // showNotification('Item added to cart!');

            } else {
                showNotification(`Error adding item to cart: ${data.error || 'Unknown error'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            showNotification(`Error adding item to cart: ${error.message}`, 'error');
        });
});

function updateCartCount(count) {
    const cartCountElements = document.querySelectorAll('.cart-count, .bottom-nav-cart-count');
    cartCountElements.forEach(element => {
        element.textContent = count;
    });
}

function showNotification(message, type = 'success') {
    alert(message);
}

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