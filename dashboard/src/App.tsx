import React, { useEffect, useState } from 'react';
import { ShieldCheck, TrendingUp, Globe, AlertCircle, Mic, Send, BarChart2 } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);


interface FactCheck {
  id: number;
  claim: string;
  verdict: string;
  confidence: number;
  virality_score: number;
  language: string;
  timestamp: string;
  counter_message?: string;
  flagged_by_ngo?: number;
}

const App: React.FC = () => {
  const [checks, setChecks] = useState<FactCheck[]>([]);
  const [stats, setStats] = useState({ 
    total: 0, 
    true: 0, 
    false: 0, 
    misleading: 0,
    trending_language: 'Tamil',
    score_distribution: [0,0,0,0,0,0,0,0,0,0]
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Simulation UI states
  const [simText, setSimText] = useState("");
  const [isSimulating, setIsSimulating] = useState(false);
  
  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!simText.trim()) return;
    
    setIsSimulating(true);
    try {
      await fetch('/api/process_audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: simText })
      });
      setSimText("");
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [checksRes, statsRes] = await Promise.all([
          fetch('/api/claims'),
          fetch('/api/analytics')
        ]);
        
        if (!checksRes.ok || !statsRes.ok) {
          throw new Error('Failed to fetch data');
        }

        const checksData = await checksRes.json();
        const statsData = await statsRes.json();
        
        setChecks(checksData);
        setStats(statsData);
        setError(null);
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setError("Unable to connect to the Fact-Checker server. Retrying...");
      } finally {
        setLoading(false);
      }
    };
    
    // Initial fetch
    fetchData();
    
    // Set up polling every 3 seconds
    const intervalId = setInterval(fetchData, 3000);
    
    // Cleanup on unmount
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-4xl font-bold text-premium-accent mb-2 flex items-center gap-3">
            <ShieldCheck size={40} />
            Vernacular Fact-Checker
          </h1>
          <p className="text-slate-400">WhatsApp-Native Misinformation Detection Dashboard</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-slate-800/50 px-4 py-2 rounded-lg border border-slate-700">
            <span className="text-xs text-slate-500 block uppercase font-semibold">Total Checked</span>
            <span className="text-xl font-bold">{stats.total}</span>
          </div>
        </div>
      </header>

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg mb-8 flex items-center gap-2">
          <AlertCircle size={20} />
          <p>{error}</p>
        </div>
      )}

      <section className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        <StatCard icon={<TrendingUp className="text-red-400" />} label="False Claims" value={stats.false} color="red" />
        <StatCard icon={<ShieldCheck className="text-green-400" />} label="True Claims" value={stats.true} color="green" />
        <StatCard icon={<Globe className="text-blue-400" />} label="Top Language" value={stats.trending_language} color="blue" />
        <StatCard icon={<AlertCircle className="text-yellow-400" />} label="High Risk" value={checks.filter(c => c.virality_score > 7).length} color="yellow" />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
        {/* Voice Upload Simulation */}
        <section className="premium-card lg:col-span-1 border border-premium-accent/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Mic className="text-premium-accent" />
            Voice Audit Simulator
          </h2>
          <p className="text-sm text-slate-400 mb-6 border-b border-slate-700/50 pb-4">
            User uploads or records a voice message. Backend processes the audio, transcribes it, and triggers the Fact Check Engine.
          </p>
          <form onSubmit={handleSimulate} className="flex flex-col gap-4">
            <label className="text-sm font-semibold text-slate-300">Simulate Audio Transcription (Fake Whisper output):</label>
            <textarea 
              value={simText}
              onChange={(e) => setSimText(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-premium-accent h-28 resize-none"
              placeholder='e.g., "Drinking hot water cures COVID-19 immediately"'
              disabled={isSimulating}
            ></textarea>
            <button 
              type="submit" 
              disabled={isSimulating || !simText.trim()}
              className="w-full bg-premium-accent hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-lg flex justify-center items-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSimulating ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  <Send size={18} />
                  Simulate Upload
                </>
              )}
            </button>
          </form>
        </section>

        {/* Analytics Dashboard - Chart.js */}
        <section className="premium-card lg:col-span-2 border border-slate-800">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <BarChart2 className="text-violet-400" />
            Virality Score Distribution
          </h2>
          <div className="h-64 w-full relative">
            <Bar 
              data={{
                labels: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                datasets: [
                  {
                    label: 'Number of Claims',
                    data: stats.score_distribution,
                    backgroundColor: 'rgba(139, 92, 246, 0.5)',
                    borderColor: 'rgb(139, 92, 246)',
                    borderWidth: 1,
                    borderRadius: 4,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                  x: { grid: { display: false } }
                },
                plugins: {
                  legend: { display: false }
                }
              }}
            />
          </div>
        </section>
      </div>

      <main>
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 border-t border-slate-800 pt-8">
          <TrendingUp size={24} className="text-premium-accent" />
          Recent Investigations
        </h2>
        
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-premium-accent"></div>
          </div>
        ) : checks.length === 0 ? (
          <div className="text-center py-20 text-slate-500 bg-slate-800/20 rounded-xl border border-slate-800">
            <ShieldCheck size={48} className="mx-auto mb-4 opacity-50" />
            <p className="text-xl font-semibold">No claims analyzed yet.</p>
            <p className="text-sm mt-2">Send a message to the WhatsApp bot to get started.</p>
          </div>
        ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {checks.map(check => (
            <FactCheckCard key={check.id} check={check} />
          ))}
        </div>
        )}
      </main>
    </div>
  );
};

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}

