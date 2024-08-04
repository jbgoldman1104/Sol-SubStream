const timeFrames = [
  { text: "6m", resolution: "120" },
  { text: "3m", resolution: "60" },
  { text: "1m", resolution: "30" },
  {
    text: "5d",
    resolution: "D",
    description: "5 days",
  },
  {
    text: "1d",
    resolution: "D",
    description: "1 day",
  },
];

const TIMEZONE = {
  '-10': ['Pacific/Honolulu'],
  '-8': ['America/Anchorage', 'America/Juneau'],
  '-7': ['America/Los_Angeles', 'America/Phoenix', 'America/Vancouver'],
  '-6': ['America/Mexico_City'],
  '-5': ['America/Bogota', 'America/Chicago', 'America/Lima'],
  '-4': ['America/Caracas', 'America/New_York', 'America/Santiago', 'America/Toronto'],
  '-3': ['America/Argentina/Buenos_Aires', 'America/Sao_Paulo'],
  0: ['Atlantic/Reykjavik'],
  1: ['Africa/Casablanca', 'Africa/Lagos', 'Europe/London'],
  2: [
    'Europe/Belgrade',
    'Europe/Berlin',
    'Europe/Bratislava',
    'Europe/Brussels',
    'Europe/Budapest',
    'Europe/Copenhagen',
    'Africa/Johannesburg',
    'Europe/Luxembourg',
    'Europe/Madrid',
    'Europe/Oslo',
    'Europe/Paris',
    'Europe/Rome',
    'Europe/Stockholm',
    'Europe/Warsaw',
    'Europe/Zurich',
  ],
  3: [
    'Asia/Bahrain',
    'Europe/Athens',
    'Europe/Bucharest',
    'Africa/Cairo',
    'Europe/Helsinki',
    'Europe/Istanbul',
    'Asia/Jerusalem',
    'Asia/Kuwait',
    'Europe/Moscow',
    'Asia/Nicosia',
    'Asia/Qatar',
    'Europe/Riga',
  ],
  4: ['Asia/Dubai'],
  5: ['Asia/Karachi'],
  6: ['Asia/Almaty'],
  6.5: ['Asia/Yangon'],
  7: ['Asia/Bangkok'],
  8: ['Asia/Chongqing'],
  9: ['Asia/Tokyo'],
  9.5: ['Australia/Adelaide'],
  10: ['Australia/Brisbane'],
  11: ['Pacific/Norfolk'],
  12.75: ['Pacific/Chatham'],
};

var firstBar, prevBar, curBar;

const resNames = {
  // minutes
  1: "1min",
  3: "3min",
  5: "5min",
  15: "15min",
  30: "30min",
  // hours
  60: "1h",
  120: "2h",
  240: "4h",
  360: "6h",
  720: "12h",
  // days
  "1D": "1day",
  "3D": "3day",
  "1W": "1week",
  "1M": "1month"
};

const resValues = {
  // minutes
  1: '1m',
  5: '5m',
  15: '15m',
  30: '30m',
  // hours
  60: '1h',
  120: '2h',
  360: '6h',
  // days
  "1D": '1d',
  "1W": '1w',
  "1M": '1M'
};

function printDate(mm) {
  let date = new Date(mm);
  let tt =
    date.getFullYear() +
    "/" +
    (date.getMonth() + 1) +
    "/" +
    date.getDate() +
    " " +
    date.getHours() +
    ":" +
    date.getMinutes() +
    ":" +
    date.getSeconds();
  return tt;
}

function parseFullSymbol(fullSymbol) {
  const match = fullSymbol.match(/^(\w+):(\w+)\/(\w+)$/);
  if (!match) {
    return null;
  }

  return {
    exchange: match[1],
    fromSymbol: match[2],
    toSymbol: match[3],
  };
}

const configurationData = {
  supported_resolutions: [
    // minutes
    "1",
    "5",
    "30",
    // hours
    "60",
    "120",
    "240",
    "360",
    "720",
    // days
    "D",
    "W",
    "M",
  ],
};

