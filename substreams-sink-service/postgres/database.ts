import { db_host, db_port, db_name, db_user, db_password } from './config.js';
import { Sequelize } from 'sequelize';
export default new Sequelize({
    dialect: "postgres",
    logging: false,
    host: db_host,
    port: db_port,
    database: db_name,
    username: db_user,
    password: db_password
});