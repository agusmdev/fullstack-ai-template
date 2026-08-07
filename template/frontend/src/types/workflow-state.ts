/** Behavioural type of a workflow state (mirrors the backend enum). */
export type WorkflowStateType =
  | 'backlog'
  | 'unstarted'
  | 'started'
  | 'completed'
  | 'canceled'

/** Shape of the backend `GET /workflow-states` list item (WorkflowStateResponse). */
export interface WorkflowState {
  id: string
  team_id: string
  name: string
  type: WorkflowStateType
  position: number
  color: string | null
}

/** Shape of a paginated `Page<WorkflowStateResponse>` from fastapi_pagination. */
export interface WorkflowStatesResponse {
  items: WorkflowState[]
  total: number
  page: number
  size: number
  pages: number
}
