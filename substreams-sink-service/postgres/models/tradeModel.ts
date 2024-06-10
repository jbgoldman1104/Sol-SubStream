// src/models/user.ts
import { Model, Sequelize, DataTypes } from 'sequelize';

export default class TradeData extends Model {
  public id?: number
  public blockDate!: Date
  public blockTime!: number
  public blockSlot!: number
  public txId!: string
  public signer!: string
  public poolAddress!: string
  public baseMint!: string
  public quoteMint!: string
  public baseAmount!: number
  public quoteAmount!: number
  public outerProgram?: string
  public innerProgram?: string
  public baseReserve!: number
  public quoteReserve!: number
}

export const TradeDataMap = (sequelize: Sequelize) => {
  TradeData.init({
    id: {
      type: DataTypes.BIGINT,
      autoIncrement: true,
      primaryKey: true
    },
    blockDate: {
      type: DataTypes.DATE
    },
    blockTime: {
      type: DataTypes.INTEGER
    },
    blockSlot: {
      type: DataTypes.INTEGER
    },
    txId: {
      type: DataTypes.STRING(90)
    },
    signer: {
      type: DataTypes.STRING(45)
    },
    poolAddress: {
      type: DataTypes.STRING(45)
    },
    baseMint: {
      type: DataTypes.STRING(45)
    },
    quoteMint: {
      type: DataTypes.STRING(45)
    },
    baseAmount: {
      type: DataTypes.FLOAT
    },
    quoteAmount: {
      type: DataTypes.FLOAT
    },
    outerProgram: {
      type: DataTypes.STRING(45),
      allowNull: true
    },
    innerProgram: {
      type: DataTypes.STRING(45),
      allowNull: true
    },
    baseReserve: {
      type: DataTypes.FLOAT
    },
    quoteReserve: {
      type: DataTypes.FLOAT
    }
  }, {
    sequelize,
    tableName: 'trade',
    timestamps: false
  });
  TradeData.sync();
}