import { notFound } from 'next/navigation';

import { HypothesesCard } from '@/components/incidents/hypotheses-card';
import { IncidentHeader } from '@/components/incidents/incident-header';
import { TimelineChart } from '@/components/incidents/timeline-chart';
import { fetchIncident, fetchIncidentAnalysis, fetchIncidentTimeline } from '@/lib/data';

export default async function IncidentDetailPage({ params }: { params: { incidentId: string } }) {
  const { incidentId } = params;
  try {
    const [incident, timeline, analysis] = await Promise.all([
      fetchIncident(incidentId),
      fetchIncidentTimeline(incidentId),
      fetchIncidentAnalysis(incidentId),
    ]);

    return (
      <section className="space-y-6">
        <IncidentHeader incident={incident} />
        <TimelineChart timeline={timeline} />
        <HypothesesCard analysis={analysis} />
      </section>
    );
  } catch (error) {
    notFound();
  }
}
