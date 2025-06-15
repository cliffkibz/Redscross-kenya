// main.js - General purpose JavaScript for the application

// Any common functions or initializations can go here.
// For example, if you have global event listeners or UI manipulations not specific
// to auth, incidents, or resources.

// Example: A simple script to ensure navigation links are active based on current URL
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });

    // You might also want to scroll to top on page load
    window.scrollTo(0, 0);
}); 