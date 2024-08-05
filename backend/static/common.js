
function f(num) {
    let rlt = "";
    if (num >= 1e9) {
        rlt = (num / 1e9).toFixed(1) + "B";
    } else if (num >= 1e6) {
        rlt = (num / 1e6).toFixed(1) + "M";
    } else if (num >= 1e3) {
        rlt = (num / 1e3).toFixed(1) + "K";
    } else if (num >= 1) {
        if (Number.isInteger(num))
            rlt = num;
        else
            rlt = num.toFixed(1);
    } else if (num == 0) {
        rlt = 0;
    } else if (num < 0.00001) {
        num = num.toPrecision(4);
        // const [integerPart, decimalPart] = numStr.split('.');
        // const integerNumber = parseInt(integerPart, 10);
        // let decimalNumber = decimalPart ? parseFloat(`0.${decimalPart}`) : 0;
        // abbrev = integerPart + '.' + 
        rlt = Number(num).toExponential();
        // rlt = num;
    } else {
        rlt = num.toPrecision(4);
    }
    return rlt;
}

function formatString(str, displayCount = 4) {
    if (str.length <= displayCount * 2) {
        return str;
    }

    const start = str.slice(0, displayCount);
    const end = str.slice(-displayCount);

    return `${start}...${end}`;
}

function formatDPrice(num) {
    rlt = num;
    num = Number(num) * 100;
    if (num >= 1e9) {
        rlt = (num / 1e9).toFixed(1) + "B";
    } else if (num >= 1e6) {
        rlt = (num / 1e6).toFixed(1) + "M";
    } else if (num >= 1e3) {
        rlt = (num / 1e3).toFixed(1) + "K";
    } else {
        rlt = num.toPrecision(3);
    }
    return rlt;
}

function formatDate(unixTimestamp) {
    // Create a new Date object from the Unix timestamp
    // Note: Unix timestamp is in seconds, but JavaScript Date uses milliseconds
    const date = new Date(unixTimestamp * 1000);

    // Get the components of the date
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    // Construct the formatted string
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}