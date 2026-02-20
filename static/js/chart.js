const chartContainer = document.getElementById("chart");

const chart = LightweightCharts.createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: 500,
    layout: {
        backgroundColor: '#0b1c2d',
        textColor: '#ffffff'
    },
    grid: {
        vertLines: { color: '#1e2a38' },
        horzLines: { color: '#1e2a38' }
    }
});

// ✅ correct for v5
const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries);

// 🔥 REQUIRED
let signalLines = [];

// ---------------- DRAW SIGNAL ----------------
function drawSignal(price, type) {
    const colorMap = {
        BUY: "#00ff00",
        SELL: "#ff3333",
        SL: "#ffa500"
    };

    const line = candleSeries.createPriceLine({
        price,
        color: colorMap[type],
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: type
    });

    signalLines.push(line);
}

// ---------------- RESIZE ----------------
window.addEventListener("resize", () => {
    chart.applyOptions({ width: chartContainer.clientWidth });
});
