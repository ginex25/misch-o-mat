import {LiquidModel} from "./Liquid.js";

export default class ConnectionModel {
    constructor(conn) {
        this.id = conn.connection;
        this.offset = conn.offset;
        this.connected = !!conn.liquid_name;
        this.liquid = this.connected
            ? new LiquidModel(conn.liquid_id, conn.liquid_name, conn.liquid_alcohol, conn.liquid_level)
            : null;
        this.fill = this.connected ? conn.liquid_level : null;
    }
}