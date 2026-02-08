import { IncidentList } from '@/components/overview/incident-list';
import { KpiCards } from '@/components/overview/kpi-cards';
import { ServiceGrid } from '@/components/overview/service-grid';
import { fetchActiveIncidents, fetchServiceSummary } from '@/lib/data';

export default async function HomePage() {
  const [incidents, services] = await Promise.all([fetchActiveIncidents(), fetchServiceSummary()]);

  return (
    <section className="space-y-8">
      <KpiCards incidents={incidents} services={services} />
      <ServiceGrid services={services.slice(0, 4)} />
      <IncidentList incidents={incidents} />
    </section>
  );
}
