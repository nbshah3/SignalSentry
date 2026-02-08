import { OverviewClient } from '@/components/overview/overview-client';
import { ensureDemoData, fetchActiveIncidents, fetchServiceSummary } from '@/lib/data';

export default async function HomePage() {
  const seeded = await ensureDemoData();
  const [incidents, services] = await Promise.all([fetchActiveIncidents(), fetchServiceSummary()]);
  return (
    <OverviewClient
      initialIncidents={incidents}
      initialServices={services}
      initialSeedMessage={seeded ? 'Demo data seeded' : null}
    />
  );
}
