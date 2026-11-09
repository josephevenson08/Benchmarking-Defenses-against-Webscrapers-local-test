// mixes every label and value of the page in the html source with a seeded shuffle and CSS order puts them back on screen

function shuffle(list, rng) {
    const arr = [...list]; // make a copy of the list
    for (let i = arr.length - 1; i >= 1; i--) 
    {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]]; 
    }
    return arr;
}

function fieldRows(rows, rng) {
    const elements = [];    // 1. build the list of elements

    for (let k = 0; k < rows.length; k++){ //2. one pass per field

        const row = rows[k];
        elements.push(`<span class="label" style="order: ${2 * k}">${row.label}</span>`); // label is even order
        elements.push(`<span class="value" style="order: ${2 * k + 1}">${row.value}</span>`);  // value is odd order
        }
    // 3. shuffle the list of elements
        const shuffledElements = shuffle(elements, rng);
    
        return "    <div class=\"fields\">\n" + shuffledElements.map((x) => "      " + x).join("\n") + "\n    </div>";    }
const style = `
    .fields { flex-direction: row; flex-wrap: wrap; }
    .fields > .label { flex: 0 0 10rem; 
        padding: 0.5rem 1rem 0.5rem 0;
        box-sizing: border-box; 
        border-bottom: 1px solid #eaeef2; }
    .fields > .value { flex: 0 0 calc(100% - 10rem);
        padding: 0.5rem 0;
        border-bottom: 1px solid #eaeef2; }`;

module.exports = { fieldRows, style };        
