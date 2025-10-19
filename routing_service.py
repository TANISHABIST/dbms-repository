from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from geolocation import GeolocationService, Location, DistanceResult
import json
import requests
from datetime import datetime, timedelta

@dataclass
class RouteStep:
    """Represents a step in a route"""
    instruction: str
    distance_meters: float
    duration_seconds: int
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]

@dataclass
class Route:
    """Represents a complete route"""
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    total_distance_km: float
    total_duration_minutes: int
    steps: List[RouteStep]
    transport_mode: str
    estimated_arrival: datetime

class RoutingService:
    """Service for GPS routing and navigation"""
    
    def __init__(self):
        self.geo_service = GeolocationService()
        # In production, you would use actual routing APIs like:
        # - Google Maps Directions API
        # - OpenRouteService API
        # - OSRM (Open Source Routing Machine)
        # - Mapbox Directions API
    
    def get_route(self, 
                  start_lat: float, 
                  start_lon: float, 
                  end_lat: float, 
                  end_lon: float,
                  transport_mode: str = "driving") -> Route:
        """
        Get route between two points
        Note: This is a simplified implementation
        In production, use actual routing APIs
        """
        start_location = Location(start_lat, start_lon)
        end_location = Location(end_lat, end_lon)
        
        # Calculate straight-line distance
        distance_result = self.geo_service.calculate_distance(start_location, end_location)
        
        # Create simplified route steps
        steps = self._create_simplified_route_steps(
            start_lat, start_lon, end_lat, end_lon, distance_result.distance_km
        )
        
        # Calculate estimated arrival time
        current_time = datetime.now()
        estimated_arrival = current_time + timedelta(minutes=distance_result.estimated_travel_time_minutes)
        
        return Route(
            start_location=(start_lat, start_lon),
            end_location=(end_lat, end_lon),
            total_distance_km=distance_result.distance_km,
            total_duration_minutes=distance_result.estimated_travel_time_minutes,
            steps=steps,
            transport_mode=transport_mode,
            estimated_arrival=estimated_arrival
        )
    
    def get_directions_to_hospital(self, 
                                 user_lat: float, 
                                 user_lon: float, 
                                 hospital_lat: float, 
                                 hospital_lon: float,
                                 transport_mode: str = "driving") -> Dict:
        """
        Get detailed directions to a hospital
        """
        route = self.get_route(user_lat, user_lon, hospital_lat, hospital_lon, transport_mode)
        
        return {
            "route": {
                "start": {
                    "latitude": route.start_location[0],
                    "longitude": route.start_location[1]
                },
                "end": {
                    "latitude": route.end_location[0],
                    "longitude": route.end_location[1]
                },
                "total_distance_km": round(route.total_distance_km, 2),
                "total_duration_minutes": route.total_duration_minutes,
                "transport_mode": route.transport_mode,
                "estimated_arrival": route.estimated_arrival.isoformat()
            },
            "steps": [
                {
                    "instruction": step.instruction,
                    "distance_meters": step.distance_meters,
                    "duration_seconds": step.duration_seconds,
                    "start_location": {
                        "latitude": step.start_location[0],
                        "longitude": step.start_location[1]
                    },
                    "end_location": {
                        "latitude": step.end_location[0],
                        "longitude": step.end_location[1]
                    }
                }
                for step in route.steps
            ],
            "summary": {
                "total_steps": len(route.steps),
                "estimated_travel_time": f"{route.total_duration_minutes} minutes",
                "estimated_distance": f"{route.total_distance_km:.2f} km"
            }
        }
    
    def get_emergency_route(self, 
                          user_lat: float, 
                          user_lon: float, 
                          hospital_lat: float, 
                          hospital_lon: float) -> Dict:
        """
        Get emergency route with fastest path
        """
        # For emergency routes, we assume faster speeds
        route = self.get_route(user_lat, user_lon, hospital_lat, hospital_lon, "emergency")
        
        # Adjust for emergency conditions (faster speeds, priority lanes, etc.)
        emergency_duration = int(route.total_duration_minutes * 0.8)  # 20% faster
        emergency_arrival = datetime.now() + timedelta(minutes=emergency_duration)
        
        return {
            "route": {
                "start": {
                    "latitude": route.start_location[0],
                    "longitude": route.start_location[1]
                },
                "end": {
                    "latitude": route.end_location[0],
                    "longitude": route.end_location[1]
                },
                "total_distance_km": round(route.total_distance_km, 2),
                "total_duration_minutes": emergency_duration,
                "transport_mode": "emergency",
                "estimated_arrival": emergency_arrival.isoformat(),
                "is_emergency": True
            },
            "emergency_info": {
                "priority": "HIGH",
                "estimated_time_saved": f"{route.total_duration_minutes - emergency_duration} minutes",
                "recommendations": [
                    "Use emergency lanes if available",
                    "Contact hospital in advance",
                    "Prepare medical documents",
                    "Have emergency contacts ready"
                ]
            },
            "steps": [
                {
                    "instruction": step.instruction,
                    "distance_meters": step.distance_meters,
                    "duration_seconds": int(step.duration_seconds * 0.8),  # 20% faster
                    "start_location": {
                        "latitude": step.start_location[0],
                        "longitude": step.start_location[1]
                    },
                    "end_location": {
                        "latitude": step.end_location[0],
                        "longitude": step.end_location[1]
                    }
                }
                for step in route.steps
            ]
        }
    
    def get_multiple_routes(self, 
                          user_lat: float, 
                          user_lon: float, 
                          hospitals: List[Dict]) -> List[Dict]:
        """
        Get routes to multiple hospitals and rank by travel time
        """
        routes = []
        
        for hospital in hospitals:
            route = self.get_route(
                user_lat, user_lon, 
                hospital["latitude"], hospital["longitude"]
            )
            
            route_info = {
                "hospital": hospital,
                "route": {
                    "total_distance_km": round(route.total_distance_km, 2),
                    "total_duration_minutes": route.total_duration_minutes,
                    "estimated_arrival": route.estimated_arrival.isoformat()
                },
                "priority_score": self._calculate_route_priority(route, hospital)
            }
            routes.append(route_info)
        
        # Sort by priority score (higher is better)
        routes.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return routes
    
    def _create_simplified_route_steps(self, 
                                     start_lat: float, 
                                     start_lon: float, 
                                     end_lat: float, 
                                     end_lon: float, 
                                     total_distance_km: float) -> List[RouteStep]:
        """
        Create simplified route steps
        In production, this would use actual routing APIs
        """
        steps = []
        
        # Calculate midpoint for a simple 2-step route
        mid_lat = (start_lat + end_lat) / 2
        mid_lon = (start_lon + end_lon) / 2
        
        # Step 1: Start to midpoint
        step1_distance = total_distance_km * 0.5 * 1000  # Convert to meters
        step1_duration = int(step1_distance / 1000 * 60)  # Rough estimate
        
        steps.append(RouteStep(
            instruction="Start navigation to destination",
            distance_meters=step1_distance,
            duration_seconds=step1_duration,
            start_location=(start_lat, start_lon),
            end_location=(mid_lat, mid_lon)
        ))
        
        # Step 2: Midpoint to end
        step2_distance = total_distance_km * 0.5 * 1000
        step2_duration = int(step2_distance / 1000 * 60)
        
        steps.append(RouteStep(
            instruction="Continue to hospital destination",
            distance_meters=step2_distance,
            duration_seconds=step2_duration,
            start_location=(mid_lat, mid_lon),
            end_location=(end_lat, end_lon)
        ))
        
        return steps
    
    def _calculate_route_priority(self, route: Route, hospital: Dict) -> float:
        """
        Calculate priority score for route based on distance, time, and hospital factors
        """
        # Distance factor (closer is better)
        distance_factor = max(0, 1 - (route.total_distance_km / 500))
        
        # Time factor (faster is better)
        time_factor = max(0, 1 - (route.total_duration_minutes / 300))
        
        # Hospital reputation factor (if available)
        hospital_factor = 0.5  # Default neutral score
        
        # Combined priority score
        priority_score = (
            distance_factor * 0.4 +  # 40% distance
            time_factor * 0.4 +     # 40% time
            hospital_factor * 0.2   # 20% hospital quality
        )
        
        return priority_score

