import {ODSample} from "./odsample";

self.onmessage = function(message) {
    // console.log(message.data);
    let result = ODSample(...message.data)
    self.postMessage(result);
}
