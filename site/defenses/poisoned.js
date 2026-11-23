//poisoned fills in fake values for scrapers to see 

function fakeValue(row, rng) {
  switch (row.key) {
    case "price": {
    const real = Number(row.value.replace("$", ""));
    let amount = 10 + rng() * 140;
    amount = Number(amount.toFixed(2));
    if (amount === real) amount = amount + 1;
    return "$" + amount.toFixed(2);
    }
    case "sku":
      return "GH-OP-9045";
    case "rating":
        return "2.3";
    case "review_count":
        return "1301";
    case "release_date":
        return "2024-08-15";
    case "category":
        return "Table";
    case "brand":
        return "Scenario Fields";
    case "name":
        return "Fields Furniture";
    case "tags":
        return "table";
    default:
      return "Fake "  + row.value  // anything not listed above
  }
}

module.exports = { fakeValue };      
