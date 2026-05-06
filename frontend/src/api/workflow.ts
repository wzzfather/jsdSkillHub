import { api } from "./client";
import type { WorkflowOverview, WorkflowStep } from "./types";

export async function fetchWorkflowSteps() {
  return api.get<WorkflowStep[]>("/workflow/steps");
}

export async function fetchWorkflowOverview() {
  return api.get<WorkflowOverview>("/workflow/overview");
}
