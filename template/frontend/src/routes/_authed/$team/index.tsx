import { createFileRoute, redirect } from '@tanstack/react-router'

/**
 * `/$team` — redirects to the team's issues view. The sidebar links always
 * include a section, but a bare team URL (typed or deep-linked) lands here.
 */
export const Route = createFileRoute('/_authed/$team/')({
  beforeLoad: ({ params }) => {
    throw redirect({ to: '/$team/issues', params: { team: params.team }, replace: true })
  },
})
