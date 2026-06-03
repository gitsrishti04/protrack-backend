import numpy as np
import pandas as pd

np.random.seed(42)
n = 500

total_tasks = np.random.randint(5, 50, n)
completed_tasks = (total_tasks * np.random.uniform(0.1, 1.0, n)).astype(int)
delayed_tasks = (total_tasks * np.random.uniform(0.0, 0.4, n)).astype(int)
team_size = np.random.randint(2, 15, n)
completion_pct = (completed_tasks / total_tasks * 100).astype(int)
task_completion_rate = completed_tasks / total_tasks
delayed_task_rate = delayed_tasks / total_tasks
deadline_days = np.random.randint(30, 365, n)

# days_remaining — projects with low completion and high delay rate take longer
days_remaining = (
    deadline_days * (1 - task_completion_rate) * np.random.uniform(0.8, 1.3, n)
).astype(int)
days_remaining = np.clip(days_remaining, 1, 400)

# is_delayed label — realistic rule
is_delayed = ((delayed_task_rate > 0.3) | (completion_pct < 25)).astype(int)

## convert in df
df = pd.DataFrame({
    "total_tasks": total_tasks,
    "completed_tasks": completed_tasks,
    "delayed_tasks": delayed_tasks,
    "team_size": team_size,
    "completion_pct": completion_pct,
    "task_completion_rate": task_completion_rate,
    "delayed_task_rate": delayed_task_rate,
    "deadline_days": deadline_days,
    "days_remaining": days_remaining,
    "is_delayed": is_delayed
})

## now converted in csv
df.to_csv("app/ml/synthetic_completion.csv", index=False)
print(f"Generated {len(df)} rows → app/ml/synthetic_completion.csv")
print(df.head())
print(f"\nDelayed projects: {is_delayed.sum()} / {n}")



