
// listing-detail.js - Handles functionality for the listing detail page

// Location and Map functionality
let map = null;
let isMapExpanded = false;

// Function to cleanup existing map
function cleanupMap() {
    if (map !== null) {
        console.log('Cleaning up existing map');
        map.remove();
        map = null;
    }
}

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing page components');
    // Only initialize if map element exists and no map is already created
    if (document.getElementById('listing-map') && !map) {
        initializeMap();
    }
    loadNearbyListings();
});

// Cleanup map when page is unloaded
window.addEventListener('beforeunload', function() {
    cleanupMap();
});

// Also cleanup on page hide (for mobile browsers and tabs)
window.addEventListener('pagehide', function() {
    cleanupMap();
});

// Handle potential SPA-like navigation
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') {
        cleanupMap();
    }
});

function initializeMap() {
    // Prevent multiple map initializations
    if (map !== null) {
        console.log('Map already initialized, skipping...');
        return;
    }
    
    const mapElement = document.getElementById('listing-map');
    if (!mapElement) {
        console.log('Map element not found');
        return;
    }
    
    // Check if map is already initialized by checking for leaflet container
    if (mapElement.querySelector('.leaflet-container')) {
        console.log('Map container already exists, skipping...');
        return;
    }
    
    const lat = parseFloat(mapElement.dataset.lat);
    const lng = parseFloat(mapElement.dataset.lng);
    const title = mapElement.dataset.title;
    
    if (isNaN(lat) || isNaN(lng)) {
        console.log('Invalid coordinates:', lat, lng);
        return;
    }
    
    console.log('Initializing map with coordinates:', lat, lng);
    
    try {
        // Initialize the map
        map = L.map('listing-map').setView([lat, lng], 15);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Create custom icon to avoid 404 errors
        const customIcon = L.divIcon({
            className: 'custom-marker',
            html: '<i class="fas fa-map-marker-alt" style="color: #dc2626; font-size: 24px;"></i>',
            iconSize: [24, 24],
            iconAnchor: [12, 24]
        });
        
        // Add marker for the listing
        const marker = L.marker([lat, lng], {icon: customIcon}).addTo(map);
        marker.bindPopup(`<b>${title}</b><br>Locația anunțului`);
        
        // Disable map interaction by default to prevent scroll conflicts
        map.scrollWheelZoom.disable();
        map.on('click', function() {
            map.scrollWheelZoom.enable();
            showNotification('Harta este acum activă pentru navigare', 'info');
        });
        
        console.log('Map initialized successfully');
    } catch (error) {
        console.error('Error initializing map:', error);
    }
}

function toggleMapSize() {
    if (!map) {
        console.log('No map available to toggle');
        return;
    }
    
    const mapElement = document.getElementById('listing-map');
    const toggleBtn = document.querySelector('[onclick="toggleMapSize()"]');
    
    if (!mapElement || !toggleBtn) {
        console.log('Map element or toggle button not found');
        return;
    }
    
    if (!isMapExpanded) {
        mapElement.classList.add('map-fullscreen');
        toggleBtn.innerHTML = '<i class="fas fa-compress mr-1"></i>Micșorează harta';
        isMapExpanded = true;
    } else {
        mapElement.classList.remove('map-fullscreen');
        toggleBtn.innerHTML = '<i class="fas fa-expand mr-1"></i>Mărește harta';
        isMapExpanded = false;
    }
    
    // Refresh map size after a short delay
    setTimeout(() => {
        if (map) {
            map.invalidateSize();
            console.log('Map size invalidated');
        }
    }, 100);
}

function getDirections() {
    const mapElement = document.getElementById('listing-map');
    if (!mapElement) return;
    
    const lat = mapElement.dataset.lat;
    const lng = mapElement.dataset.lng;
    
    // Open Google Maps with directions
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
    window.open(url, '_blank');
}

function loadNearbyListings() {
    const listingIdStr = "{{ listing.id }}";
    const nearbyContainer = document.getElementById('nearby-listings');
    
    if (!nearbyContainer) return;
    
    fetch(`/api/listings/${listingIdStr}/nearby/`)
        .then(response => response.json())
        .then(data => {
            if (data.listings && data.listings.length > 0) {
                nearbyContainer.innerHTML = '';
                data.listings.forEach(listing => {
                    const listingElement = document.createElement('div');
                    listingElement.className = 'border-b border-gray-200 pb-3 last:border-b-0 last:pb-0';
                    listingElement.innerHTML = `
                        <a href="/listing/${listing.id}/" class="flex items-center hover:bg-gray-50 p-2 rounded">
                            <div class="w-16 h-16 bg-gray-200 rounded flex items-center justify-center mr-3 flex-shrink-0">
                                ${listing.image_url ? `<img src="${listing.image_url}" alt="${listing.title}" class="w-full h-full object-cover rounded">` : '<i class="fas fa-image text-gray-400"></i>'}
                            </div>
                            <div class="flex-1 min-w-0">
                                <p class="text-sm font-medium text-gray-900 truncate">${listing.title}</p>
                                <p class="text-sm text-gray-500">${listing.price} RON</p>
                            </div>
                        </a>
                    `;
                    nearbyContainer.appendChild(listingElement);
                });
            } else {
                nearbyContainer.innerHTML = '<div class="text-center text-gray-500 py-3">Nu există anunțuri în apropiere</div>';
            }
        })
        .catch(error => {
            console.error('Error loading nearby listings:', error);
            nearbyContainer.innerHTML = '<div class="text-center text-red-500 py-3">Eroare la încărcarea anunțurilor din apropiere</div>';
        });
}
