let show = false;
const billContainer = document.getElementById('billContainer');
const arrowIcon = document.getElementById('arrowIcon');

document.getElementById('toggleArrow').addEventListener('click', function () {
    show = !show;

    // Toggle container class
    if (show) {
        billContainer.classList.remove('cart-page-bill-hide-container');
    } else {
        billContainer.classList.add('cart-page-bill-hide-container');
    }

    // Update arrow icon
    arrowIcon.className = `fa-solid ${show ? 'fa-angle-down' : 'fa-angle-up'}`;
});

const cartIncDecrBtns = document.querySelectorAll('.cart-page-product-increment-decrement-btn button')
console.log(cartIncDecrBtns)
cartIncDecrBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
        show = !show;
    })
})