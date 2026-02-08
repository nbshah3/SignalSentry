import { OverviewClient } from '@/components/overview/overview-client';
import { fetchActiveIncidents, fetchServiceSummary } from '@/lib/data';

export default async function HomePage() {
  const [incidents, services] = await Promise.all([fetchActiveIncidents(), fetchServiceSummary()]);
  return <OverviewClient initialIncidents={incidents} initialServices={services} />;
}
