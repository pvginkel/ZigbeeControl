import { createFileRoute } from '@tanstack/react-router'
import { TabManager } from '@/components/tabs/tab-manager'

export const Route = createFileRoute('/')({
  component: IndexPage,
})

function IndexPage() {
  return <TabManager />
}
