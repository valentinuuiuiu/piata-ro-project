
// Update statistics on homepage
document.addEventListener('DOMContentLoaded', function() {
    // Get the statistics elements
    const totalListingsStat = document.getElementById('totalListingsStat');
    const totalCategoriesStat = document.getElementById('totalCategoriesStat');
    
    // Update the statistics with values from the context
    if (totalListingsStat) {
        totalListingsStat.textContent = {{ total_listings }};
    }
    if (totalCategoriesStat) {
        totalCategoriesStat.textContent = {{ total_categories }};
    }
});
