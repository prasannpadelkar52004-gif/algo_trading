// ==============================
// CONNECT TO SOCKET
// ==============================
const socket = io();

socket.on("connect", () => {
    console.log("✅ Connected to Flask SocketIO");
});


// ==============================
// CREATE CHART
// ==============================
const chartContainer = document.getElementById("chart");

const chart = LightweightCharts.createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: 500,
    layout: {
        background: { color: "#0b1c2d" },
        textColor: "#ffffff",
    },
    grid: {
        vertLines: { color: "#1e2a38" },
        horzLines: { color: "#1e2a38" },
    },
});


// ==============================
// SERIES
// ==============================
const candleSeries = chart.addCandlestickSeries();

const supertrendLine = chart.addLineSeries({
    color: "#ff3333",
    lineWidth: 3,
});


// ==============================
// DATA
// ==============================
let supertrendSegments = [];   // store all line series
let currentSegment = null;     // active line series
let lastTrend = null;


// ==============================
// RECEIVE LIVE DATA
// ==============================
socket.on("candle", (candle) => {

    const time = Number(candle.time);

    // Update candle
    candleSeries.update({
        time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
    });

    // If no supertrend -> skip
    if (candle.supertrend === null || candle.supertrend === undefined) return;

    const value = candle.supertrend;
    const currentTrend = candle.trend; // true = uptrend

    // ================================
    // CREATE NEW SEGMENT ON FLIP
    // ================================
    if (lastTrend === null || lastTrend !== currentTrend) {

        currentSegment = chart.addLineSeries({
            color: currentTrend ? "#00ff00" : "#ff3333",
            lineWidth: 2,
        });

        supertrendSegments.push(currentSegment);
    }

    // ================================
    // ADD DATA TO CURRENT SEGMENT
    // ================================
    currentSegment.update({
        time,
        value
    });

    lastTrend = currentTrend;
});



// ==============================
// AUTO RESIZE
// ==============================
window.addEventListener("resize", () => {
    chart.applyOptions({
        width: chartContainer.clientWidth,
    });
});
