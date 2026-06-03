"""
Generate synthetic training data for Resource Allocation Prediction.

When a new project is entered, the model predicts:
  - required_developers  : how many developers are needed
  - estimated_days       : estimated project timeline in days
  - required_skill_sets  : list of skill sets required (encoded as flags)

Input features (things known at project creation time):
  - project_type         : 0=web, 1=mobile, 2=data/ml, 3=devops, 4=embedded
  - complexity           : 1=low, 2=medium, 3=high
  - total_tasks          : estimated number of tasks
  - has_frontend         : 1/0
  - has_backend          : 1/0
  - has_ml               : 1/0
  - has_mobile           : 1/0
  - has_devops           : 1/0
  - has_database         : 1/0
  - deadline_days        : days given to complete
"""

import numpy as np
import pandas as pd

np.random.seed(42)
n = 800

# ── Input features ────────────────────────────────────────────────────────
project_type   = np.random.randint(0, 5, n)          # 0=web,1=mobile,2=ml,3=devops,4=embedded
complexity     = np.random.randint(1, 4, n)           # 1=low, 2=medium, 3=high
total_tasks    = complexity * np.random.randint(5, 20, n)  # more complex = more tasks
deadline_days  = np.random.randint(30, 365, n)

# Skill flags — derived from project type with some noise
has_frontend = ((project_type == 0) | (project_type == 1) | (np.random.rand(n) > 0.6)).astype(int)
has_backend  = ((project_type == 0) | (project_type == 2) | (np.random.rand(n) > 0.5)).astype(int)
has_ml       = ((project_type == 2) | (np.random.rand(n) > 0.75)).astype(int)
has_mobile   = ((project_type == 1) | (np.random.rand(n) > 0.8)).astype(int)
has_devops   = ((project_type == 3) | (np.random.rand(n) > 0.6)).astype(int)
has_database = ((project_type != 3) | (np.random.rand(n) > 0.4)).astype(int)

# ── Target: required_developers ───────────────────────────────────────────
# Base: complexity drives team size
base_devs = complexity * 2

# Each skill area adds ~1 developer
skill_sum = has_frontend + has_backend + has_ml + has_mobile + has_devops + has_database
required_developers = (base_devs + (skill_sum * 0.5) + np.random.randint(0, 3, n)).astype(int)
required_developers = np.clip(required_developers, 2, 15)

# ── Target: estimated_days ────────────────────────────────────────────────
# More tasks + higher complexity = more days, offset by team size
estimated_days = (
    total_tasks * complexity * 1.5
    / (required_developers * 0.8)
    * np.random.uniform(0.85, 1.2, n)
).astype(int)
estimated_days = np.clip(estimated_days, 14, 365)

# ── Build DataFrame ───────────────────────────────────────────────────────
df = pd.DataFrame({
    "project_type":         project_type,
    "complexity":           complexity,
    "total_tasks":          total_tasks,
    "deadline_days":        deadline_days,
    "has_frontend":         has_frontend,
    "has_backend":          has_backend,
    "has_ml":               has_ml,
    "has_mobile":           has_mobile,
    "has_devops":           has_devops,
    "has_database":         has_database,
    # Targets
    "required_developers":  required_developers,
    "estimated_days":       estimated_days,
})

df.to_csv("app/ml/synthetic_resources.csv", index=False)
print(f"Generated {len(df)} rows → app/ml/synthetic_resources.csv")
print(df.head())
print(f"\nAvg developers needed : {required_developers.mean():.1f}")
print(f"Avg estimated days    : {estimated_days.mean():.1f}")
print(f"\nSkill distribution:")
print(f"  Frontend : {has_frontend.sum()} projects")
print(f"  Backend  : {has_backend.sum()} projects")
print(f"  ML/AI    : {has_ml.sum()} projects")
print(f"  Mobile   : {has_mobile.sum()} projects")
print(f"  DevOps   : {has_devops.sum()} projects")
print(f"  Database : {has_database.sum()} projects")
