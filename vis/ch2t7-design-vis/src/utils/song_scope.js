const SONG_START = 960;
const SONG_END = 1279;

function periodTouchesSong(period) {
  return period?.start <= SONG_END && (period.end ?? period.start) >= SONG_START;
}

export function filterSongData(data) {
  const timepoints = {};
  const visibleTimepointIds = new Set();
  const visibleEntityIds = new Set();
  for (const [entityId, items] of Object.entries(data.timepoints || {})) {
    const visible = items.filter((item) => item.time_type !== "pre_song");
    timepoints[entityId] = visible;
    if (visible.length) visibleEntityIds.add(Number(entityId));
    visible.forEach((item) => visibleTimepointIds.add(item.id));
  }

  const filterEdges = (edges, endpointIds) => (edges || []).flatMap((edge) => {
    const states = (edge.states || []).filter((state) => (
      visibleTimepointIds.has(state.subject_timepoint_id)
      || visibleTimepointIds.has(state.object_timepoint_id)
    ));
    if (!states.length && !(edge.periods || []).some(periodTouchesSong)) return [];
    endpointIds(edge).forEach((id) => visibleEntityIds.add(id));
    return [{ ...edge, states }];
  });

  const hierarchyEdges = filterEdges(data.hierarchyEdges, (edge) => [edge.parent, edge.child]);
  const staffEdges = filterEdges(data.staffEdges, (edge) => [edge.org, edge.official]);
  const evolutionEdges = filterEdges(data.evolutionEdges, (edge) => [edge.source, edge.target]);
  const collectiveInstanceEdges = filterEdges(
    data.collectiveInstanceEdges,
    (edge) => [edge.collective, edge.instance],
  );

  return {
    ...data,
    entities: (data.entities || []).filter((entity) => visibleEntityIds.has(entity.id)),
    timepoints,
    hierarchyEdges,
    staffEdges,
    evolutionEdges,
    collectiveInstanceEdges,
  };
}
