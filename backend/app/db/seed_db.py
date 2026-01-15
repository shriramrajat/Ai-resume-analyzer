
import json
import os
from sqlalchemy.orm import Session
from app.db.models import SkillsMaster, SkillCategory

def seed_skills(db: Session):
    """
    Loads skills from data/skills_master_seed.json into the database.
    Idempotent: Checks if skill exists before adding.
    """
    seed_file = "data/skills_master_seed.json"
    if not os.path.exists(seed_file):
        print(f"Seed file {seed_file} not found.")
        return

    with open(seed_file, "r") as f:
        skills_data = json.load(f)
    
    print(f"Seeding {len(skills_data)} skills...")
    
    count = 0
    for skill in skills_data:
        # Check if exists
        exists = db.query(SkillsMaster).filter(SkillsMaster.name == skill["name"]).first()
        if not exists:
            # Validate category against Enum
            try:
                # This ensures we don't insert invalid categories
                # If json has 'database' but Enum doesn't, we map it or fail.
                # In previous step I mapped them to 'tool' in the JSON itself.
                category_enum = SkillCategory(skill["category"]) 
                
                new_skill = SkillsMaster(name=skill["name"], category=category_enum)
                db.add(new_skill)
                count += 1
            except ValueError:
                print(f"Skipping invalid category for {skill['name']}: {skill['category']}")
    
    db.commit()
    print(f"Successfully seeded {count} new skills.")
