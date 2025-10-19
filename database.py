from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Hospital, Organ, OrganAvailability, TransplantProgram, PatientRequest, SearchResult
import json
import os

# Database configuration
DATABASE_URL = "sqlite:///./organ_transplant.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_sample_data():
    """Initialize database with sample hospital and organ data"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Hospital).count() > 0:
            print("Sample data already exists")
            return
        
        # Sample organs
        organs_data = [
            {"name": "Heart", "description": "Heart transplant", "urgency_level": 4, "preservation_time_hours": 4},
            {"name": "Liver", "description": "Liver transplant", "urgency_level": 3, "preservation_time_hours": 12},
            {"name": "Kidney", "description": "Kidney transplant", "urgency_level": 2, "preservation_time_hours": 24},
            {"name": "Lung", "description": "Lung transplant", "urgency_level": 4, "preservation_time_hours": 6},
            {"name": "Pancreas", "description": "Pancreas transplant", "urgency_level": 3, "preservation_time_hours": 12},
            {"name": "Cornea", "description": "Cornea transplant", "urgency_level": 1, "preservation_time_hours": 72},
            {"name": "Bone Marrow", "description": "Bone marrow transplant", "urgency_level": 3, "preservation_time_hours": 48}
        ]
        
        for organ_data in organs_data:
            organ = Organ(**organ_data)
            db.add(organ)
        
        # Sample hospitals in major Indian cities
        hospitals_data = [
            {
                "name": "Apollo Hospitals, Chennai",
                "address": "21 Greams Lane, Off Greams Road, Chennai",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "latitude": 13.0827,
                "longitude": 80.2707,
                "phone": "+91-44-2829-3333",
                "email": "info@apollohospitals.com",
                "website": "https://www.apollohospitals.com"
            },
            {
                "name": "Fortis Hospital, Mumbai",
                "address": "Mulund Goregaon Link Road, Mulund West, Mumbai",
                "city": "Mumbai",
                "state": "Maharashtra",
                "latitude": 19.1700,
                "longitude": 72.9560,
                "phone": "+91-22-4925-0000",
                "email": "info@fortishealthcare.com",
                "website": "https://www.fortishealthcare.com"
            },
            {
                "name": "Max Hospital, Delhi",
                "address": "1, Press Enclave Road, Saket, New Delhi",
                "city": "Delhi",
                "state": "Delhi",
                "latitude": 28.5355,
                "longitude": 77.2110,
                "phone": "+91-11-4055-4055",
                "email": "info@maxhealthcare.com",
                "website": "https://www.maxhealthcare.com"
            },
            {
                "name": "Narayana Health, Bangalore",
                "address": "258/A, Bommasandra Industrial Area, Hosur Road, Bangalore",
                "city": "Bangalore",
                "state": "Karnataka",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "phone": "+91-80-6750-6750",
                "email": "info@narayanahealth.org",
                "website": "https://www.narayanahealth.org"
            },
            {
                "name": "Medanta Hospital, Gurgaon",
                "address": "Sector 38, Gurgaon, Haryana",
                "city": "Gurgaon",
                "state": "Haryana",
                "latitude": 28.4595,
                "longitude": 77.0266,
                "phone": "+91-124-414-1414",
                "email": "info@medanta.org",
                "website": "https://www.medanta.org"
            },
            {
                "name": "Kokilaben Hospital, Mumbai",
                "address": "Rao Saheb Achutrao Patwardhan Marg, Four Bungalows, Andheri West, Mumbai",
                "city": "Mumbai",
                "state": "Maharashtra",
                "latitude": 19.1136,
                "longitude": 72.8367,
                "phone": "+91-22-3099-9999",
                "email": "info@kokilabenhospital.com",
                "website": "https://www.kokilabenhospital.com"
            },
            {
                "name": "Manipal Hospital, Bangalore",
                "address": "98, HAL Airport Road, Bangalore",
                "city": "Bangalore",
                "state": "Karnataka",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "phone": "+91-80-2502-4444",
                "email": "info@manipalhospitals.com",
                "website": "https://www.manipalhospitals.com"
            },
            {
                "name": "AIIMS, New Delhi",
                "address": "Ansari Nagar, New Delhi",
                "city": "Delhi",
                "state": "Delhi",
                "latitude": 28.5679,
                "longitude": 77.2090,
                "phone": "+91-11-2658-8500",
                "email": "info@aiims.edu",
                "website": "https://www.aiims.edu"
            }
        ]
        
        for hospital_data in hospitals_data:
            hospital = Hospital(**hospital_data)
            db.add(hospital)
        
        db.commit()
        
        # Add organ availability for some hospitals
        hospitals = db.query(Hospital).all()
        organs = db.query(Organ).all()
        
        # Create some sample organ availability
        import random
        for hospital in hospitals[:5]:  # First 5 hospitals
            for organ in organs:
                if random.choice([True, False]):  # Random availability
                    availability = OrganAvailability(
                        hospital_id=hospital.id,
                        organ_id=organ.id,
                        is_available=True,
                        quantity=random.randint(1, 3),
                        blood_type=random.choice(["A+", "B+", "O+", "AB+", "A-", "B-", "O-", "AB-"]),
                        age_range=random.choice(["18-65", "pediatric", "senior"]),
                        condition=random.choice(["excellent", "good", "fair"]),
                        notes=f"Available at {hospital.name}"
                    )
                    db.add(availability)
        
        # Add transplant programs
        for hospital in hospitals:
            for organ in organs[:3]:  # First 3 organs for each hospital
                program = TransplantProgram(
                    hospital_id=hospital.id,
                    organ_id=organ.id,
                    program_name=f"{organ.name} Transplant Program",
                    is_active=True,
                    success_rate=random.uniform(85, 98),
                    average_wait_time_days=random.randint(30, 365),
                    program_description=f"Comprehensive {organ.name} transplant program",
                    requirements="Standard transplant criteria apply"
                )
                db.add(program)
        
        db.commit()
        print("Sample data initialized successfully")
        
    except Exception as e:
        print(f"Error initializing sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    init_sample_data()

