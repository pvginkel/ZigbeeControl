import { createFileRoute } from '@tanstack/react-router'
import { PROJECT_TITLE, PROJECT_DESCRIPTION } from '@/lib/consts'

export const Route = createFileRoute('/about')({
  component: AboutPage,
})

function AboutPage() {
  return (
    <div className="p-8 text-zinc-300">
      <h1 className="text-2xl font-semibold text-zinc-100">{PROJECT_TITLE}</h1>
      <p className="mt-2 text-zinc-400">{PROJECT_DESCRIPTION}</p>
    </div>
  )
}
