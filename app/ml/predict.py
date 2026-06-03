import joblib
import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load pre-trained models
delay_model = joblib.load(os.path.join(BASE_DIR, "delay_model.pkl"))
completion_model = joblib.load(os.path.join(BASE_DIR, "completion_model.pkl"))


def predict_delay_risk(features_dict):
    """
    Predict if a project will be delayed.
    
    Args:
        features_dict: dict with keys:
            - total_tasks
            - completed_tasks
            - delayed_tasks
            - team_size
            - completion_pct
            - task_completion_rate
            - delayed_task_rate
    
    Returns:
        dict with:
            - is_delayed: 0 (on track) or 1 (delayed)
            - probability: confidence score
    """
    feature_order = [
        "total_tasks",
        "completed_tasks",
        "delayed_tasks",
        "team_size",
        "completion_pct",
        "task_completion_rate",
        "delayed_task_rate"
    ]
    
    # Extract features in correct order
    X = [[features_dict[f] for f in feature_order]]
    
    # Predict
    prediction = delay_model.predict(X)[0]
    probability = delay_model.predict_proba(X)[0]
    
    return {
        "is_delayed": int(prediction),
        "probability_on_track": float(probability[0]),
        "probability_delayed": float(probability[1])
    }


def predict_completion_time(features_dict):
    """
    Predict days remaining to complete the project.
    
    Args:
        features_dict: dict with keys (same as above)
    
    Returns:
        dict with:
            - days_remaining: predicted days to completion
    """
    feature_order = [
        "total_tasks",
        "completed_tasks",
        "delayed_tasks",
        "team_size",
        "completion_pct",
        "task_completion_rate",
        "delayed_task_rate"
    ]
    
    # Extract features in correct order
    X = [[features_dict[f] for f in feature_order]]
    
    # Predict
    days_pred = completion_model.predict(X)[0]
    
    return {
        "days_remaining": max(1, int(days_pred))  # Ensure at least 1 day
    }


def predict_all(features_dict):
    """
    Get both delay risk and completion time predictions.
    
    Args:
        features_dict: dict with feature keys
    
    Returns:
        dict with both predictions combined
    """
    delay_result = predict_delay_risk(features_dict)
    completion_result = predict_completion_time(features_dict)
    
    return {
        **delay_result,
        **completion_result
    }


# ── Resource Allocation Models ────────────────────────────────────────────

resource_devs_model = joblib.load(os.path.join(BASE_DIR, "resource_devs_model.pkl"))
resource_days_model = joblib.load(os.path.join(BASE_DIR, "resource_days_model.pkl"))

# Skill set labels mapped to feature flags
SKILL_LABELS = {
    "has_frontend": "Frontend Development",
    "has_backend":  "Backend Development",
    "has_ml":       "Machine Learning / AI",
    "has_mobile":   "Mobile Development",
    "has_devops":   "DevOps / Infrastructure",
    "has_database": "Database Administration",
}

PROJECT_TYPE_LABELS = {
    0: "Web Application",
    1: "Mobile Application",
    2: "Data / ML Project",
    3: "DevOps / Infrastructure",
    4: "Embedded / IoT",
}


def predict_resource_allocation(features_dict):
    """
    Predict required resources for a new project.

    Args:
        features_dict: dict with keys:
            - project_type   : int  0=web, 1=mobile, 2=ml, 3=devops, 4=embedded
            - complexity     : int  1=low, 2=medium, 3=high
            - total_tasks    : int  estimated number of tasks
            - deadline_days  : int  days available to complete
            - has_frontend   : 0/1
            - has_backend    : 0/1
            - has_ml         : 0/1
            - has_mobile     : 0/1
            - has_devops     : 0/1
            - has_database   : 0/1

    Returns:
        dict with:
            - required_developers : int
            - estimated_days      : int
            - required_skill_sets : list[str]
            - project_type_label  : str
            - complexity_label    : str
    """
    feature_order = [
        "project_type",
        "complexity",
        "total_tasks",
        "deadline_days",
        "has_frontend",
        "has_backend",
        "has_ml",
        "has_mobile",
        "has_devops",
        "has_database",
    ]

    X = [[features_dict[f] for f in feature_order]]

    # Predict
    devs_pred = resource_devs_model.predict(X)[0]
    days_pred = resource_days_model.predict(X)[0]

    # Build required skill sets from flags
    required_skills = [
        label
        for flag, label in SKILL_LABELS.items()
        if features_dict.get(flag, 0) == 1
    ]

    complexity_map = {1: "Low", 2: "Medium", 3: "High"}

    return {
        "required_developers": max(1, int(round(devs_pred))),
        "estimated_days":      max(7, int(round(days_pred))),
        "required_skill_sets": required_skills,
        "project_type_label":  PROJECT_TYPE_LABELS.get(features_dict.get("project_type", 0), "Unknown"),
        "complexity_label":    complexity_map.get(features_dict.get("complexity", 2), "Medium"),
    }