class NavigationService:
    """Service for real-time navigation and tracking"""
    
    def __init__(self):
        self.routing_service = RoutingService()
        self.active_navigations = {}  # Track active navigation sessions
    
    def start_navigation(self, 
                        user_id: str, 
                        start_lat: float, 
                        start_lon: float, 
                        end_lat: float, 
                        end_lon: float,
                        transport_mode: str = "driving") -> Dict:
        """
        Start a navigation session
        """
        navigation_id = f"nav_{user_id}_{datetime.now().timestamp()}"
        
        route = self.routing_service.get_route(
            start_lat, start_lon, end_lat, end_lon, transport_mode
        )
        
        navigation_session = {
            "id": navigation_id,
            "user_id": user_id,
            "route": route,
            "current_step": 0,
            "started_at": datetime.now(),
            "status": "active"
        }
        
        self.active_navigations[navigation_id] = navigation_session
        
        return {
            "navigation_id": navigation_id,
            "route": {
                "total_distance_km": route.total_distance_km,
                "total_duration_minutes": route.total_duration_minutes,
                "estimated_arrival": route.estimated_arrival.isoformat()
            },
            "current_step": {
                "instruction": route.steps[0].instruction,
                "distance_meters": route.steps[0].distance_meters,
                "duration_seconds": route.steps[0].duration_seconds
            },
            "status": "started"
        }
    
    def update_navigation(self, 
                         navigation_id: str, 
                         current_lat: float, 
                         current_lon: float) -> Dict:
        """
        Update navigation with current position
        """
        if navigation_id not in self.active_navigations:
            return {"error": "Navigation session not found"}
        
        session = self.active_navigations[navigation_id]
        route = session["route"]
        
        # Calculate distance to destination
        current_location = Location(current_lat, current_lon)
        destination = Location(route.end_location[0], route.end_location[1])
        remaining_distance = self.routing_service.geo_service.calculate_distance(
            current_location, destination
        )
        
        # Update session
        session["last_update"] = datetime.now()
        session["current_position"] = (current_lat, current_lon)
        
        return {
            "navigation_id": navigation_id,
            "remaining_distance_km": round(remaining_distance.distance_km, 2),
            "estimated_time_remaining_minutes": remaining_distance.estimated_travel_time_minutes,
            "current_step": session["current_step"],
            "status": "active"
        }
    
    def end_navigation(self, navigation_id: str) -> Dict:
        """
        End a navigation session
        """
        if navigation_id not in self.active_navigations:
            return {"error": "Navigation session not found"}
        
        session = self.active_navigations[navigation_id]
        session["status"] = "completed"
        session["ended_at"] = datetime.now()
        
        return {
            "navigation_id": navigation_id,
            "status": "completed",
            "duration_minutes": int((session["ended_at"] - session["started_at"]).total_seconds() / 60)
        }

# Example usage
if __name__ == "__main__":
    routing_service = RoutingService()
    
    # Test route calculation
    route = routing_service.get_route(28.6139, 77.2090, 19.0760, 72.8777)
    print(f"Route from Delhi to Mumbai: {route.total_distance_km:.2f} km, {route.total_duration_minutes} minutes")
    
    # Test navigation service
    nav_service = NavigationService()
    nav_result = nav_service.start_navigation("user123", 28.6139, 77.2090, 19.0760, 72.8777)
    print(f"Navigation started: {nav_result['navigation_id']}")