function convertResolution(resolution) {
  var interval;
  if (resolution === "1") {
    interval = "1m";
  } else if (resolution === "5") {
    interval = "5m";
  } else if (resolution === "10") {
    interval = "10m";
  } else if (resolution === "15") {
    interval = "15m";
  } else if (resolution === "30") {
    interval = "30m";
  } else if (resolution === "45") {
    interval = "45m";
  } else if (resolution === "60") {
    interval = "1h";
  } else if (resolution === "120") {
    interval = "2h";
  } else if (resolution === "240") {
    interval = "4h";
  } else if (resolution === "1D") {
    interval = "24h";
  } else {
    interval = resolution;
  }
  return interval;
}

const INTERVAL_SECONDS = {
  "1m": 60,
  "5m": 300,
  "10m": 600,
  "15m": 900,
  "30m": 1800,
  "1h": 3600,
  "4h": 14400,
  "12h": 43200,
  "24h": 86400,
};

function getNextDailyBarTime(barTime) {
  const date = new Date(barTime * 1000);
  date.setDate(date.getDate() + 1);
  return date.getTime() / 1000;
}

// Chart Methods
const Datafeed = (pool) => {
  return {
    onReady: (callback) => {
      setTimeout(() => callback(configurationData));
    },
    searchSymbols: async () => {
      // Code here...
    },
    resolveSymbol: async (
      symbolName,
      onSymbolResolvedCallback,
      onResolveErrorCallback
    ) => {
      let symbolInfo = {
        name: symbolName,
        has_intraday: true,
        has_no_volume: false,
        session: "24x7",
        timezone: "Europe/Athens",
        exchange: "",
        minmov: 0.00000000001,
        pricescale: 100000000,
        has_weekly_and_monthly: true,
        volume_precision: 2,
        data_status: "streaming",
        supported_resolutions: configurationData.supported_resolutions,
      };

      onSymbolResolvedCallback(symbolInfo);
    },

    getBars: async (
      symbolInfo,
      resolution,
      periodParams,
      onHistoryCallback,
      onErrorCallback
      // firstDataRequest
    ) => {
      const { from, to, firstDataRequest } = periodParams;

      try {
        socket.emit('data', {
          type: "PRICE_DATA_HISTORICAL",
          data: {
            address: pool, address_type: 'pair', type: resValues[resolution], time_from: from, time_to: to
          }
        }, (data) => {
          console.log(data.type)

          if (data.data != undefined && data.data.length > 0) {
            let bars = data.data.map((el) => {
              let dd = new Date(el.unixTime * 1000);
              return {
                time: dd.getTime(), //TradingView requires bar time in ms
                open: el.o,
                high: el.h,
                low: el.l,
                close: el.c,
                volume: el.v,
              };
            });
            bars = bars.sort(function (a, b) {
              if (a.time < b.time) return -1;
              else if (a.time > b.time) return 1;
              return 0;
            });

            if (prevBar == undefined)
              prevBar = bars[bars.length - 1];

            for (var i = 0; i < bars.length - 1; i++)
              bars[i].close = bars[i + 1].open;
            if (firstBar != undefined)
              bars[bars.length - 1].close = firstBar.open;
            firstBar = bars[0];

            // window.delta = 0;

            onHistoryCallback(bars, { noData: false });
          } else {
            onHistoryCallback([], { noData: true });
          }
        })

      } catch (error) {
        onErrorCallback(error);
      }
    },
    subscribeBars: (
      symbolInfo,
      resolution,
      onRealtimeCallback,
      subscribeUID,
      onResetCacheNeededCallback,
      lastDailyBar
    ) => {
      socket.emit('subscribe', {
        type: "SUBSCRIBE_PRICE",
        data: {
          address: pool, address_type: 'pair', type: resValues[resolution]
        }
      })
      socket.on('PRICE_DATA', (data) => {
        console.log(data.type)
        if (data.type == 'PRICE_DATA') {
          if (data != undefined && data.data != undefined) {
            let el = data.data;
            let dd = new Date(el.unixTime * 1000);
            let bar = {
              time: dd.getTime(), //TradingView requires bar time in ms
              open: el.o,
              high: el.h,
              low: el.l,
              close: el.c,
              volume: el.v,
            };
            if (curBar != undefined && bar.time != curBar.time) {
              prevBar = curBar;
            }
            curBar = bar;
            if (prevBar != undefined) {
              bar.open = prevBar.close;
            }
            onRealtimeCallback(bar)
          } else {
            console.log(data)
          }
        }
      })
    },
    unsubscribeBars: (subscriberUID) => {
      // Code here...
    },
  };
};

// export default Datafeed;
