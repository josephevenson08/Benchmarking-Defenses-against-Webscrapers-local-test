//honeypot defense, adds one hidden link per page to trap a path, cant be seen by real users, follows every link


function mainEnd(page, rng) { //calls once for each of the 10 pages
    return `        <a href="/trap" style="display: none;">Archive</a>`;}


module.exports = { mainEnd };        
