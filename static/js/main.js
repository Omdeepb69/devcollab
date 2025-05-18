// Basic JavaScript for DevCollab

document.addEventListener('DOMContentLoaded', function() {
    // Example function to handle form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Prevent default form submission
            event.preventDefault();
            // Here you can add AJAX submission logic if needed
            console.log('Form submitted:', form);
        });
    });

    // Example function to handle button clicks
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            console.log('Button clicked:', button);
        });
    });
});
