
// listing-detail.js - Map functionality for listing detail page

// Global variables
let map = null;
let marker = null;
let isFullscreen = false;
let nearbyListingsLayer = null;

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const mapElement = document.getElementById('listing-map');
    if (!mapElement) return;
    
    // Get coordinates from data attributes
    const lat = parseFloat(mapElement.dataset.lat);
    const lng = parseFloat(mapElement.dataset.lng);
    const title = mapElement.dataset.title;
    
    if (isNaN(lat) || isNaN(lng)) {
        console.warn('Invalid coordinates for map');
        return;
    }
    
    // Initialize the map
    initializeMap(lat, lng, title);
    
    // Set up event listeners
    setupEventListeners();
});

function initializeMap(lat, lng, title) {
    // Clean up any existing map
    if (map) {
        map.remove();
        map = null;
    }
    
    // Create map centered on listing location
    map = L.map('listing-map').setView([lat, lng], 13);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        minZoom: 3
    }).addTo(map);
    
    // Create custom marker with icon
    const customMarker = L.divIcon({
        className: 'custom-marker',
        html: `<i class="fas fa-map-marker-alt text-primary text-3xl"></i>`,
        iconSize: [32, 32],
        iconAnchor: [16, 32]
    });
    
    // Add marker to map
    marker = L.marker([lat, lng], { icon: customMarker }).addTo(map);
    
    // Add popup with listing title
    marker.bindPopup(title).openPopup();
    
    // Fit map to marker
    map.panTo([lat, lng]);
    
    // Load nearby listings
    loadNearbyListings(lat, lng);
}

function loadNearbyListings(lat, lng) {
    // Clear existing layer if any
    if (nearbyListingsLayer) {
        map.removeLayer(nearbyListingsLayer);
    }
    
    // Create a new layer group for nearby listings
    nearbyListingsLayer = L.layerGroup().addTo(map);
    
    // This would typically be an AJAX call to get nearby listings
    // For now, we'll simulate with some sample data
    const sampleListings = [
        { lat: lat + 0.01, lng: lng + 0.01, title: 'Listing 1', price: '1000 RON' },
        { lat: lat - 0.01, lng: lng - 0.01, title: 'Listing 2', price: '1500 RON' },
        { lat: lat + 0.02, lng: lng - 0.02, title: 'Listing 3', price: '800 RON' }
    ];
    
    // Add markers for nearby listings
    sampleListings.forEach(listing => {
        const smallMarker = L.divIcon({
            className: 'custom-marker',
            html: `<i class="fas fa-circle text-gray-500 text-xs"></i>`,
            iconSize: [8, 8],
            iconAnchor: [4, 4]
        });
        
        const marker = L.marker([listing.lat, listing.lng], { icon: smallMarker }).addTo(nearbyListingsLayer);
        marker.bindPopup(`<b>${listing.title}</b><br>${listing.price}`);
    });
}

function toggleMapSize() {
    const mapElement = document.getElementById('listing-map');
    const toggleBtn = document.querySelector('[onclick="toggleMapSize()"]');
    
    if (!mapElement || !toggleBtn) return;
    
    isFullscreen = !isFullscreen;
    
    if (isFullscreen) {
        mapElement.classList.add('map-fullscreen');
        toggleBtn.innerHTML = '<i class="fas fa-compress mr-2"></i>Redu harta';
    } else {
        mapElement.classList.remove('map-fullscreen');
        toggleBtn.innerHTML = '<i class="fas fa-expand mr-2"></i>Mărește harta';
    }
    
    // Resize map to fit new container size
    if (map) {
        map.invalidateSize();
    }
}

function setupEventListeners() {
    // Clean up map on page hide or visibility change
    window.addEventListener('pagehide', cleanupMap);
    window.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden') {
            cleanupMap();
        }
    });
}

function cleanupMap() {
    if (map) {
        map.remove();
        map = null;
    }
    if (nearbyListingsLayer) {
        nearbyListingsLayer.clearLayers();
        nearbyListingsLayer = null;
    }
    marker = null;
}

// Export functions for use in templates if needed
window.toggleMapSize = toggleMapSize;
