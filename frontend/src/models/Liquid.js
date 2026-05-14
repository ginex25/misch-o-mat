export class LiquidModel {
    constructor(id, name, isAlcohol, fuelfilllstand_ml) {
        this.id = id;
        this.name = name;
        this.isAlcohol = isAlcohol;
        this.fill = fuelfilllstand_ml;
    }
}

/**
 * @param {Object} data - Response von /api/liquids
 * @returns {LiquidModel[]}
 */
export function parseLiquids(data) {
    return Object.entries(data).map(
        ([id, liquid]) => new LiquidModel(id, liquid.name, liquid.alkohol, liquid.fuellstand_ml)
    ).sort((a, b) => a.name.localeCompare(b.name, "de"));
}