const StatCard = ({ icon, label, value, color }: StatCardProps) => (
  <div className="premium-card flex items-center gap-4">
    <div className={`p-3 rounded-full bg-${color}-400/10`}>
      {icon}
    </div>
    <div>
      <span className="text-xs text-slate-500 block uppercase font-bold tracking-wider">{label}</span>
      <span className="text-2xl font-bold">{value}</span>
    </div>
  </div>
);

const FactCheckCard = ({ check }: { check: FactCheck }) => {
  const [isFlagged, setIsFlagged] = useState(check.flagged_by_ngo === 1);
  const [isFlagging, setIsFlagging] = useState(false);

  const toggleFlag = async () => {
    setIsFlagging(true);
    try {
      const res = await fetch(`/api/claims/${check.id}/flag`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) setIsFlagged(data.flagged === 1);
    } catch (err) {
      console.error(err);
    } finally {
      setIsFlagging(false);
    }
  };

  return (
    <div className={`premium-card transition-colors duration-300 ${isFlagged ? 'border-red-500/50 bg-red-500/5' : 'border border-slate-800 hover:border-premium-accent'}`}>
      <div className="flex justify-between items-start mb-4">
        <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
          check.verdict === 'False' ? 'bg-red-500/20 text-red-500' : 
          check.verdict === 'True' ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'
        }`}>
          {check.verdict}
        </span>
        <div className="flex gap-2 items-center">
          <button 
            onClick={toggleFlag}
            disabled={isFlagging}
            className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${isFlagged ? 'bg-red-500/20 text-red-400' : 'bg-slate-800 text-slate-400 hover:text-white cursor-pointer'}`}
          >
            <AlertCircle size={12} />
            {isFlagged ? 'Disputed' : 'Flag as Disputed'}
          </button>
          <span className="text-xs text-slate-500">{new Date(check.timestamp).toLocaleDateString()}</span>
        </div>
      </div>
      <p className="text-lg font-semibold mb-4 line-clamp-2">{check.claim}</p>

      {check.counter_message && (
        <div className="bg-slate-900/50 border border-slate-700/50 rounded p-3 mb-4">
          <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">
            Auto-Drafted Counter-Message
          </p>
          <p className="text-sm text-slate-300 italic whitespace-pre-wrap">"{check.counter_message}"</p>
        </div>
      )}

      <div className="flex justify-between items-center text-sm text-slate-400 border-t border-slate-700 pt-4 mt-auto">
        <div className="flex items-center gap-1">
          <Globe size={14} />
          {check.language}
        </div>
        <div className="bg-slate-800 px-2 py-1 rounded">
          Confidence: {check.confidence}%
        </div>
      </div>
    </div>
  );
};

export default App;
