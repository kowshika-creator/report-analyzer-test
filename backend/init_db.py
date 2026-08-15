from database import engine, SessionLocal, Base
from models import ReferenceRange, User
import bcrypt
import datetime

def init_and_seed_db():
    print("Initializing database tables...")
    # Drop tables to recreate with new schema safely
    Base.metadata.drop_all(bind=engine)
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding clinical reference ranges...")
        
        # Comprehensive clinical ranges representing standard accepted values
        seed_ranges = [
            # 1. CBC Panel
            ReferenceRange(
                biomarker_name="Hemoglobin",
                alias_names="Hb,Hgb,Hemoglobin Count",
                min_normal=12.0,
                max_normal=17.5,
                unit="g/dL",
                panel_name="CBC",
                description="Oxygen-carrying protein in red blood cells. Low values may point to anemia; high values can indicate dehydration."
            ),
            ReferenceRange(
                biomarker_name="WBC",
                alias_names="White Blood Cells,Leukocytes,WBC Count",
                min_normal=4.5,
                max_normal=11.0,
                unit="10^3/uL",
                panel_name="CBC",
                description="White Blood Cells. Crucial for immune response. High counts indicate infections; low counts point to immune vulnerabilities."
            ),
            ReferenceRange(
                biomarker_name="Platelets",
                alias_names="PLT,Thrombocytes,Platelet Count",
                min_normal=150.0,
                max_normal=450.0,
                unit="10^3/uL",
                panel_name="CBC",
                description="Cells essential for blood clotting. Extremely low counts pose severe bleeding risks."
            ),
            ReferenceRange(
                biomarker_name="RBC",
                alias_names="Red Blood Cells,Erythrocytes,RBC Count",
                min_normal=4.2,
                max_normal=5.9,
                unit="10^6/uL",
                panel_name="CBC",
                description="Red Blood Cell count. Responsible for cellular oxygen distribution."
            ),
            ReferenceRange(
                biomarker_name="Neutrophils",
                alias_names="Neutrophils %,Segmented Neutrophils,NEUT,NEUT%",
                min_normal=40.0,
                max_normal=75.0,
                unit="%",
                panel_name="CBC",
                description="Primary white blood cell subtype defending against acute bacterial infections. Elevated counts occur in acute inflammatory/infectious patterns."
            ),

            # 2. Blood Sugar Panel
            ReferenceRange(
                biomarker_name="HbA1c",
                alias_names="Hemoglobin A1c,A1c,Glycated Hemoglobin",
                min_normal=4.0,
                max_normal=5.6,
                unit="%",
                panel_name="Blood Sugar",
                description="Measures average blood sugar levels over the past 3 months. Values >= 6.5% indicate diabetes."
            ),
            ReferenceRange(
                biomarker_name="Fasting",
                alias_names="Fasting Glucose,Fasting Blood Sugar,FBS,Glucose Fasting",
                min_normal=70.0,
                max_normal=100.0,
                unit="mg/dL",
                panel_name="Blood Sugar",
                description="Blood sugar level after an overnight fast. High fasting levels indicate insulin resistance or prediabetes."
            ),
            ReferenceRange(
                biomarker_name="Post-Prandial",
                alias_names="Post-Prandial Glucose,Post-Meal Glucose,PPBS",
                min_normal=70.0,
                max_normal=140.0,
                unit="mg/dL",
                panel_name="Blood Sugar",
                description="Glucose levels measured exactly 2 hours after a meal. Normal digestive sugar response should clear below 140."
            ),

            # 3. Lipid Profile Panel
            ReferenceRange(
                biomarker_name="Total Cholesterol",
                alias_names="Cholesterol,Total Chol,Chol",
                min_normal=100.0,
                max_normal=200.0,
                unit="mg/dL",
                panel_name="Lipid Profile",
                description="Total fat concentration in blood. Elevated levels raise atherosclerotic cardiovascular risks."
            ),
            ReferenceRange(
                biomarker_name="HDL",
                alias_names="HDL Cholesterol,High-Density Lipoprotein,Good Cholesterol",
                min_normal=40.0,
                max_normal=60.0,
                unit="mg/dL",
                panel_name="Lipid Profile",
                description="High-Density Lipoprotein ('good' cholesterol). Helps clear fat deposits from arteries. Higher is generally optimal."
            ),
            ReferenceRange(
                biomarker_name="LDL",
                alias_names="LDL Cholesterol,Low-Density Lipoprotein,Bad Cholesterol",
                min_normal=50.0,
                max_normal=100.0,
                unit="mg/dL",
                panel_name="Lipid Profile",
                description="Low-Density Lipoprotein ('bad' cholesterol). Leads to arterial plaque accumulation. Lower values are healthier."
            ),
            ReferenceRange(
                biomarker_name="Triglycerides",
                alias_names="TRIG,Triglyceride",
                min_normal=50.0,
                max_normal=150.0,
                unit="mg/dL",
                panel_name="Lipid Profile",
                description="Storage fats circulating in the bloodstream. Elevated levels are linked to pancreas inflammation and heart conditions."
            ),

            # 4. Liver Function Test Panel
            ReferenceRange(
                biomarker_name="ALT",
                alias_names="Alanine Aminotransferase,SGPT",
                min_normal=5.0,
                max_normal=35.0,
                unit="U/L",
                panel_name="Liver Function Test",
                description="Enzyme concentrated in liver cells. Higher levels point to liver injury or hepatic inflammation."
            ),
            ReferenceRange(
                biomarker_name="AST",
                alias_names="Aspartate Aminotransferase,SGOT",
                min_normal=8.0,
                max_normal=40.0,
                unit="U/L",
                panel_name="Liver Function Test",
                description="Enzyme present in liver and muscle cells. Elevated numbers indicate liver tissue stress or cellular damage."
            ),
            ReferenceRange(
                biomarker_name="Total Bilirubin",
                alias_names="TBIL,Total Bili,Bili Total,Bilirubin",
                min_normal=0.4,
                max_normal=1.0,
                unit="mg/dL",
                panel_name="Liver Function Test",
                description="Waste product from broken-down red blood cells. High levels induce jaundice and signal bile duct or liver blockage."
            ),
            ReferenceRange(
                biomarker_name="Direct Bilirubin",
                alias_names="DBIL,Direct Bili,Bili Direct,Conjugated Bilirubin",
                min_normal=0.0,
                max_normal=0.3,
                unit="mg/dL",
                panel_name="Liver Function Test",
                description="Conjugated bilirubin processed by liver. High levels suggest gallstones, bile duct obstruction or active liver dysfunction."
            ),
            ReferenceRange(
                biomarker_name="Alkaline Phosphatase",
                alias_names="ALP,Alk Phos,Alkaline Phos",
                min_normal=15.0,
                max_normal=112.0,
                unit="mIU/mL",
                panel_name="Liver Function Test",
                description="Enzyme in liver and bone. Elevated levels show blocked bile ducts or bone conditions."
            ),
            ReferenceRange(
                biomarker_name="Albumin",
                alias_names="ALB,Serum Albumin",
                min_normal=3.5,
                max_normal=5.0,
                unit="g/dL",
                panel_name="Liver Function Test",
                description="Primary protein synthesised by liver. Maintains fluid balances. Low levels suggest malnutrition or liver disease."
            ),

            # 5. Kidney Function Test Panel
            ReferenceRange(
                biomarker_name="Creatinine",
                alias_names="Serum Creatinine,Creat,CRE",
                min_normal=0.6,
                max_normal=1.2,
                unit="mg/dL",
                panel_name="Kidney Function Test",
                description="Byproduct of muscle breakdown cleared by kidneys. Raised values point to reduced kidney filter functionality."
            ),
            ReferenceRange(
                biomarker_name="BUN",
                alias_names="Blood Urea Nitrogen,Urea Nitrogen",
                min_normal=7.0,
                max_normal=20.0,
                unit="mg/dL",
                panel_name="Kidney Function Test",
                description="Urea waste product. High values occur during kidney stress, heart failures, or significant dehydration."
            ),
            ReferenceRange(
                biomarker_name="EGFR",
                alias_names="eGFR,Glomerular Filtration Rate,Estimated GFR",
                min_normal=90.0,
                max_normal=150.0,
                unit="mL/min/1.73m^2",
                panel_name="Kidney Function Test",
                description="Calculated rate of kidney filtering. Scores below 60 signal chronic kidney disease stages."
            ),

            # 6. Thyroid Profile Panel
            ReferenceRange(
                biomarker_name="TSH",
                alias_names="Thyroid Stimulating Hormone,Thyrotropin",
                min_normal=0.4,
                max_normal=4.0,
                unit="uIU/mL",
                panel_name="Thyroid Profile",
                description="Pituitary messenger monitoring thyroid production. High values show underactive thyroid (hypothyroidism)."
            ),
            ReferenceRange(
                biomarker_name="Free T3",
                alias_names="FT3,Free Triiodothyronine",
                min_normal=2.3,
                max_normal=4.2,
                unit="pg/mL",
                panel_name="Thyroid Profile",
                description="Active thyroid hormone circulating freely. Assessed to diagnose hyperthyroid conditions."
            ),
            ReferenceRange(
                biomarker_name="Free T4",
                alias_names="FT4,Free Thyroxine",
                min_normal=0.8,
                max_normal=1.8,
                unit="ng/dL",
                panel_name="Thyroid Profile",
                description="Main storage hormone released by thyroid. Helps isolate metabolic and auto-immune thyroid diseases."
            ),
            ReferenceRange(
                biomarker_name="C-Reactive Protein",
                alias_names="CRP,C-Reactive Protein,hs-CRP,hsCRP",
                min_normal=0.0,
                max_normal=6.0,
                unit="mg/L",
                panel_name="Inflammatory Profile",
                description="Liver-synthesised acute phase protein marking active internal systemic inflammation or acute infectious episodes."
            )
        ]

        db.add_all(seed_ranges)
        
        # Seed default test user: test@axon.com / password123
        print("Seeding default clinical test user (test@axon.com / password123)...")
        hashed = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        test_user = User(
            email="test@axon.com",
            hashed_password=hashed,
            created_at=datetime.datetime.utcnow()
        )
        db.add(test_user)
        
        db.commit()
        print(f"Successfully seeded database with {len(seed_ranges)} clinical ranges and 1 test user account!")
        
    except Exception as e:
        db.rollback()
        print(f"Failed to seed database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_and_seed_db()
