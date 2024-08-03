
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
    return num
}