import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries } from 'lightweight-charts';

const SignalChart = ({ symbol, entryPrice, stopLoss, takeProfit, direction, openedAt, currentPrice, telemetry }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef();
    const seriesRef = useRef();
    const priceLinesRef = useRef([]);
    const [interval, setIntervalState] = useState('30');

    useEffect(() => {
        if (!chartContainerRef.current) return;

        let chart;
        const handleResize = () => {
            if (chartRef.current && chartContainerRef.current) {
                try {
                    chartRef.current.applyOptions({
                        width: chartContainerRef.current.clientWidth
                    });
                } catch (e) {
                    console.error("Resize error:", e);
                }
            }
        };

        try {
            chart = createChart(chartContainerRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: 'transparent' },
                    textColor: '#d1d4dc',
                    fontSize: 10,
                },
                grid: {
                    vertLines: { color: 'rgba(42, 46, 57, 0.2)' },
                    horzLines: { color: 'rgba(42, 46, 57, 0.2)' },
                },
                width: chartContainerRef.current.clientWidth || 300,
                height: 300,
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    rightOffset: 5, // Space for latest candle
                },
                rightPriceScale: {
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    visible: true,
                    scaleMargins: {
                        top: 0.2, // Leave space for HUD
                        bottom: 0.2,
                    },
                },
                crosshair: {
                    vertLine: {
                        labelVisible: false,
                    },
                }
            });

            chartRef.current = chart;

            const candlestickSeries = chart.addSeries(CandlestickSeries, {
                upColor: '#10b981',
                downColor: '#ef4444',
                borderVisible: false,
                wickUpColor: '#10b981',
                wickDownColor: '#ef4444',
                priceLineVisible: false, // Hide the default price line to use our tactical one
            });
            seriesRef.current = candlestickSeries;

            // Function to manage tactical lines
            const updateTacticalLines = () => {
                // Clear existing lines
                priceLinesRef.current.forEach(line => candlestickSeries.removePriceLine(line));
                priceLinesRef.current = [];

                // Fallback Calculation if props are missing (1% SL, 2% TP default)
                let finalSL = stopLoss;
                let finalTP = takeProfit;

                if ((!finalSL || Number(finalSL) === 0) && entryPrice) {
                    finalSL = direction === 'LONG' ? entryPrice * 0.99 : entryPrice * 1.01;
                }
                if ((!finalTP || Number(finalTP) === 0) && entryPrice) {
                    finalTP = direction === 'LONG' ? entryPrice * 1.02 : entryPrice * 0.98;
                }

                const addLine = (price, color, title, style = 2) => {
                    const numericPrice = Number(price);
                    if (!isNaN(numericPrice) && numericPrice > 0) {
                        try {
                            const line = candlestickSeries.createPriceLine({
                                price: numericPrice,
                                color: color,
                                lineWidth: 2,
                                lineStyle: style,
                                axisLabelVisible: true,
                                title: title,
                            });
                            priceLinesRef.current.push(line);
                        } catch (e) {
                            console.warn(`Could not add line ${title}:`, e);
                        }
                    }
                };

                // Entry (Dashed White/Blue)
                addLine(entryPrice, '#6366f1', 'ENTRY', 2);

                // Stop Loss (Solid Red)
                addLine(finalSL, '#f43f5e', 'STOP LOSS', 0);

                // Take Profit (Solid Emerald)
                addLine(finalTP, '#10b981', 'TAKE PROFIT', 0);

                // Current Price (Dynamic Tactical Line)
                if (currentPrice) {
                    addLine(currentPrice, '#ffffff', 'LIVE', 3);
                }
            };

            updateTacticalLines();

            // Fetch Candles
            const fetchCandles = async () => {
                try {
                    const response = await fetch(`/api/chart/klines/${symbol}?interval=${interval}&limit=150`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data && data.candles && Array.isArray(data.candles)) {
                            const formattedData = data.candles
                                .map(c => ({
                                    time: Number(c.timestamp) / 1000,
                                    open: Number(c.open),
                                    high: Number(c.high),
                                    low: Number(c.low),
                                    close: Number(c.close),
                                }))
                                .sort((a, b) => a.time - b.time);

                            if (formattedData.length > 0) {
                                candlestickSeries.setData(formattedData);

                                // Set Markers for Entry
                                if (openedAt) {
                                    const entryTime = new Date(openedAt).getTime() / 1000;
                                    // Window depends on interval (in minutes converted to seconds)
                                    const intervalSec = (interval === 'D' ? 1440 : parseInt(interval)) * 60;
                                    const entryCandle = formattedData.find(c => Math.abs(c.time - entryTime) < intervalSec);

                                    if (entryCandle) {
                                        if (typeof candlestickSeries.setMarkers === 'function') {
                                            candlestickSeries.setMarkers([
                                                {
                                                    time: entryCandle.time,
                                                    position: direction === 'LONG' ? 'belowBar' : 'aboveBar',
                                                    color: direction === 'LONG' ? '#10b981' : '#f43f5e',
                                                    shape: direction === 'LONG' ? 'arrowUp' : 'arrowDown',
                                                    text: 'ENTRY',
                                                }
                                            ]);
                                        } else {
                                            console.warn("setMarkers not available on series object");
                                        }
                                    }
                                }

                                if (candlestickSeries.data().length > 0) {
                                    // Always fit content on initial load or interval change
                                    chart.timeScale().fitContent();
                                }
                            }
                        }
                    }
                } catch (err) {
                    console.error("Error loading candles:", err);
                }
            };

            fetchCandles();
            const pollInterval = setInterval(fetchCandles, 20000);

            window.addEventListener('resize', handleResize);

            return () => {
                clearInterval(pollInterval);
                window.removeEventListener('resize', handleResize);
                if (chart) chart.remove();
                chartRef.current = null;
            };

        } catch (error) {
            console.error("FATAL: Could not initialize chart:", error);
        }
    }, [symbol, entryPrice, stopLoss, takeProfit, openedAt, direction, currentPrice, interval]);

    return (
        <div className="signal-chart-wrapper animate-fade w-full h-full relative group">
            {/* TIMEFRAME SELECTOR - Responsive Grid for Mobile */}
            <div className="absolute top-2 right-2 sm:top-4 sm:right-4 z-30 flex flex-wrap sm:flex-nowrap items-center justify-end gap-1 bg-black/60 sm:bg-black/40 backdrop-blur-md p-1 rounded-lg border border-white/10 opacity-90 sm:opacity-70 group-hover:opacity-100 transition-opacity max-w-[160px] sm:max-w-none">
                {['1', '5', '15', '30', '60', '120', '240', 'D'].map(tf => (
                    <button
                        key={tf}
                        onClick={() => setIntervalState(tf)}
                        className={`
                            px-1.5 py-1 text-[8px] sm:text-[9px] font-bold rounded transition-all
                            ${interval === tf
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'}
                        `}
                    >
                        {tf === '240' ? '4H' : tf === '120' ? '2H' : tf === '60' ? '1H' : tf === 'D' ? '1D' : `${tf}M`}
                    </button>
                ))}
            </div>

            {/* AGENT HUD OVERLAY - Compact on Mobile */}
            <div className="absolute top-2 left-2 sm:top-4 sm:left-4 z-20 pointer-events-none">
                <div className="bg-black/80 sm:bg-black/60 backdrop-blur-md border border-white/10 p-2 sm:p-3 rounded-lg max-w-[200px] sm:max-w-[320px] shadow-2xl transition-all duration-500 group-hover:bg-black/90">
                    <div className="flex items-center gap-1 sm:gap-2 mb-1 sm:mb-2">
                        <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                        <span className="text-[10px] sm:text-xs font-bold text-emerald-400 uppercase tracking-widest whitespace-nowrap">Elite Agent Live</span>
                    </div>
                    <p className="text-xs sm:text-sm md:text-base text-blue-100/90 leading-tight sm:leading-relaxed italic font-medium">
                        "{telemetry || 'Analisando vetores de preço...'}"
                    </p>
                </div>
            </div>

            {/* SYMBOL BADGE - Smaller on Mobile */}
            <div className="absolute bottom-4 right-4 z-20 pointer-events-none opacity-20 sm:opacity-40 group-hover:opacity-100 transition-opacity">
                <span className="text-2xl sm:text-4xl font-black text-white/10 tracking-tighter">{symbol}</span>
            </div>

            <div ref={chartContainerRef} className="absolute inset-0 w-full h-full" />
        </div>
    );
};

export default SignalChart;
