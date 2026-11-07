// shuffles the order of the fields in the HTML page

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
        elements.push(`<span class="label" style="order: ${2 * k}">${row.label}</span>`);
        elements.push(`<span class="value" style="order: ${2 * k + 1}">${row.value}</span>`); 
        }
    // C: shuffle it and return the HTML
        const shuffledElements = shuffle(elements, rng);


        return "    <div class=\"fields\">\n" + shuffledElements.map((x) => "      " + x).join("\n") + "\n    </div>";    }
module.exports = { fieldRows };