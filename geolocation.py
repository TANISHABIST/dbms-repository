import math
import requests
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from models import Hospital, OrganAvailability

@dataclass
class Location:
    """Represents a geographical location"""
    latitude: float
    longitude: float
    address: Optional[str] = None

@dataclass
class DistanceResult:
    """Result of distance calculation"""
    distance_km: float
    distance_miles: float
    estimated_travel_time_minutes: int
    route_summary: Optional[str] = None

class GeolocationService:
    """Service for geolocation and distance calculations"""
    
    def __init__(self):
        self.earth_radius_km = 6371.0
        self.earth_radius_miles = 3959.0
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth using Haversine formula
        Returns distance in kilometers
        """
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.earth_radius_km * c
    
    def calculate_distance(self, location1: Location, location2: Location) -> DistanceResult:
        """Calculate distance between two locations"""
        distance_km = self.haversine_distance(
            location1.latitude, location1.longitude,
            location2.latitude, location2.longitude
        )
        
        distance_miles = distance_km * 0.621371
        
        # Estimate travel time (assuming average speed of 50 km/h in urban areas)
        estimated_travel_time = int((distance_km / 50) * 60)  # Convert to minutes
        
        return DistanceResult(
            distance_km=distance_km,
            distance_miles=distance_miles,
            estimated_travel_time_minutes=estimated_travel_time
        )
    
    def find_nearest_hospitals(self, 
                             user_latitude: float, 
                             user_longitude: float, 
                             hospitals: List[Hospital], 
                             max_distance_km: float = 500.0) -> List[Tuple[Hospital, DistanceResult]]:
        """
        Find hospitals within a specified distance from user location
        Returns list of (hospital, distance_result) tuples sorted by distance
        """
        user_location = Location(user_latitude, user_longitude)
        nearby_hospitals = []
        
        for hospital in hospitals:
            hospital_location = Location(hospital.latitude, hospital.longitude)
            distance_result = self.calculate_distance(user_location, hospital_location)
            
            if distance_result.distance_km <= max_distance_km:
                nearby_hospitals.append((hospital, distance_result))
        
        # Sort by distance
        nearby_hospitals.sort(key=lambda x: x[1].distance_km)
        return nearby_hospitals
    
    def get_coordinates_from_address(self, address: str) -> Optional[Location]:
        """
        Get coordinates from address using geocoding
        Note: This is a placeholder - in production, use a proper geocoding service
        """
        # This is a simplified version - in production, use Google Maps API, OpenStreetMap, etc.
        # For now, return None to indicate geocoding is not implemented
        return None
    
    def calculate_route_time(self, 
                           start_lat: float, 
                           start_lon: float, 
                           end_lat: float, 
                           end_lon: float,
                           transport_mode: str = "driving") -> Optional[DistanceResult]:
        """
        Calculate actual route time using routing service
        Note: This is a placeholder - in production, use Google Maps Directions API, OSRM, etc.
        """
        # For now, use straight-line distance with speed factor
        distance_km = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)
        
        # Adjust speed based on transport mode
        speed_kmh = {
            "driving": 50,
            "walking": 5,
            "cycling": 15,
            "public_transport": 30
        }.get(transport_mode, 50)
        
        travel_time_minutes = int((distance_km / speed_kmh) * 60)
        
        return DistanceResult(
            distance_km=distance_km,
            distance_miles=distance_km * 0.621371,
            estimated_travel_time_minutes=travel_time_minutes
        )

class OrganSearchService:
    """Service for searching organs and finding nearest hospitals"""
    
    def __init__(self, geolocation_service: GeolocationService):
        self.geo_service = geolocation_service
    
    def search_organs_nearby(self, 
                           user_latitude: float, 
                           user_longitude: float, 
                           organ_name: str,
                           blood_type: str = None,
                           max_distance_km: float = 500.0) -> List[Dict]:
        """
        Search for available organs near user location
        Returns list of available organs with hospital and distance info
        """
        # This would typically query the database
        # For now, return a placeholder structure
        results = []
        
        # In production, this would:
        # 1. Query database for hospitals with available organs
        # 2. Filter by organ name and blood type
        # 3. Calculate distances
        # 4. Return sorted results
        
        return results
    
    def get_organ_availability_score(self, 
                                   organ_availability: OrganAvailability, 
                                   user_blood_type: str = None) -> float:
        """
        Calculate compatibility score for organ availability
        Returns score between 0 and 1
        """
        score = 0.5  # Base score
        
        # Blood type compatibility
        if user_blood_type and organ_availability.blood_type:
            if user_blood_type == organ_availability.blood_type:
                score += 0.3
            elif self._is_blood_type_compatible(user_blood_type, organ_availability.blood_type):
                score += 0.2
        
        # Organ condition
        condition_scores = {
            "excellent": 0.2,
            "good": 0.1,
            "fair": 0.05
        }
        score += condition_scores.get(organ_availability.condition, 0)
        
        return min(score, 1.0)
    
    def _is_blood_type_compatible(self, recipient: str, donor: str) -> bool:
        """Check if blood types are compatible"""
        # Simplified blood type compatibility
        compatible_pairs = {
            "O-": ["O-"],
            "O+": ["O-", "O+"],
            "A-": ["O-", "A-"],
            "A+": ["O-", "O+", "A-", "A+"],
            "B-": ["O-", "B-"],
            "B+": ["O-", "O+", "B-", "B+"],
            "AB-": ["O-", "A-", "B-", "AB-"],
            "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
        }
        
        return donor in compatible_pairs.get(recipient, [])

# Example usage and testing
if __name__ == "__main__":
    # Test the geolocation service
    geo_service = GeolocationService()
    
    # Test distance calculation
    location1 = Location(28.6139, 77.2090)  # Delhi
    location2 = Location(19.0760, 72.8777)  # Mumbai
    
    distance = geo_service.calculate_distance(location1, location2)
    print(f"Distance between Delhi and Mumbai: {distance.distance_km:.2f} km")
    print(f"Estimated travel time: {distance.estimated_travel_time_minutes} minutes")

