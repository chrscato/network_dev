document.addEventListener('DOMContentLoaded', function() {
    // Check for saved dark mode preference
    const darkMode = localStorage.getItem('darkMode');
    
    // Apply dark mode if previously enabled
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
    }
    
    // Create dark mode toggle button
    const toggleButton = document.createElement('div');
    toggleButton.classList.add('dark-mode-toggle');
    toggleButton.innerHTML = darkMode === 'enabled' ? '☀️' : '🌙';
    document.body.appendChild(toggleButton);
    
    // Toggle dark mode on button click
    toggleButton.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        // Update localStorage
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('darkMode', 'enabled');
            toggleButton.innerHTML = '☀️';
        } else {
            localStorage.setItem('darkMode', null);
            toggleButton.innerHTML = '🌙';
        }
    });
}); 