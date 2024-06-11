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

getTokenMetadata("DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2").then(() => { }).catch(error => { });