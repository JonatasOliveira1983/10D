const API_BASE = '/api';

export async function fetchSignals(minScore = 0) {
    try {
        const response = await fetch(`${API_BASE}/signals?min_score=${minScore}`);
        if (!response.ok) throw new Error('Failed to fetch signals');
        return await response.json();
    } catch (error) {
        console.error('Error fetching signals:', error);
        return { signals: [], count: 0 };
    }
}

export async function fetchPairs() {
    try {
        const response = await fetch(`${API_BASE}/pairs`);
        if (!response.ok) throw new Error('Failed to fetch pairs');
        return await response.json();
    } catch (error) {
        console.error('Error fetching pairs:', error);
        return { pairs: [], count: 0 };
    }
}

export async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        return await response.json();
    } catch (error) {
        console.error('Error fetching stats:', error);
        return {
            monitored_pairs: 0,
            active_signals: 0,
            long_signals: 0,
            short_signals: 0,
            average_score: 0
        };
    }
}

export async function fetchHistory(limit = 50) {
    try {
        const response = await fetch(`${API_BASE}/history?limit=${limit}`);
        if (!response.ok) throw new Error('Failed to fetch history');
        return await response.json();
    } catch (error) {
        console.error('Error fetching history:', error);
        return { history: [], count: 0 };
    }
}

export async function triggerScan() {
    try {
        const response = await fetch(`${API_BASE}/scan`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to trigger scan');
        return await response.json();
    } catch (error) {
        console.error('Error triggering scan:', error);
        return { message: 'Error', new_signals: 0 };
    }
}

export async function startScanner() {
    try {
        const response = await fetch(`${API_BASE}/scanner/start`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to start scanner');
        return await response.json();
    } catch (error) {
        console.error('Error starting scanner:', error);
        return { status: 'error' };
    }
}

export async function stopScanner() {
    try {
        const response = await fetch(`${API_BASE}/scanner/stop`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to stop scanner');
        return await response.json();
    } catch (error) {
        console.error('Error stopping scanner:', error);
        return { status: 'error' };
    }
}

export async function fetchBTCRegime() {
    try {
        const response = await fetch(`${API_BASE}/btc/regime`);
        if (!response.ok) throw new Error('Failed to fetch BTC regime');
        return await response.json();
    } catch (error) {
        console.error('Error fetching BTC regime:', error);
        return {
            regime: 'TRENDING',
            tp_pct: 2.0,
            sl_pct: 1.0,
            status: 'ERROR'
        };
    }
}

export async function fetchSentiment() {
    try {
        const response = await fetch(`${API_BASE}/sentiment`);
        if (!response.ok) throw new Error('Failed to fetch sentiment');
        return await response.json();
    } catch (error) {
        console.error('Error fetching sentiment:', error);
        return {
            status: "error",
            headlines: [],
            analysis: { score: 50, sentiment: "NEUTRAL", summary: "Failed to load" }
        };
    }
}
