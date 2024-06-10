import TradeData, { TradeDataMap } from './models/tradeModel.js'
import database from './database.js';
import type { Transaction } from 'sequelize';

const createQuery =
    "CREATE TABLE trade ( \
    id SERIAL PRIMARY KEY,\
    id SERIAL PRIMARY KEY,\
    blockDate TIMESTAMP,\
    blockTime INT NOT NULL,\
    blockSlot INT NOT NULL,\
    txId VARCHAR(255) NOT NULL,\
    signer VARCHAR(255) NOT NULL,\
    poolAddress VARCHAR(255) NOT NULL,\
    baseMint VARCHAR(255) NOT NULL,\
    quoteMint VARCHAR(255) NOT NULL,\
    baseAmount NUMERIC NOT NULL,\
    quoteAmount NUMERIC NOT NULL,\
    outerProgram VARCHAR(255),\
    innerProgram VARCHAR(255),\
    baseReserve NUMERIC NOT NULL,\
    quoteReserve NUMERIC NOT NULL,\
    quotePrice NUMERIC NOT NULL \
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
        console.log('insertTrades :>> ', message?.data[0].blockSlot);
        // console.log('insertTrades :>> ', message?.data[0]);
        TradeDataMap(database);
        TradeData.bulkCreate(message?.data)
    } catch (error) {
        console.error('error :>> ', error);
    }
}
