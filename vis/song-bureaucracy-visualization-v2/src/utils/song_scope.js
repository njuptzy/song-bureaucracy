const SONG_START = 960;
const SONG_END = 1279;

function periodTouchesSong(period) {
  return period?.start <= SONG_END && (period.end ?? period.start) >= SONG_START;
}

export function filterSongDataset(dataset) {
  const events = (dataset.events || []).filter((event) => event.timeType !== "pre_song");
  const eventIds = new Set(events.map((event) => event.id));
  const entityIds = new Set(events.map((event) => event.entityId));
  const relations = (dataset.relations || []).filter((relation) => (
    eventIds.has(relation.subjectId)
    || eventIds.has(relation.objectId)
    || (relation.periods || []).some(periodTouchesSong)
  ));
  relations.forEach((relation) => {
    entityIds.add(relation.subjectEntityId);
    entityIds.add(relation.objectEntityId);
  });

  const eventCounts = new Map();
  events.forEach((event) => eventCounts.set(event.entityId, (eventCounts.get(event.entityId) || 0) + 1));
  const entities = (dataset.entities || [])
    .filter((entity) => entityIds.has(entity.id))
    .map((entity) => ({ ...entity, eventCount: eventCounts.get(entity.id) || 0 }));

  return { ...dataset, entities, events, relations };
}
