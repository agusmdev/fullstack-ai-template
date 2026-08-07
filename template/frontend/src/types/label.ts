/** Shape of the backend `GET /labels` list item (LabelResponse). */
export interface Label {
  id: string
  team_id: string
  name: string
  color: string | null
}

/** Shape of a paginated `Page<LabelResponse>` from fastapi_pagination. */
export interface LabelsResponse {
  items: Label[]
  total: number
  page: number
  size: number
  pages: number
}
