//! Planning engine — hierarchical goal decomposition.
//!
//! The hierarchy is: `Goal → Objective → Task → Subtask → Action`. The engine
//! stores goals, decomposes them into an executable tree (a deterministic stub
//! here, an LLM in the full design), analyses task dependencies, and repairs
//! plans when steps fail.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Lifecycle status shared by every level of the plan tree.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Status {
    Pending,
    Active,
    Blocked,
    Done,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    pub id: String,
    pub description: String,
    /// Optional tool/capability this action needs (e.g. "WriteFile").
    pub tool: Option<String>,
    pub status: Status,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subtask {
    pub id: String,
    pub description: String,
    pub actions: Vec<Action>,
    pub status: Status,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: String,
    pub description: String,
    pub subtasks: Vec<Subtask>,
    /// Ids of other tasks that must complete first.
    pub depends_on: Vec<String>,
    pub status: Status,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Objective {
    pub id: String,
    pub description: String,
    pub tasks: Vec<Task>,
    pub status: Status,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Goal {
    pub id: String,
    pub description: String,
    pub objectives: Vec<Objective>,
    pub status: Status,
}

fn id() -> String {
    Uuid::new_v4().to_string()
}

/// Holds every goal the daemon is pursuing.
#[derive(Default)]
pub struct PlanningEngine {
    goals: HashMap<String, Goal>,
}

impl PlanningEngine {
    pub fn new() -> Self {
        Self::default()
    }

    /// Register a new, undecomposed goal. Returns its id.
    pub fn create_goal(&mut self, description: impl Into<String>) -> String {
        let goal = Goal {
            id: id(),
            description: description.into(),
            objectives: Vec::new(),
            status: Status::Pending,
        };
        let gid = goal.id.clone();
        self.goals.insert(gid.clone(), goal);
        gid
    }

    pub fn get(&self, goal_id: &str) -> Option<&Goal> {
        self.goals.get(goal_id)
    }

    pub fn goals(&self) -> Vec<&Goal> {
        self.goals.values().collect()
    }

    /// Decompose a goal into a default objective/task/subtask/action tree.
    ///
    /// This is a deterministic stub: it produces a "plan → execute → verify"
    /// skeleton so downstream systems have something concrete to schedule. A
    /// real implementation would call an LLM planner.
    pub fn decompose(&mut self, goal_id: &str) -> bool {
        let Some(goal) = self.goals.get_mut(goal_id) else {
            return false;
        };
        let base = goal.description.clone();

        let plan_task = Task {
            id: id(),
            description: format!("Plan approach for: {base}"),
            subtasks: vec![Subtask {
                id: id(),
                description: "Gather context and constraints".into(),
                actions: vec![Action {
                    id: id(),
                    description: "Search relevant memory and workspace".into(),
                    tool: Some("SearchCode".into()),
                    status: Status::Pending,
                }],
                status: Status::Pending,
            }],
            depends_on: vec![],
            status: Status::Pending,
        };

        let exec_task = Task {
            id: id(),
            description: format!("Execute: {base}"),
            subtasks: vec![Subtask {
                id: id(),
                description: "Apply changes".into(),
                actions: vec![Action {
                    id: id(),
                    description: "Write files / run commands".into(),
                    tool: Some("WriteFile".into()),
                    status: Status::Pending,
                }],
                status: Status::Pending,
            }],
            depends_on: vec![plan_task.id.clone()],
            status: Status::Pending,
        };

        let verify_task = Task {
            id: id(),
            description: format!("Verify: {base}"),
            subtasks: vec![Subtask {
                id: id(),
                description: "Validate outcome".into(),
                actions: vec![Action {
                    id: id(),
                    description: "Run tests / checks".into(),
                    tool: Some("ExecuteCommand".into()),
                    status: Status::Pending,
                }],
                status: Status::Pending,
            }],
            depends_on: vec![exec_task.id.clone()],
            status: Status::Pending,
        };

        goal.objectives = vec![Objective {
            id: id(),
            description: format!("Deliver: {base}"),
            tasks: vec![plan_task, exec_task, verify_task],
            status: Status::Pending,
        }];
        goal.status = Status::Active;
        true
    }

    /// Dependency analysis: return the descriptions of tasks that are runnable
    /// now (all dependencies are `Done`).
    pub fn ready_tasks(&self, goal_id: &str) -> Vec<String> {
        let Some(goal) = self.goals.get(goal_id) else {
            return vec![];
        };
        let done: std::collections::HashSet<&str> = goal
            .objectives
            .iter()
            .flat_map(|o| &o.tasks)
            .filter(|t| t.status == Status::Done)
            .map(|t| t.id.as_str())
            .collect();

        goal.objectives
            .iter()
            .flat_map(|o| &o.tasks)
            .filter(|t| t.status == Status::Pending)
            .filter(|t| t.depends_on.iter().all(|d| done.contains(d.as_str())))
            .map(|t| t.description.clone())
            .collect()
    }

    /// Plan repair stub: mark a failed task, then re-open its downstream
    /// dependents so they can be re-planned. Returns the number of tasks reset.
    pub fn repair(&mut self, goal_id: &str, failed_task_id: &str) -> usize {
        let Some(goal) = self.goals.get_mut(goal_id) else {
            return 0;
        };
        let mut reset = 0;
        for obj in &mut goal.objectives {
            for task in &mut obj.tasks {
                if task.id == failed_task_id {
                    task.status = Status::Failed;
                    reset += 1;
                } else if task.depends_on.iter().any(|d| d == failed_task_id) {
                    task.status = Status::Pending;
                    reset += 1;
                }
            }
        }
        if reset > 0 {
            goal.status = Status::Active;
        }
        reset
    }
}

