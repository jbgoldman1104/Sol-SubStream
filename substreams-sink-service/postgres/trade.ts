import TradeData, { TradeDataMap } from './models/tradeModel.js'
import database from './database.js';

const createQuery =
    "CREATE TABLE trade ( \
    \"id\" SERIAL PRIMARY KEY,\
    \"blockDate\" TIMESTAMP,\
    \"blockTime\" INT NOT NULL,\
    \"blockSlot\" INT NOT NULL,\
    \"txId\" VARCHAR(90) NOT NULL,\
    \"signer\" VARCHAR(45) NOT NULL,\
    \"poolAddress\" VARCHAR(45) NOT NULL,\
    \"baseMint\" VARCHAR(45) NOT NULL,\
    \"quoteMint\" VARCHAR(45) NOT NULL,\
    \"baseAmount\" NUMERIC NOT NULL,\
    \"quoteAmount\" NUMERIC NOT NULL,\
    \"instructionType\" VARCHAR(20),\
    \"outerProgram\" VARCHAR(45),\
    \"innerProgram\" VARCHAR(45),\
    \"baseReserve\" NUMERIC NOT NULL,\
    \"quoteReserve\" NUMERIC NOT NULL\
);"

export async function initialize() {
    try {
        await database.query(createQuery)
        console.log('Schema script executed successfully.');
    } catch (error) {
        console.error('Error executing schema creation script:', error);
    }
}

export async function insertTrades(message: any) {
    try {
        let unix_timestamp = message?.data[0].blockTime;
        var date = new Date(unix_timestamp * 1000 + 9 * 3600000);
        // console.log('insertTrades :>> ', message?.data[0]);
        let t1 = performance.now()
        TradeDataMap(database);
        TradeData.bulkCreate(message?.data)
        let t2 = performance.now()
        console.log('insertTrades :>> ', message?.data[0].blockSlot, message?.data[0].blockTime, '  ',
            date.toISOString().replace(/[T]/g, ' ').substring(0, 19), '  ', (t2 - t1).toFixed(2), ' ms');
    } catch (error) {
        console.error('error :>> ', error);
    }
}
