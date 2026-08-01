import assert from "node:assert/strict";
import test from "node:test";

import { filterSongData } from "./song_scope.js";
import { filterSongDataset } from "../../../song-bureaucracy-visualization-v2/src/utils/song_scope.js";

test("8050只向界面保留宋代时间点及有宋代证据的关系", () => {
  const data = filterSongData({
    entities: [{ id: 1 }, { id: 2 }, { id: 3 }],
    timepoints: {
      1: [{ id: 10, time_type: "pre_song" }],
      2: [{ id: 20, time_type: "exact" }],
      3: [{ id: 30, time_type: "pre_song" }],
    },
    hierarchyEdges: [{
      parent: 1,
      child: 2,
      states: [{ subject_timepoint_id: 10, object_timepoint_id: 20 }],
      periods: [],
    }],
    staffEdges: [],
  });
  assert.deepEqual(data.entities.map((entity) => entity.id), [1, 2]);
  assert.equal(data.timepoints[1].length, 0);
  assert.equal(data.hierarchyEdges.length, 1);
});

test("8051排除纯宋前事件和纯宋前实体", () => {
  const dataset = filterSongDataset({
    entities: [{ id: 1, eventCount: 1 }, { id: 2, eventCount: 1 }, { id: 3, eventCount: 1 }],
    events: [
      { id: 10, entityId: 1, timeType: "pre_song" },
      { id: 20, entityId: 2, timeType: "exact" },
      { id: 30, entityId: 3, timeType: "pre_song" },
    ],
    relations: [{
      subjectId: 10,
      objectId: 20,
      subjectEntityId: 1,
      objectEntityId: 2,
      periods: [],
    }],
  });
  assert.deepEqual(dataset.events.map((event) => event.id), [20]);
  assert.deepEqual(dataset.entities.map((entity) => entity.id), [1, 2]);
  assert.equal(dataset.relations.length, 1);
});
