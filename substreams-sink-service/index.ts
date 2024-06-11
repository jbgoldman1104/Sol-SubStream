import { setup, http } from "substreams-sink";

import { type ActionOptions } from "./bin/cli.js";

import { initialize, insertTrades } from './postgres/trade.js'
import { getTokenMetadata } from './utils/utils.js'

if (false) {
    await initialize()
}

export async function action(options: ActionOptions) {
    const { emitter } = await setup(options);
    emitter.on("anyMessage", insertTrades);
    http.listen(options);
    await emitter.start();
    http.server.close()
}

getTokenMetadata("Exvw13JFc3kBFLaiVgQncwg2nk1KnjdFkePFiF73a1iq").then(() => { }).catch(error => { });