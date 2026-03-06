const socket = io();

socket.on("connect", () => {
    console.log("Connected to server");
});

const chartContainer = document.getElementById("chart");

const chart = LightweightCharts.createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: 500,
    layout: {
        background: { color: "#0b1c2d" },
        textColor: "#ffffff",
    },
});

const candleSeries = chart.addCandlestickSeries();

let currentSegment = null;
let lastTrend = null;

socket.on("candle", (candle) => {

    const time = Number(candle.time);

    candleSeries.update({
        time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close
    });

    if (candle.supertrend === null) return;

    const value = candle.supertrend;
    const trend = candle.trend;

    if (lastTrend === null || trend !== lastTrend) {

        currentSegment = chart.addLineSeries({
            color: trend ? "#00ff00" : "#ff3333",
            lineWidth: 2
        });

    }

    currentSegment.update({
        time,
        value
    });

    lastTrend = trend;

});