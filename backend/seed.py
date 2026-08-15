from database import engine, SessionLocal, Base
from models import ReferenceRange

def seed_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if database is already seeded
        if db.query(ReferenceRange).count() > 0:
            print("Database already seeded with reference ranges.")
            return

        # Seed data
        seed_data = [
            ReferenceRange(
                parameter_name="Hemoglobin",
                alias_names="Hb,Hgb",
                min_value=12.0,
                max_value=16.0,
                unit="g/dL",
                category="CBC",
                description="Oxygen-carrying protein in red blood cells. Low levels indicate anemia."
            ),
            ReferenceRange(
                parameter_name="Cholesterol",
                alias_names="Total Cholesterol,Chol",
                min_value=100.0,
                max_value=200.0,
                unit="mg/dL",
                category="Lipid Panel",
                description="Essential fat molecule. High levels increase cardiovascular risk."
            ),
            ReferenceRange(
                parameter_name="Glucose",
                alias_names="Fasting Glucose,Blood Sugar",
                min_value=70.0,
                max_value=100.0,
                unit="mg/dL",
                category="Metabolic Panel",
                description="Primary source of energy for body cells. High levels indicate hyperglycemia or diabetes."
            ),
            ReferenceRange(
                parameter_name="WBC",
                alias_names="White Blood Cells,Leukocytes",
                min_value=4.5,
                max_value=11.0,
                unit="10^3/uL",
                category="CBC",
                description="Immune cells that fight infection. High levels indicate infection or inflammation."
            ),
            ReferenceRange(
                parameter_name="Platelets",
                alias_names="PLT,Thrombocytes",
                min_value=150.0,
                max_value=450.0,
                unit="10^3/uL",
                category="CBC",
                description="Blood cells involved in clotting. Low levels pose bleeding risks."
            ),
            ReferenceRange(
                parameter_name="Thyroid Stimulating Hormone",
                alias_names="TSH",
                min_value=0.4,
                max_value=4.0,
                unit="uIU/mL",
                category="Thyroid Panel",
                description="Stimulates thyroid to produce T3/T4 hormones. High levels indicate hypothyroid activity."
            )
        ]

        db.add_all(seed_data)
        db.commit()
        print("Database successfully seeded with standard medical parameter ranges!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
