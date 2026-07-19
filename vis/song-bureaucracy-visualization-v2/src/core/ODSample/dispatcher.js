import ODSampleWorker from "./odsample.worker.js?worker";

export class ODSampleDispatcher {
  constructor() {
    this._queue = [];
    this._worker = new ODSampleWorker();
    this._worker.onmessage = (e) => this._queue.shift().resolve(e.data);
    this._worker.onerror = (e) => this._queue.shift().reject(e.error);
  }

  dispatch(...args) {
    return new Promise((resolve, reject) => {
      this._queue.push({resolve, reject});
      this._worker.postMessage(args);
    });
  }
}
