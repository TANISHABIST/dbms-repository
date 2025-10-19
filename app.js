// Organ Transplant Database Frontend Application
class OrganTransplantApp {
    constructor() {
        this.map = null;
        this.markers = [];
        this.userLocation = null;
        this.apiBaseUrl = 'http://localhost:8000';
        this.init();
    }

    init() {
        this.initializeMap();
        this.setupEventListeners();
        this.getUserLocation();
    }

    initializeMap() {
        // Initialize map centered on India
        this.map = L.map('map').setView([20.5937, 78.9629], 5);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add custom CSS for map
        this.map.getContainer().style.borderRadius = '15px';
    }

    setupEventListeners() {
        // Search form
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.searchOrgans();
        });

        // Hospital search form
        document.getElementById('hospitalForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.searchHospitals();
        });

        // Patient request form
        document.getElementById('patientRequestForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitPatientRequest();
        });
    }

    async getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    this.map.setView([this.userLocation.lat, this.userLocation.lng], 10);
                    this.addUserMarker();
                },
                (error) => {
                    console.log('Geolocation error:', error);
                    this.showError('Unable to get your location. Please enter coordinates manually.');
                }
            );
        } else {
            this.showError('Geolocation is not supported by this browser.');
        }
    }

    addUserMarker() {
        if (this.userLocation) {
            const userIcon = L.divIcon({
                className: 'user-marker',
                html: '<i class="fas fa-user" style="color: #667eea; font-size: 20px;"></i>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            L.marker([this.userLocation.lat, this.userLocation.lng], { icon: userIcon })
                .addTo(this.map)
                .bindPopup('<b>Your Location</b>');
        }
    }

    async searchOrgans() {
        if (!this.userLocation) {
            this.showError('Please allow location access or enter coordinates manually.');
            return;
        }

        this.showLoading('Searching for organs...');

        const organName = document.getElementById('organName').value;
        const bloodType = document.getElementById('bloodType').value;
        const urgencyLevel = document.getElementById('urgencyLevel').value;
        const maxDistance = document.getElementById('maxDistance').value;

        try {
            const params = new URLSearchParams({
                latitude: this.userLocation.lat,
                longitude: this.userLocation.lng,
                max_distance_km: maxDistance
            });

            if (organName) params.append('organ_name', organName);
            if (bloodType) params.append('blood_type', bloodType);
            if (urgencyLevel) params.append('urgency_level', urgencyLevel);

            const response = await fetch(`${this.apiBaseUrl}/search/organs?${params}`);
            const results = await response.json();

            this.displayOrganResults(results);
            this.addOrganMarkers(results);
        } catch (error) {
            this.showError('Error searching for organs: ' + error.message);
        }
    }

    async searchHospitals() {
        if (!this.userLocation) {
            this.showError('Please allow location access or enter coordinates manually.');
            return;
        }

        this.showLoading('Searching for hospitals...');

        const maxDistance = document.getElementById('maxDistanceHospitals').value;

        try {
            const params = new URLSearchParams({
                latitude: this.userLocation.lat,
                longitude: this.userLocation.lng,
                max_distance_km: maxDistance
            });

            const response = await fetch(`${this.apiBaseUrl}/search/nearest-hospitals?${params}`);
            const results = await response.json();

            this.displayHospitalResults(results);
            this.addHospitalMarkers(results);
        } catch (error) {
            this.showError('Error searching for hospitals: ' + error.message);
        }
    }

    async submitPatientRequest() {
        if (!this.userLocation) {
            this.showError('Please allow location access or enter coordinates manually.');
            return;
        }

        const formData = {
            patient_name: document.getElementById('patientName').value,
            patient_age: parseInt(document.getElementById('patientAge').value),
            blood_type: document.getElementById('patientBloodType').value,
            organ_name: document.getElementById('patientOrgan').value,
            latitude: this.userLocation.lat,
            longitude: this.userLocation.lng,
            contact_phone: document.getElementById('contactPhone').value,
            contact_email: document.getElementById('contactEmail').value,
            medical_notes: document.getElementById('medicalNotes').value,
            urgency_level: 1
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/patient-request`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.error) {
                this.showError(result.error);
            } else {
                this.showSuccess(`Patient request submitted successfully! Found ${result.matching_hospitals} matching hospitals.`);
                this.displayPatientRequestResults(result.top_matches);
            }
        } catch (error) {
            this.showError('Error submitting patient request: ' + error.message);
        }
    }

    displayOrganResults(results) {
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="error">No organs found matching your criteria.</div>';
            return;
        }

        results.forEach((result, index) => {
            const resultElement = document.createElement('div');
            resultElement.className = 'result-item';
            resultElement.innerHTML = `
                <h4>${result.hospital.name}</h4>
                <p><strong>Organ:</strong> ${result.organ.name}</p>
                <p><strong>Blood Type:</strong> ${result.availability.blood_type || 'Any'}</p>
                <p><strong>Condition:</strong> ${result.availability.condition}</p>
                <p><strong>Quantity:</strong> ${result.availability.quantity}</p>
                <p><strong>Address:</strong> ${result.hospital.address}</p>
                <p><strong>Phone:</strong> ${result.hospital.phone || 'N/A'}</p>
                <div class="distance-info">
                    ${result.distance.km} km • ${result.distance.travel_time_minutes} min
                </div>
                <button onclick="app.getDirections(${result.hospital.latitude}, ${result.hospital.longitude})" 
                        style="margin-top: 10px; padding: 8px 15px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    <i class="fas fa-route"></i> Get Directions
                </button>
            `;
            resultsContainer.appendChild(resultElement);
        });
    }

    displayHospitalResults(results) {
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="error">No hospitals found within the specified distance.</div>';
            return;
        }

        results.forEach((result, index) => {
            const resultElement = document.createElement('div');
            resultElement.className = 'result-item';
            resultElement.innerHTML = `
                <h4>${result.name}</h4>
                <p><strong>Address:</strong> ${result.address}</p>
                <p><strong>City:</strong> ${result.city}, ${result.state}</p>
                <p><strong>Phone:</strong> ${result.phone || 'N/A'}</p>
                <p><strong>Email:</strong> ${result.email || 'N/A'}</p>
                <div class="distance-info">
                    ${result.distance.km} km • ${result.distance.travel_time_minutes} min
                </div>
                <button onclick="app.getDirections(${result.latitude}, ${result.longitude})" 
                        style="margin-top: 10px; padding: 8px 15px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    <i class="fas fa-route"></i> Get Directions
                </button>
            `;
            resultsContainer.appendChild(resultElement);
        });
    }

    displayPatientRequestResults(results) {
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="error">No matching hospitals found for your request.</div>';
            return;
        }

        results.forEach((result, index) => {
            const resultElement = document.createElement('div');
            resultElement.className = 'result-item';
            resultElement.innerHTML = `
                <h4>${result.hospital.name}</h4>
                <p><strong>Organ:</strong> ${result.organ.name}</p>
                <p><strong>Blood Type:</strong> ${result.availability.blood_type || 'Any'}</p>
                <p><strong>Condition:</strong> ${result.availability.condition}</p>
                <p><strong>Compatibility Score:</strong> ${result.compatibility_score}</p>
                <p><strong>Priority Score:</strong> ${result.priority_score}</p>
                <div class="distance-info">
                    ${result.distance.km} km • ${result.distance.travel_time_minutes} min
                </div>
                <button onclick="app.getDirections(${result.hospital.latitude}, ${result.hospital.longitude})" 
                        style="margin-top: 10px; padding: 8px 15px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    <i class="fas fa-route"></i> Get Directions
                </button>
            `;
            resultsContainer.appendChild(resultElement);
        });
    }

    addOrganMarkers(results) {
        this.clearMarkers();

        results.forEach((result, index) => {
            const marker = L.marker([result.hospital.latitude, result.hospital.longitude])
                .addTo(this.map)
                .bindPopup(`
                    <div style="min-width: 200px;">
                        <h4>${result.hospital.name}</h4>
                        <p><strong>Organ:</strong> ${result.organ.name}</p>
                        <p><strong>Blood Type:</strong> ${result.availability.blood_type || 'Any'}</p>
                        <p><strong>Condition:</strong> ${result.availability.condition}</p>
                        <p><strong>Distance:</strong> ${result.distance.km} km</p>
                        <p><strong>Travel Time:</strong> ${result.distance.travel_time_minutes} min</p>
                        <button onclick="app.getDirections(${result.hospital.latitude}, ${result.hospital.longitude})" 
                                style="margin-top: 10px; padding: 5px 10px; background: #667eea; color: white; border: none; border-radius: 3px; cursor: pointer;">
                            Get Directions
                        </button>
                    </div>
                `);

            this.markers.push(marker);
        });

        if (results.length > 0) {
            this.fitMapToMarkers();
        }
    }

    addHospitalMarkers(results) {
        this.clearMarkers();

        results.forEach((result, index) => {
            const marker = L.marker([result.latitude, result.longitude])
                .addTo(this.map)
                .bindPopup(`
                    <div style="min-width: 200px;">
                        <h4>${result.name}</h4>
                        <p><strong>Address:</strong> ${result.address}</p>
                        <p><strong>City:</strong> ${result.city}, ${result.state}</p>
                        <p><strong>Phone:</strong> ${result.phone || 'N/A'}</p>
                        <p><strong>Distance:</strong> ${result.distance.km} km</p>
                        <p><strong>Travel Time:</strong> ${result.distance.travel_time_minutes} min</p>
                        <button onclick="app.getDirections(${result.latitude}, ${result.longitude})" 
                                style="margin-top: 10px; padding: 5px 10px; background: #667eea; color: white; border: none; border-radius: 3px; cursor: pointer;">
                            Get Directions
                        </button>
                    </div>
                `);

            this.markers.push(marker);
        });

        if (results.length > 0) {
            this.fitMapToMarkers();
        }
    }

    clearMarkers() {
        this.markers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = [];
    }

    fitMapToMarkers() {
        if (this.markers.length > 0) {
            const group = new L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    getDirections(lat, lng) {
        if (this.userLocation) {
            // Open directions in new tab (using Google Maps as example)
            const url = `https://www.google.com/maps/dir/${this.userLocation.lat},${this.userLocation.lng}/${lat},${lng}`;
            window.open(url, '_blank');
        } else {
            this.showError('Please allow location access to get directions.');
        }
    }

    showLoading(message) {
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = `<div class="loading">${message}</div>`;
    }

    showError(message) {
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = `<div class="error">${message}</div>`;
    }

    showSuccess(message) {
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = `<div class="success">${message}</div>`;
    }
}

// Initialize the application
const app = new OrganTransplantApp();

