import { setup, http } from "substreams-sink";

import { type ActionOptions } from "./bin/cli.js";

import { initialize, insertTrades } from './postgres/trade.js'

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
