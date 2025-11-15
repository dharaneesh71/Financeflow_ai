import React, { useState, useRef, useEffect } from 'react';
import { 
  Upload, FileText, Database, CheckCircle, AlertCircle, 
  Loader, TrendingUp, Sun, Moon, Terminal, 
  Activity, X, Sparkles, Edit, Trash2, Plus, 
  ArrowRight, ArrowLeft, LogOut, User, Home, Settings,
  Clock, Zap, Shield, Menu, Bell, Eye, 
  EyeOff, Lock, Mail, BarChart3,
  MessageSquare, Send,
  RefreshCw
} from 'lucide-react';
// --- NEW: Import charting components ---
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  CartesianGrid, XAxis, YAxis, Tooltip, Legend
} from 'recharts';

// --- SNOWFALL COMPONENT (v2) ---
const Snowfall = () => {
  // ... (Your existing Snowfall component code... no changes)
  const snowflakeCount = 50; 
  return (
    <div className="snowfall-container" aria-hidden="true">
      {Array.from({ length: snowflakeCount }).map((_, i) => (
        <div 
          key={i} 
          className="snowflake" 
          style={{
            '--size': `${Math.random() * 0.5 + 0.4}rem`,
            '--left-start': `${Math.random() * 100}vw`,
            '--left-end': `${Math.random() * 100}vw`,
            '--animation-delay': `${Math.random() * -10}s`,
            '--animation-duration': `${Math.random() * 10 + 10}s`,
            '--flutter-duration': `${Math.random() * 2 + 3}s`,
          }}
        >
          <span className="flutter">❄</span>
        </div>
      ))}
    </div>
  );
};

// --- A simple fade-in animation component ---
const FadeIn = ({ children, key }) => {
  return (
    <div key={key} className="animate-fade-in">
      {children}
    </div>
  );
};

const API_BASE = 'http://localhost:8000/api';

// --- HOOK FOR SESSION-ONLY PERSISTENCE ---
function useSessionState(key, defaultValue) {
  // ... (Your existing useSessionState hook... no changes)
  const [state, setState] = useState(() => {
    const persistedValue = sessionStorage.getItem(key);
    if (persistedValue !== null) {
      try {
        return JSON.parse(persistedValue);
      } catch (e) {
        console.error("Failed to parse sessionStorage key", key, e);
        return defaultValue;
      }
    }
    return defaultValue;
  });

  useEffect(() => {
    sessionStorage.setItem(key, JSON.stringify(state));
  }, [key, state]);

  return [state, setState];
}

// --- HOOK FOR PERMANENT PERSISTENCE ---
function useLocalStorageState(key, defaultValue) {
  // ... (Your existing useLocalStorageState hook... no changes)
  const [state, setState] = useState(() => {
    const persistedValue = localStorage.getItem(key);
    if (persistedValue !== null) {
      try {
        return JSON.parse(persistedValue);
      } catch (e) {
        console.error("Failed to parse localStorage key", key, e);
        return defaultValue;
      }
    }
    return defaultValue;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(state));
  }, [key, state]);

  return [state, setState];
}

// --- FIXED: TABLE MODAL COMPONENT ---
const TableModal = ({ results, onClose, darkMode, textClass, textMutedClass, cardClass, headerClass, cellClass }) => {
  // ... (Your existing TableModal component code... no changes)
  if (!results?.schema?.tables?.[0]) {
    console.error("View Table: Missing schema");
    return null;
  }
 
  const table = results.schema.tables[0];
  const headers = table.columns;
 
  let dataRows = [];
  if (results.extracted_metrics_by_document && Object.keys(results.extracted_metrics_by_document).length > 0) {
    dataRows = Object.entries(results.extracted_metrics_by_document);
  } 
  else if (results.extracted_metrics && Object.keys(results.extracted_metrics).length > 0) {
    dataRows = [["(Single Document)", results.extracted_metrics]];
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 animate-fade-in">
      <div 
        className={`relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl ${cardClass}`}
      >
        <div className={`flex items-center justify-between p-4 border-b ${darkMode ? 'border-slate-700' : 'border-gray-200'}`}>
          <div className="flex items-center gap-3">
            <Database className="text-cyan-400" />
            <h3 className={`text-xl font-bold ${textClass}`}>
              Preview: {table.table_name}
            </h3>
          </div>
          <button 
            onClick={onClose} 
            className={`p-2 rounded-lg ${darkMode ? 'hover:bg-slate-700' : 'hover:bg-gray-200'}`}
          >
            <X className="w-6 h-6" />
          </button>
        </div>
       
        <div className="overflow-auto p-4">
          {dataRows.length === 0 ? (
            <div className={`text-center p-8 ${textMutedClass}`}>
              <AlertCircle className="w-12 h-12 mx-auto mb-4" />
              <h4 className="text-lg font-semibold">No Data Returned</h4>
              <p>The backend processed the files but did not return any extracted metrics.</p>
            </div>
          ) : (
            <div className="overflow-x-auto relative rounded-lg border border-gray-500/30">
              <table className={`w-full text-left text-sm ${textClass}`}>
                <thead className={`text-xs uppercase ${headerClass}`}>
                  <tr>
                    {headers.map((header) => (
                      <th key={header.name} scope="col" className="px-6 py-3">
                        {header.name.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataRows.map(([docName, metrics], idx) => (
                    <tr 
                      key={idx} 
                      className={`border-b ${cellClass} ${darkMode ? 'bg-slate-800/50' : 'bg-white/50'}`}
                    >
                      {headers.map((header) => {
                        let cellValue = 'N/A';
                        const lowerCaseHeader = header.name.toLowerCase();
                       
                        if (lowerCaseHeader === 'document_name') {
                          cellValue = docName;
                        } else if (metrics[lowerCaseHeader] !== undefined && metrics[lowerCaseHeader] !== null) {
                          cellValue = String(metrics[lowerCaseHeader]);
                        } else if (lowerCaseHeader === 'metric_id' || lowerCaseHeader === 'extraction_date') {
                          cellValue = '(auto)'; 
                        }
                       
                        return (
                          <td key={header.name} className="px-6 py-4">
                            {cellValue === 'N/A' ? <span className={textMutedClass}>N/A</span> : cellValue}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className={`p-4 border-t ${darkMode ? 'border-slate-700' : 'border-gray-200'} text-right`}>
          <button
            onClick={onClose}
            className={`px-5 py-2 rounded-lg text-white bg-gradient-to-r from-blue-500 to-cyan-400 hover:from-blue-600 hover:to-cyan-500`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// --- THIS COMPONENT IS MODIFIED ---
// Replace your RenderAnalysisChart component with this fixed version
// Replace your RenderAnalysisChart component with this clean version

const RenderAnalysisChart = ({ chart, darkMode, textMutedClass, accentText }) => {
  console.log('📊 Chart data received:', chart);
  
  if (!chart || !chart.data || chart.data.length === 0) {
    return (
      <div className={`p-4 text-center ${textMutedClass}`}>
        No data returned for this chart.
      </div>
    );
  }

  const { chart_type, title, x_axis, y_axis, series, data } = chart;
  
  console.log('Chart type:', chart_type);
  console.log('X-axis:', x_axis);
  console.log('Y-axis:', y_axis);
  console.log('Series:', series);
  console.log('Raw data:', data);
  
  const strokeColor = darkMode ? '#94a3b8' : '#64748b';
  const COLORS = ['#0ea5e9', '#06b6d4', '#14b8a6', '#f59e0b', '#ef4444'];
  
  // Clean up company names
  const cleanCompanyName = (name) => {
    if (!name) return name;
    let cleaned = name.replace(/^.*[\\\/]/, '');
    cleaned = cleaned.replace(/\.(pdf|png|jpg|jpeg)$/i, '');
    return cleaned;
  };

  // Format X-axis labels
  const formatXAxisTick = (tick) => {
    if (typeof tick !== 'string') return tick;
    if (tick.includes("COURSERA")) return "Coursera";
    if (tick.includes("Alphabet")) return "Alphabet";
    if (tick.includes("Apple")) return "Apple";
    if (tick.includes("Microsoft")) return "Microsoft";
    if (tick.length > 15) {
      return `${tick.substring(0, 12)}...`;
    }
    return tick;
  };
  
  // Clean data
  const cleanedData = data.map(row => {
    const newRow = { ...row };
    if (newRow[x_axis]) {
      newRow[x_axis] = cleanCompanyName(newRow[x_axis]);
    }
    if (newRow.COMPANY_NAME) {
      newRow.COMPANY_NAME = cleanCompanyName(newRow.COMPANY_NAME);
    }
    if (newRow.DOCUMENT_NAME) {
      newRow.DOCUMENT_NAME = cleanCompanyName(newRow.DOCUMENT_NAME);
    }
    return newRow;
  });

  console.log('Cleaned data:', cleanedData);

  if (cleanedData.length === 0) {
    return (
      <div className={`p-4 text-center ${textMutedClass}`}>
        No data to display after cleaning.
      </div>
    );
  }

  // TABLE VIEW - render separately
  if (chart_type === 'table') {
    return (
      <div className="w-full">
        <h4 className={`text-lg font-semibold mb-4 text-center ${accentText}`}>{title}</h4>
        <div className="overflow-auto max-h-96 relative rounded-lg border border-gray-500/30">
          <table className="w-full text-left text-sm">
            <thead className={`text-xs uppercase sticky top-0 ${darkMode ? 'bg-slate-800' : 'bg-gray-100'}`}>
              <tr>
                {cleanedData.length > 0 && Object.keys(cleanedData[0]).map((key) => (
                  <th key={key} scope="col" className="px-6 py-3 whitespace-nowrap">
                    {key.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cleanedData.map((row, idx) => (
                <tr key={idx} className={`border-b ${darkMode ? 'border-slate-700' : 'border-gray-200'} ${darkMode ? 'bg-slate-800/50' : 'bg-white/50'}`}>
                  {Object.values(row).map((val, i) => (
                    <td key={i} className="px-6 py-4 whitespace-nowTwrap">
                      {typeof val === 'number' ? val.toLocaleString() : String(val)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // CHART VIEWS (Bar, Line, Pie) - all in ResponsiveContainer
  return (
    <div className="w-full">
      <h4 className={`text-lg font-semibold mb-4 text-center ${accentText}`}>{title}</h4>
      <ResponsiveContainer width="100%" height={400}>
        {chart_type === 'bar' && (
          <BarChart data={cleanedData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={strokeColor} opacity={0.3} />
            <XAxis 
              dataKey={x_axis || 'COMPANY_NAME'} 
              stroke={strokeColor} 
              interval={0} 
              angle={-45} 
              textAnchor="end" 
              height={80}
              tickFormatter={formatXAxisTick}
            />
            <YAxis stroke={strokeColor} />
            <Tooltip
              contentStyle={{
                backgroundColor: darkMode ? '#0f172a' : '#ffffff',
                borderColor: darkMode ? '#334155' : '#e2e8f0',
                borderRadius: '0.5rem',
              }}
              formatter={(value) => typeof value === 'number' ? value.toLocaleString() : value}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="rect"
              iconSize={14}
              formatter={(value) => <span style={{ color: darkMode ? '#e2e8f0' : '#1e293b', marginLeft: '5px' }}>{value}</span>}
            />
            {series && series.length > 0 ? (
              series.map((s, idx) => (
                <Bar key={s} dataKey={s} fill={COLORS[idx % COLORS.length]} />
              ))
            ) : (
              <Bar dataKey={y_axis || Object.keys(cleanedData[0]).find(k => k !== x_axis)} fill={COLORS[0]} />
            )}
          </BarChart>
        )}

        {chart_type === 'line' && (
          <LineChart data={cleanedData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={strokeColor} opacity={0.3} />
            <XAxis 
              dataKey={x_axis || 'COMPANY_NAME'} 
              stroke={strokeColor} 
              interval={0} 
              angle={-45} 
              textAnchor="end" 
              height={80}
              tickFormatter={formatXAxisTick}
            />
            <YAxis stroke={strokeColor} />
            <Tooltip
              contentStyle={{
                backgroundColor: darkMode ? '#0f172a' : '#ffffff',
                borderColor: darkMode ? '#334155' : '#e2e8f0',
                borderRadius: '0.5rem',
              }}
              formatter={(value) => typeof value === 'number' ? value.toLocaleString() : value}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="rect"
              iconSize={14}
              formatter={(value) => <span style={{ color: darkMode ? '#e2e8f0' : '#1e293b', marginLeft: '5px' }}>{value}</span>}
            />
            {series && series.length > 0 ? (
              series.map((s, idx) => (
                <Line key={s} type="monotone" dataKey={s} stroke={COLORS[idx % COLORS.length]} strokeWidth={2} />
              ))
            ) : (
              <Line type="monotone" dataKey={y_axis || Object.keys(cleanedData[0]).find(k => k !== x_axis)} stroke={COLORS[0]} strokeWidth={2} />
            )}
          </LineChart>
        )}

        {chart_type === 'pie' && (
          <PieChart>
            <Pie
              data={cleanedData} 
              dataKey={y_axis || Object.keys(cleanedData[0]).find(k => k !== x_axis && typeof cleanedData[0][k] === 'number')}
              nameKey={x_axis || 'COMPANY_NAME'}
              cx="50%"
              cy="50%"
              outerRadius={120}
              fill="#8884d8"
              label={(entry) => `${entry[x_axis || 'COMPANY_NAME']}: ${entry[y_axis]}`}
            >
              {cleanedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: darkMode ? '#0f172a' : '#ffffff',
                borderColor: darkMode ? '#334155' : '#e2e8f0',
                borderRadius: '0.5rem',
              }}
              formatter={(value) => typeof value === 'number' ? value.toLocaleString() : value}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="rect"
              iconSize={14}
              formatter={(value) => <span style={{ color: darkMode ? '#e2e8f0' : '#1e293b', marginLeft: '5px' }}>{value}</span>}
            />
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  );
};
// --- END MODIFICATION ---

function App() {
 
  // --- STATE PERSISTENCE ---
  const [darkMode, setDarkMode] = useLocalStorageState('snowflow-darkMode', true);
  const [isAuthenticated, setIsAuthenticated] = useSessionState('snowflow-isAuthenticated', false);
  const [showLogin, setShowLogin] = useState(() => !isAuthenticated); 
  const [username, setUsername] = useSessionState('snowflow-username', 'admin');
 
  const correctPasswordRef = useRef(
    localStorage.getItem('snowflow-correctPassword') || '1234'
  );
 
  const [totalProcessedCount, setTotalProcessedCount] = useSessionState('snowflow-totalProcessedCount', 0);
  const [dashboardStats, setDashboardStats] = useSessionState('snowflow-dashboardStats', {
    successRate: 0,
    avgProcessTime: '0s', 
    activeUsers: 0
  });

  // --- TASK PERSISTENCE (Session Only) ---
  const [step, setStep] = useSessionState('snowflow-step', 1);
  const [files, setFiles] = useState([]); 
  const [fileMeta, setFileMeta] = useSessionState('snowflow-fileMeta', []); 
  const [uploadedFilePaths, setUploadedFilePaths] = useSessionState('snowflow-uploadedFilePaths', []);
  const [userPrompt, setUserPrompt] = useSessionState('snowflow-userPrompt', '');
  const [suggestedMetrics, setSuggestedMetrics] = useSessionState('snowflow-suggestedMetrics', []);
  const [selectedMetrics, setSelectedMetrics] = useSessionState('snowflow-selectedMetrics', []);
  const [results, setResults] = useSessionState('snowflow-results', null);
 
  const [showPassword, setShowPassword] = useState(false);

  const [password, setPassword] = useState(correctPasswordRef.current);
  const [authError, setAuthError] = useState('');
 
  // --- NEW: Default to 'home' instead of 'analysis'
  const [currentView, setCurrentView] = useState('home'); 
  const [sidebarOpen, setSidebarOpen] = useState(true);
 
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
 
  const [editingMetric, setEditingMetric] = useState(null);
 
  const [currentStage, setCurrentStage] = useState('');
  const [progress, setProgress] = useState(0);
 
  // Logs State (not persistent)
  const [logs, setLogs] = useState([]);
  const fileInputRef = useRef(null);
  const logsEndRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  // Settings State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // NOTIFICATION STATE
  const [notifications, setNotifications] = useState([
    { id: 1, text: 'Welcome to SnowFlow AI!' },
  ]);
  const [showNotifications, setShowNotifications] = useState(false);
  const notificationRef = useRef(null);
 
  // User Menu (for logout)
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef(null);
 
  const [showTableModal, setShowTableModal] = useState(false);
  
  // --- NEW: Analysis Dashboard State ---
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [analysisHistory, setAnalysisHistory] = useSessionState('snowflow-analysisHistory', []);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [availableData, setAvailableData] = useSessionState('snowflow-availableData', { companies: [], metrics: [], tables: [] });
  const analysisEndRef = useRef(null);
  // --- END NEW ---


  // --- PERSISTENCE EFFECTS ---
  useEffect(() => {
    // ... (Your existing useEffects... no changes)
    localStorage.setItem('snowflow-darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLogin(true);
    }
  }, [isAuthenticated]);


  // --- Utilities ---

  const addLog = async (message, type = 'info') => {
    // ... (Your existing addLog function... no changes)
    const timestamp = new Date().toLocaleTimeString();
    const newLog = { timestamp, message, type, id: Date.now() };
    setLogs(prev => [...prev, newLog]);
    try {
      await fetch(`${API_BASE}/logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, type, timestamp })
      });
    } catch (err) {
      console.error('Failed to send log to backend:', err);
    }
  };

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);
  
  // --- NEW: Scroll for analysis chat ---
  useEffect(() => {
    analysisEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [analysisHistory]);

  const fetchLogs = async () => {
    // ... (Your existing fetchLogs function... no changes)
    try {
      const response = await fetch(`${API_BASE}/logs`);
      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.statusText}`);
      }
      const data = await response.json(); 
      setLogs(prev => [...data.logs, ...prev.filter(p => !data.logs.find(l => l.id === p.id))]);
    } catch (err) {
      addLog(`Failed to fetch logs: ${err.message}.`, 'error');
    }
  };

  useEffect(() => {
    if (isAuthenticated && currentView === 'logs') {
      fetchLogs();
    }
  }, [currentView, isAuthenticated]); 

  // Click away listener for popovers
  useEffect(() => {
    // ... (Your existing click away listener... no changes)
    function handleClickOutside(event) {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        if (!event.target.closest('#notification-button')) {
          setShowNotifications(false);
        }
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        if (!event.target.closest('#user-menu-button')) {
          setShowUserMenu(false);
        }
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [notificationRef, userMenuRef]);

  // --- Auth Handlers ---

  const handleLogin = (e) => {
    // ... (Your existing handleLogin function... no changes)
    e.preventDefault();
    setAuthError('');
   
    if (username === 'admin' && password === correctPasswordRef.current) {
      setIsAuthenticated(true);
      setShowLogin(false);
      addLog(`User ${username} logged in successfully`, 'success');
    } else {
      setAuthError('Invalid credentials');
    }
  };
 
  // --- THIS FUNCTION HAS BEEN MODIFIED ---
  // Clears both SESSION task state and ANALYSIS state
  const resetTask = () => {
    // Reset pipeline state
    setStep(1);
    setFiles([]);
    setFileMeta([]);
    setUploadedFilePaths([]);
    setUserPrompt('');
    setSuggestedMetrics([]);
    setSelectedMetrics([]);
    setResults(null);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';

    // Reset analysis state
    setAnalysisHistory([]);
    setAvailableData({ companies: [], metrics: [], tables: [] });
    setAnalysisQuery('');
    setIsAnalyzing(false);
    setAnalysisError('');
   
    // Clear all session storage except auth
    Object.keys(sessionStorage).forEach(key => {
      if (key.startsWith('snowflow-') && key !== 'snowflow-isAuthenticated' && key !== 'snowflow-username') {
        sessionStorage.removeItem(key);
      }
    });
    addLog('🔄 App Reset', 'info');
  };
 
  const handleLogout = () => {
    // ... (Your existing handleLogout function... no changes)
    setIsAuthenticated(false);
    setShowLogin(true);
    addLog('User logged out', 'info');
   
    sessionStorage.clear();
   
    correctPasswordRef.current = '1234';
    localStorage.setItem('snowflow-correctPassword', '1234');
   
    setUsername('admin');
    setPassword('1234');
    resetTask(); 
  };

  // --- File Paste & Drag/Drop Handlers ---

  useEffect(() => {
    // ... (Your existing paste handler... no changes)
    const handlePaste = (e) => {
      if (step !== 1) return;
      const items = e.clipboardData.files;
      if (items.length > 0) {
        const pastedFiles = Array.from(items).filter(file => 
          ['application/pdf', 'image/png', 'image/jpeg'].includes(file.type)
        );
        if (pastedFiles.length > 0) {
          setFiles(prev => [...prev, ...pastedFiles]);
          setFileMeta(prev => [...prev, ...pastedFiles.map(f => ({ name: f.name, size: f.size }))]);
          addLog(`Pasted ${pastedFiles.length} file(s)`, 'info');
        }
      }
    };
    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, [step, setFileMeta]); 

  const handleDragOver = (e) => {
    // ... (Your existing drag/drop handlers... no changes)
    e.preventDefault();
    e.stopPropagation();
    if (step === 1) setIsDragging(true);
  };
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (step !== 1) return;
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter(file =>
      ['application/pdf', 'image/png', 'image/jpeg'].includes(file.type)
    );
    if (droppedFiles.length > 0) {
      setFiles(prev => [...prev, ...droppedFiles]);
      setFileMeta(prev => [...prev, ...droppedFiles.map(f => ({ name: f.name, size: f.size }))]);
      addLog(`Dropped ${droppedFiles.length} file(s)`, 'info');
    }
  };


  // --- Step 1: Upload Handlers ---

  const handleFileSelect = (e) => {
    // ... (Your existing file handlers... no changes)
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles]);
    setFileMeta(prev => [...prev, ...selectedFiles.map(f => ({ name: f.name, size: f.size }))]);
    setError('');
    setResults(null);
    setStep(1);
    addLog(`📁 Selected ${selectedFiles.length} file(s)`, 'info');
  };

  const uploadFiles = async () => {
    // ... (Your existing uploadFiles function... no changes)
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    addLog('📤 Uploading files to server...', 'info');
   
    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${errorText}`);
    }
   
    const result = await response.json();
    setUploadedFilePaths(result.files);
    addLog(`✅ Upload complete: ${result.files.length} file(s)`, 'success');
    return result;
  };

  const handleStep1 = async () => {
    // ... (Your existing step 1 handler... no changes)
    if (files.length === 0) {
      setError('Files not found (they may have been cleared on refresh). Please re-select your files.');
      return;
    }
    try {
      setProcessing(true);
      setError('');
      await uploadFiles();
      setStep(2);
      addLog('✅ Ready for metric suggestions', 'success');
    } catch (err) {
      setError(err.message);
      addLog(`❌ Upload error: ${err.message}`, 'error');
    } finally {
      setProcessing(false);
    }
  };

  // --- Step 2: Suggest Handlers ---

  const handleStep2 = async () => {
    // ... (Your existing step 2 handler... no changes)
    if (uploadedFilePaths.length === 0) {
      setError('No files were uploaded. Please go back to Step 1.');
      return;
    }
    try {
      setProcessing(true);
      setError('');
      addLog('💡 Requesting metric suggestions (Gemini)...', 'info');

      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          file_paths: uploadedFilePaths,
          user_prompt: userPrompt || null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get metric suggestions');
      }

      const result = await response.json();
     
      if (result.suggested_metrics && result.suggested_metrics.length > 0) {
        setSuggestedMetrics(result.suggested_metrics);
        setSelectedMetrics(result.suggested_metrics);
        setStep(3);
        addLog(`✅ Received ${result.suggested_metrics.length} metric suggestions`, 'success');
      } else {
        setError('No metrics were suggested. Please try again with a different prompt.');
        addLog('⚠️ No metrics suggested', 'error');
      }
    } catch (err) {
      setError(err.message);
      addLog(`❌ Suggestion error: ${err.message}`, 'error');
    } finally {
      setProcessing(false);
    }
  };

  // --- Step 3: Review & Custom Metric Handlers ---

  const toggleMetricSelection = (index) => {
    // ... (Your existing metric handlers... no changes)
    const metric = suggestedMetrics[index];
    const isSelected = selectedMetrics.some(m => m.name === metric.name);
    if (isSelected) {
      setSelectedMetrics(prev => prev.filter(m => m.name !== metric.name));
    } else {
      setSelectedMetrics(prev => [...prev, metric]);
    }
  };

  // --- NEW: SELECT/DESELECT ALL ---
  const handleSelectAll = () => {
    // This will select all *suggested* metrics
    // It creates a new Set to avoid duplicates if some are already selected
    const allMetrics = [...selectedMetrics];
    suggestedMetrics.forEach(sm => {
      if (!allMetrics.some(m => m.name === sm.name)) {
        allMetrics.push(sm);
      }
    });
    setSelectedMetrics(allMetrics);
  };
  
  const handleDeselectAll = () => {
    // This clears all selected metrics (suggested and custom)
    setSelectedMetrics([]);
  };
  // --- END NEW ---

  const addMetric = () => {
    setEditingMetric({ name: '', type: 'str', description: '' });
  };

  const saveMetric = () => {
    if (!editingMetric.name) {
      setError('Metric name is required');
      return;
    }
    if (editingMetric.id !== undefined) {
      setSelectedMetrics(prev => prev.map((m, i) => i === editingMetric.id ? editingMetric : m));
    } else {
      setSelectedMetrics(prev => [...prev, editingMetric]);
    }
    setEditingMetric(null);
    setError('');
  };

  const deleteMetric = (index) => {
    setSelectedMetrics(prev => prev.filter((_, i) => i !== index));
  };

  // --- Step 4: Process Handlers ---

  const handleStep3 = async () => {
    // ... (Your existing step 3 handler... no changes)
    if (selectedMetrics.length === 0) {
      setError('Please select at least one metric to extract');
      return;
    }
    try {
      setProcessing(true);
      setDashboardStats(prev => ({...prev, activeUsers: 1}));
      setError('');
      setStep(4);
      addLog('🔄 Starting processing pipeline...', 'info');
      // ... (rest of your step 3 logic)
      setCurrentStage('Step 1: Extracting Markdown');
      setProgress(10);
      addLog('📄 Extracting markdown (LandingAI)...', 'info');
      await new Promise(resolve => setTimeout(resolve, 500)); 
     
      setCurrentStage('Step 2: Metrics Suggested');
      setProgress(20);
      await new Promise(resolve => setTimeout(resolve, 200)); 
     
      setCurrentStage('Step 3: Review Complete');
      setProgress(30);
      await new Promise(resolve => setTimeout(resolve, 200)); 
     
      setCurrentStage('Step 4: Extracting Metrics');
      setProgress(40);
      addLog('🔍 Extracting metrics (Gemini)...', 'info');
      await new Promise(resolve => setTimeout(resolve, 500)); 
     
      setCurrentStage('Step 5: Deploying to Snowflake');
      setProgress(60);
      addLog('❄️ Deploying to Snowflake...', 'info');
     
      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          file_paths: uploadedFilePaths,
          user_prompt: userPrompt || null,
          selected_metrics: selectedMetrics
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Processing failed');
      }

      const result = await response.json();
      setProgress(100);
      setCurrentStage('Complete');
      setResults(result);
      setStep(5);
     
      setTotalProcessedCount(prevCount => prevCount + fileMeta.length); 
      setDashboardStats(prev => ({
        ...prev,
        successRate: 98.5, 
        avgProcessTime: '2.3s', 
      }));
     
      addLog('✅ Processing complete!', 'success');
      addLog(`✅ Created ${result.schema?.tables?.length || 0} tables`, 'success');
      addLog(`✅ Loaded ${result.deployment?.rows_loaded || 0} rows`, 'success');

    } catch (err) {
      setError(err.message);
      setCurrentStage('Error');
      setProgress(0);
      addLog(`❌ Pipeline error: ${err.message}`, 'error');
    } finally {
      setProcessing(false);
      setDashboardStats(prev => ({...prev, activeUsers: 0}));
    }
  };

  // --- Step 5: Reset Handler ---
  const resetAppTask = () => {
    // This function is now an alias for the main resetTask
    resetTask();
  };

  // --- Settings: Change Password (FIXED) ---
  const handleChangePassword = async (e) => {
    // ... (Your existing password change handler... no changes)
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }
    if (newPassword.length < 4) {
      setPasswordError('New password must be at least 4 characters');
      return;
    }
   
    addLog('Attempting to change password...', 'info');
    try {
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          if (currentPassword !== correctPasswordRef.current) {
            reject(new Error('Current password is incorrect'));
          } else {
            resolve({ success: true });
          }
        }, 1000);
      });

      correctPasswordRef.current = newPassword; 
      localStorage.setItem('snowflow-correctPassword', newPassword); 

      setPasswordSuccess('Password changed successfully! You will be logged out.');
      addLog('Password changed successfully', 'success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');

      setTimeout(handleLogout, 2000); 

    } catch (err) {
      setPasswordError(err.message);
      addLog(`Password change failed: ${err.message}`, 'error');
    }
  };
  
  
  // --- NEW: Analysis Dashboard Functions ---
  
  const fetchAnalysisMetadata = async () => {
    setAnalysisError('');
    addLog('Fetching analysis metadata...', 'info');
    try {
      const response = await fetch(`${API_BASE}/analysis/metadata`);
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to fetch metadata');
      }
      const data = await response.json();
      setAvailableData({
        companies: data.companies || [],
        metrics: data.metrics || [],
        tables: data.tables || [],
      });
      addLog(`✅ Found ${data.companies?.length || 0} companies and ${data.metrics?.length || 0} metrics.`, 'success');
    } catch (err) {
      addLog(`Failed to fetch metadata: ${err.message}`, 'error');
      setAnalysisError(`Failed to fetch metadata: ${err.message}`);
    }
  };
  
  // Fetch metadata when view changes to 'analysis'
  useEffect(() => {
    if (currentView === 'analysis' && availableData.companies.length === 0) {
      fetchAnalysisMetadata();
    }
  }, [currentView, availableData.companies.length]);

  

  const handleSendAnalysisQuery = async () => {
    if (!analysisQuery.trim() || isAnalyzing) return;
  
    setIsAnalyzing(true);
    setAnalysisError(''); // Clear any previous errors
    const userMessage = { role: 'user', content: analysisQuery };
    
    // Use functional update to ensure we have the latest history
    setAnalysisHistory(prevHistory => [...prevHistory, userMessage]);
    const currentQuery = analysisQuery;
    setAnalysisQuery('');
  
    try {
      // Get the history *before* adding the new model response
      const historyForBackend = [...analysisHistory, userMessage]
        .slice(-6) // Send last 6 messages
        .map(msg => ({
          role: msg.role === 'user' ? 'user' : 'model',
          // Send simple string for model, as backend expects
          content: msg.role === 'user' ? msg.content : (msg.content.summary || JSON.stringify(msg.content))
        }));
  
      const response = await fetch(`${API_BASE}/analysis/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: currentQuery,
          // Send all *except* the latest user message
          conversation_history: historyForBackend.slice(0, -1) 
        }),
      });
  
      if (!response.ok) {
        const errData = await response.json();
        // Don't throw - handle gracefully
        const errorMessage = errData.detail || 'I had trouble processing your request. Could you try rephrasing it?';
        
        addLog(`Analysis request failed: ${errorMessage}`, 'warning');
        setAnalysisHistory(prev => [...prev, { 
          role: 'model', 
          content: { 
            summary: "I'm having trouble understanding your request.",
            insights: [
              "- Could you try rephrasing your question?",
              "- Try asking about specific companies or metrics",
              "- For example: 'Compare the assets of Microsoft and Apple'",
              "- Or: 'Which company has the highest total equity?'"
            ]
          } 
        }]);
        setIsAnalyzing(false);
        return; // Don't throw, just return
      }
  
      const result = await response.json();
      
      // Check if result has an error field (but not a hard error)
      if (result.error && !result.summary) {
        // Backend returned an error object
        addLog(`Analysis issue: ${result.error}`, 'info');
        setAnalysisHistory(prev => [...prev, { 
          role: 'model', 
          content: { 
            summary: "Let me help you rephrase that.",
            insights: result.insights || [
              "- Try asking in a different way",
              "- Be more specific about what you want to know",
              "- I can help with comparisons, rankings, and financial metrics"
            ]
          } 
        }]);
      } else {
        // Successful response
        addLog('Analysis successful', 'success');
        setAnalysisHistory(prev => [...prev, { role: 'model', content: result }]);
      }
  
    } catch (err) {
      // Network or parsing errors - be graceful
      console.error('Analysis error:', err);
      addLog(`Analysis communication error: ${err.message}`, 'warning');
      
      setAnalysisHistory(prev => [...prev, { 
        role: 'model', 
        content: { 
          summary: "I'm having trouble connecting right now.",
          insights: [
            "- Please check your internet connection",
            "- Try your question again in a moment",
            "- If the problem persists, contact support"
          ]
        } 
      }]);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // --- END NEW ---


  // --- SNOWFLOW THEME ---

  const bgClass = darkMode 
    // ... (Your existing theme classes... no changes)
    ? 'bg-gradient-to-br from-gray-900 via-blue-950 to-gray-900' 
    : 'bg-gradient-to-br from-slate-50 to-blue-100';
 
  const cardClass = darkMode
    ? 'bg-slate-900/50 backdrop-blur-lg border border-blue-900/50'
    : 'bg-white/70 backdrop-blur-lg border border-gray-200 shadow-sm';
 
  const textClass = darkMode ? 'text-white' : 'text-slate-900';
  const textMutedClass = darkMode ? 'text-slate-400' : 'text-slate-600';
 
  const accentGradient = 'bg-gradient-to-r from-blue-500 to-cyan-400';
  const accentHover = 'hover:from-blue-600 hover:to-cyan-500';
  const accentText = darkMode ? 'text-cyan-300' : 'text-cyan-700';
  const accentRing = 'focus:ring-cyan-500';

  const tableHeaderClass = darkMode ? 'bg-slate-800' : 'bg-gray-100';
  const tableCellClass = darkMode ? 'border-slate-700' : 'border-gray-200';

  // --- Login View ---
  if (showLogin) {
    return (
      // ... (Your existing Login View... no changes)
      <div className={`min-h-screen ${bgClass} flex items-center justify-center p-4 relative overflow-hidden`}>
        <Snowfall />
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        </div>

        <div className={`${cardClass} rounded-3xl shadow-2xl p-8 md:p-12 max-w-md w-full relative z-10`}>
          <div className="text-center mb-8">
            <div className={`p-4 rounded-2xl inline-block mb-4 ${accentGradient}`}>
              <TrendingUp className="w-12 h-12 text-white" />
            </div>
            <h1 className={`text-3xl font-bold ${textClass} mb-2`}>SnowFlow AI</h1>
            <p className={textMutedClass}>Intelligent Document Processing</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className={`block ${textClass} font-medium mb-2 flex items-center gap-2`}>
                <Mail className="w-4 h-4" />
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={`w-full px-4 py-3 rounded-xl ${darkMode ? 'bg-slate-700/50 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing} transition-all`}
                placeholder="Enter your username"
              />
            </div>

            <div>
              <label className={`block ${textClass} font-medium mb-2 flex items-center gap-2`}>
                <Lock className="w-4 h-4" />
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`w-full px-4 py-3 rounded-xl ${darkMode ? 'bg-slate-700/50 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing} transition-all pr-12`}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2"
                >
                  {showPassword ? <EyeOff className="w-5 h-5 text-slate-400" /> : <Eye className="w-5 h-5 text-slate-400" />}
                </button>
              </div>
            </div>

            {authError && (
              <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-xl">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <p className="text-red-300 text-sm">{authError}</p>
              </div>
            )}

            <button
              type="submit"
              className={`w-full py-4 ${accentGradient} ${accentHover} text-white font-bold rounded-xl transition-all transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center justify-center gap-2`}
            >
              <Lock className="w-5 h-5" />
              Sign In
            </button>
          </form>
        </div>
      </div>
    );
  }


  // --- Main App Layout ---
  return (
    <div 
      className={`min-h-screen ${bgClass} transition-all duration-300 ${textClass} relative z-0`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <Snowfall />

      {/* Header */}
      <header className={`${darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white/80 border-slate-200'} backdrop-blur-xl border-b sticky top-0 z-40`}>
        {/* ... (Your existing Header... no changes) ... */}
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className={`p-2 ${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} rounded-lg transition-colors lg:hidden`}
              >
                <Menu className="w-6 h-6" />
              </button>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-xl ${accentGradient}`}>
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className={`text-xl font-bold ${textClass}`}>SnowFlow AI</h1>
                  <p className={`text-xs ${textMutedClass}`}>Document Intelligence</p>
                </div>
              </div>
            </div>
           
            <div className="flex items-center gap-3 relative">
              {/* --- THIS BUTTON HAS BEEN MODIFIED --- */}
              <button 
                onClick={resetTask}
                title="Reset & Refresh"
                className={`relative p-2 ${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} rounded-lg transition-colors`}
              >
                <RefreshCw className="w-5 h-5" />
              </button>
              {/* --- END MODIFICATION --- */}

              <button 
                id="notification-button"
                onClick={() => setShowNotifications(!showNotifications)} 
                className={`relative p-2 ${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} rounded-lg transition-colors`}
              >
                <Bell className="w-5 h-5" />
                {notifications.length > 0 && (
                  <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-current"></span>
                )}
              </button>

              {showNotifications && (
                <div 
                  ref={notificationRef}
                  className={`${cardClass} absolute top-12 right-0 w-80 rounded-lg shadow-2xl z-50 overflow-hidden animate-fade-in-down`}
                >
                  <div className={`p-3 flex items-center justify-between border-b ${darkMode ? 'border-slate-700' : 'border-gray-200'}`}>
                    <h4 className="font-semibold">Notifications</h4>
                    {notifications.length > 0 && (
                      <button 
                        onClick={() => setNotifications([])}
                        className={`text-xs ${accentText} hover:underline`}
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                  <div className="p-2 max-h-64 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <p className={`text-sm text-center p-4 ${textMutedClass}`}>No new notifications</p>
                    ) : (
                      notifications.map(notif => (
                        <div key={notif.id} className={`text-sm p-3 rounded-lg ${darkMode ? 'hover:bg-slate-800' : 'hover:bg-slate-100'}`}>
                          {notif.text}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 ${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} rounded-lg transition-colors`}
              >
                {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
              </button>

              <div className="relative" ref={userMenuRef}>
                <button
                  id="user-menu-button"
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg ${darkMode ? 'bg-cyan-900/30' : 'bg-cyan-500/10'} transition-colors ${darkMode ? 'hover:bg-cyan-900/50' : 'hover:bg-cyan-500/20'}`}
                >
                  <User className={`w-4 h-4 ${accentText}`} />
                  <span className={`text-sm font-medium ${accentText}`}>{username}</span>
                </button>

                {showUserMenu && (
                  <div className={`${cardClass} absolute top-12 right-0 w-48 rounded-lg shadow-2xl z-50 overflow-hidden animate-fade-in-down`}>
                    <button
                      onClick={handleLogout}
                      className={`w-full flex items-center gap-3 px-4 py-3 text-left ${darkMode ? 'hover:bg-red-500/30' : 'hover:bg-red-500/10'} text-red-400 transition-colors`}
                    >
                      <LogOut className="w-5 h-5" />
                      <span>Logout</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:sticky top-[73px] left-0 h-[calc(100vh-73px)] w-64 ${darkMode ? 'bg-slate-900/50' : 'bg-white/80'} backdrop-blur-xl border-r ${darkMode ? 'border-slate-800' : 'border-slate-200'} transition-transform duration-300 z-30`}>
          <nav className="p-4 space-y-2">
            <button
              onClick={() => setCurrentView('home')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                currentView === 'home' 
                  ? `${accentGradient} text-white shadow-lg` 
                  : `${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} ${textClass}`
              }`}
            >
              <Home className="w-5 h-5" />
              <span className="font-medium">Dashboard & Process</span>
            </button>
            
            {/* --- NEW: Analysis Dashboard Button --- */}
            <button
              onClick={() => setCurrentView('analysis')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                currentView === 'analysis' 
                  ? `${accentGradient} text-white shadow-lg` 
                  : `${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} ${textClass}`
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              <span className="font-medium">Analysis Dashboard</span>
            </button>
            {/* --- END NEW --- */}
           
            <button
              onClick={() => setCurrentView('logs')}
              // ... (Your existing Logs button)
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                currentView === 'logs' 
                  ? `${accentGradient} text-white shadow-lg` 
                  : `${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} ${textClass}`
              }`}
            >
              <Terminal className="w-5 h-5" />
              <span className="font-medium">Activity Logs</span>
              {logs.length > 0 && (
                <span className="ml-auto bg-cyan-500 text-white text-xs px-2 py-0.5 rounded-full">{logs.length}</span>
              )}
            </button>
           
            <button
              onClick={() => setCurrentView('settings')}
              // ... (Your existing Settings button)
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                currentView === 'settings' 
                  ? `${accentGradient} text-white shadow-lg` 
                  : `${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'} ${textClass}`
              }`}
            >
              <Settings className="w-5 h-5" />
              <span className="font-medium">Settings</span>
            </button>
          </nav>

          <div className="p-4">
            {/* ... (Your existing Quick Stats box... no changes) ... */}
            <div className={`${cardClass} rounded-xl p-4 space-y-3 transition-transform duration-300 hover:scale-105`}>
              <h3 className={`text-sm font-semibold ${textClass} mb-3`}>Quick Stats</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`text-xs ${textMutedClass}`}>Processed</span>
                  <span className={`text-sm font-bold ${textClass}`}>{totalProcessedCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`text-xs ${textMutedClass}`}>Success Rate</span>
                  <span className={`text-sm font-bold ${dashboardStats.successRate > 0 ? 'text-green-400' : textClass}`}>
                    {dashboardStats.successRate}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`text-xs ${textMutedClass}`}>Avg Time</span>
                  <span className={`text-sm font-bold ${textClass}`}>{dashboardStats.avgProcessTime}</span>
                </div>
                 <div className="flex items-center justify-between">
                  {/* --- THIS LINE IS FIXED --- */}
                  <span className={`text-xs ${textMutedClass}`}>Active</span>
                  <span className={`text-sm font-bold ${dashboardStats.activeUsers > 0 ? 'text-cyan-400' : textClass}`}>
                    {dashboardStats.activeUsers}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 lg:p-8">

          {/* Step Indicator (Shared across Home View) */}
          {currentView === 'home' && (
            // ... (Your existing Step Indicator... no changes)
            <div className={`${cardClass} rounded-2xl shadow-xl p-6 mb-8`}>
              <div className="flex items-center justify-between">
                {[1, 2, 3, 4, 5].map((s) => (
                  <React.Fragment key={s}>
                    <div className="flex flex-col items-center flex-1">
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg transition-all ${
                          step === s ? `${accentGradient} text-white animate-pulse` :
                          step > s
                            ? 'bg-teal-600 text-white'
                            : `${darkMode ? 'bg-slate-700 text-slate-400' : 'bg-slate-200 text-slate-500'}`
                        }`}
                      >
                        {step > s ? <CheckCircle className="w-6 h-6" /> : s}
                      </div>
                      <p className={`mt-2 text-sm font-medium text-center ${
                        step >= s ? textClass : textMutedClass
                      }`}>
                        {s === 1 && 'Upload Docs'}
                        {s === 2 && 'Prompt AI'}
                        {s === 3 && 'Review'}
                        {s === 4 && 'Process'}
                        {s === 5 && 'Results'}
                      </p>
                    </div>
                    {s < 5 && (
                      <div className={`flex-1 h-1 mx-2 ${
                        step > s
                          ? 'bg-teal-600'
                          : `${darkMode ? 'bg-slate-700' : 'bg-slate-200'}`
                      }`} />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* View Router */}
          
          {/* --- NEW: Analysis View --- */}
          {currentView === 'analysis' && (
            <FadeIn key="analysis-view">
              <div className="h-[calc(100vh-120px)] flex flex-col lg:flex-row gap-6">
                
                {/* Left Side: Data Context */}
                <div className={`lg:w-1/3 ${cardClass} rounded-2xl shadow-xl p-6 flex flex-col`}>
                  <h2 className={`text-xl font-bold ${textClass} mb-4`}>Available Data</h2>
                  <p className={`${textMutedClass} text-sm mb-4`}>
                    Ask questions about the following companies and metrics.
                  </p>
                  
                  <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                    <div>
                      <h3 className={`font-semibold ${accentText} mb-2`}>Companies ({availableData.companies.length})</h3>
                      <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                        {availableData.companies.length > 0 ? availableData.companies.map(c => (
                          <span key={c} className={`px-2 py-0.5 text-xs rounded-full ${darkMode ? 'bg-slate-700' : 'bg-slate-200'}`}>
                            {c}
                          </span>
                        )) : <p className={`text-sm ${textMutedClass}`}>No companies found.</p>}
                      </div>
                    </div>
                    
                    <div>
                      <h3 className={`font-semibold ${accentText} mb-2`}>Metrics ({availableData.metrics.length})</h3>
                      <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                        {availableData.metrics.length > 0 ? availableData.metrics.map(m => (
                          <span key={m} className={`px-2 py-0.5 text-xs rounded-full ${darkMode ? 'bg-slate-700' : 'bg-slate-200'}`}>
                            {m}
                          </span>
                        )) : <p className={`text-sm ${textMutedClass}`}>No metrics found.</p>}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Side: Chat Interface */}
                <div className={`flex-1 ${cardClass} rounded-2xl shadow-xl flex flex-col overflow-hidden`}>
                  {/* Chat History */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {analysisHistory.length === 0 && (
                      <div className="text-center h-full flex flex-col justify-center items-center">
                        <BarChart3 className={`w-16 h-16 ${textMutedClass} opacity-50 mb-4`} />
                        <h3 className={`text-xl font-semibold ${textClass}`}>Analysis Dashboard</h3>
                        <p className={textMutedClass}>Ask a question to get started.</p>
                        <p className={`${textMutedClass} text-sm mt-2`}>e.g., "Compare revenue for all companies"</p>
                      </div>
                    )}

                    {analysisHistory.map((msg, idx) => (
                      <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.role === 'user' ? (
                          <div className={`p-4 rounded-2xl max-w-lg ${accentGradient} text-white`}>
                            {msg.content}
                          </div>
                        ) : (
                          <div className={`p-4 rounded-2xl max-w-full w-full ${darkMode ? 'bg-slate-800' : 'bg-slate-100'}`}>
                            {/* REMOVED: Red error styling - now all responses look the same */}
                            <div className="space-y-4">
                              <p>{msg.content.summary}</p>
                              {msg.content.insights && msg.content.insights.length > 0 && (
                                <div>
                                  <h4 className={`font-semibold ${textClass} mb-2`}>Insights:</h4>
                                  <ul className="space-y-1">
                                    {msg.content.insights.map((insight, i) => (
                                      <li key={i} className={textMutedClass}>{insight}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {msg.content.chart && (
                                <div className={`${darkMode ? 'bg-slate-900' : 'bg-white'} p-4 rounded-lg`}>
                                  <RenderAnalysisChart 
                                    chart={msg.content.chart} 
                                    darkMode={darkMode}
                                    textMutedClass={textMutedClass}
                                    accentText={accentText}
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                    <div ref={analysisEndRef} />
                  </div>

                  {/* Chat Input */}
                  <div className={`p-4 border-t ${darkMode ? 'border-slate-700' : 'border-slate-200'}`}>
                    {/* REMOVED: analysisError display - errors are now shown in chat */}
                    <div className="relative">
                      <input
                        type="text"
                        value={analysisQuery}
                        onChange={(e) => setAnalysisQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendAnalysisQuery()}
                        placeholder={isAnalyzing ? "Analyzing..." : "Ask about the data..."}
                        disabled={isAnalyzing}
                        className={`w-full px-4 py-3 pr-12 rounded-xl ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing} transition-all`}
                      />
                      <button
                        onClick={handleSendAnalysisQuery}
                        disabled={isAnalyzing || !analysisQuery.trim()}
                        className={`absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg ${accentGradient} ${accentHover} text-white disabled:from-gray-500 disabled:to-gray-600`}
                      >
                        {isAnalyzing ? <Loader className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>
                </div>

              </div>
            </FadeIn>
          )}
          {/* --- END NEW --- */}
          
          {currentView === 'logs' && (
            <FadeIn key="logs-view">
              {/* ... (Your existing Logs view... no changes) ... */}
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className={`text-3xl font-bold ${textClass}`}>Activity Logs</h2>
                    <p className={textMutedClass}>Real-time system activity and processing logs</p>
                  </div>
                  <button
                    onClick={() => setLogs([])}
                    className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                  >
                    Clear Logs
                  </button>
                </div>
                <div className={`${cardClass} rounded-2xl shadow-xl overflow-hidden`}>
                  <div className={`${darkMode ? 'bg-slate-900/50' : 'bg-slate-100/50'} p-6 max-h-[70vh] overflow-y-auto font-mono text-sm`}>
                    {logs.length === 0 ? (
                      <div className="text-center py-12">
                        <Terminal className={`w-16 h-16 ${textMutedClass} mx-auto mb-4 opacity-50`} />
                        <p className={textMutedClass}>No logs yet. Start processing documents to see activity.</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {logs.map((log) => (
                          <div
                            key={log.id}
                            className={`p-3 rounded-lg transition-all ${
                              log.type === 'error' 
                                ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                              log.type === 'success' 
                                ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                              darkMode ? 'bg-slate-800/50 text-slate-300' : 'bg-white text-slate-700'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <Clock className="w-4 h-4 mt-0.5 opacity-50" />
                              <div className="flex-1">
                                <span className="opacity-75 text-xs">[{log.timestamp}]</span>
                                <p className="mt-1">{log.message}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                        <div ref={logsEndRef} />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </FadeIn>
          )}

          {currentView === 'settings' && (
            <FadeIn key="settings-view">
              {/* ... (Your existing Settings view... no changes) ... */}
              <div className="space-y-6 max-w-2xl">
                <div>
                  <h2 className={`text-3xl font-bold ${textClass}`}>Settings</h2>
                  <p className={textMutedClass}>Configure your application preferences</p>
                </div>
                <div className={`${cardClass} rounded-2xl shadow-xl p-8`}>
                  <h3 className={`text-xl font-semibold ${textClass} mb-4`}>Security</h3>
                  <form onSubmit={handleChangePassword} className="space-y-4">
                    <div>
                      <label className={`block ${textClass} font-medium mb-2`}>Current Password</label>
                      <input
                        type="password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing}`}
                      />
                    </div>
                    <div>
                      <label className={`block ${textClass} font-medium mb-2`}>New Password</label>
                      <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing}`}
                      />
                    </div>
                    <div>
                      <label className={`block ${textClass} font-medium mb-2`}>Confirm New Password</label>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing}`}
                      />
                    </div>

                    {passwordError && (
                      <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-xl">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <p className="text-red-300 text-sm">{passwordError}</p>
                      </div>
                    )}
                    {passwordSuccess && (
                      <div className="flex items-center gap-2 p-3 bg-green-500/20 border border-green-500/50 rounded-xl">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <p className="text-green-300 text-sm">{passwordSuccess}</p>
                      </div>
                    )}

                    <button
                      type="submit"
                      className={`px-6 py-2 ${accentGradient} ${accentHover} text-white font-semibold rounded-lg shadow transition-colors`}
                    >
                      Change Password
                    </button>
                  </form>
                </div>
              </div>
            </FadeIn>
          )}

          {currentView === 'home' && (
            <div className="space-y-6">
              {/* ... (Your existing Home view steps 1-5... no changes) ... */}
              <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
                <h2 className={`text-3xl font-bold ${textClass} mb-6`}>Document Extraction Pipeline</h2>
               
                {/* Step 1: Upload */}
                {step === 1 && (
                  <FadeIn key="step1">
                    {/* ... (Your existing Step 1 JSX) ... */}
                    <div className="space-y-6">
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        onChange={handleFileSelect}
                        accept=".pdf,.png,.jpg,.jpeg"
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className={`flex flex-col items-center justify-center gap-3 px-6 py-10 border-2 ${
                          isDragging 
                            ? 'border-cyan-500 bg-cyan-500/10' 
                            : 'border-dashed border-gray-500 hover:border-cyan-500'
                        } ${textClass} rounded-xl cursor-pointer transition-all`}
                      >
                        <Upload className="w-10 h-10" />
                        <span className="font-semibold text-lg">{isDragging ? 'Drop files here' : 'Click to choose files, or drag & drop'}</span>
                        <p className={textMutedClass}>You can also paste files from your clipboard</p>
                      </label>

                      {fileMeta.length > 0 && (
                        <div className={`p-4 rounded-xl ${darkMode ? 'bg-slate-700/50' : 'bg-slate-100/50'}`}>
                          <p className={`${textClass} font-semibold mb-2`}>Files Selected ({fileMeta.length}):</p>
                          <ul className="space-y-1 max-h-32 overflow-y-auto">
                            {fileMeta.map((file, idx) => (
                              <li key={`${file.name}-${idx}`} className={`flex justify-between items-center text-sm ${textMutedClass}`}>
                                <span>{file.name}</span>
                                <span>{(file.size / 1024).toFixed(1)} KB</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {error && (
                        <div className="flex items-center gap-3 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg">
                          <AlertCircle className="w-5 h-5 text-red-300" />
                          <p className="text-red-300">{error}</p>

                        </div>
                      )}

                      <button
                        onClick={handleStep1}
                        disabled={fileMeta.length === 0 || processing} 
                        className="w-full py-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
                      >
                        {processing ? (
                          <>
                            <Loader className="w-5 h-5 animate-spin" />
                            <span>Uploading...</span>
                          </>
                        ) : (
                          <>
                            <span>Upload & Start AI Suggestion</span>
                            <ArrowRight className="w-5 h-5" />
                          </>
                        )}
                      </button>
                    </div>
                  </FadeIn>
                )}

                {/* Step 2: Suggest Metrics */}
                {step === 2 && (
                  <FadeIn key="step2">
                    {/* ... (Your existing Step 2 JSX) ... */}
                    <div className="space-y-6">
                      <div className="text-center">
                        <Sparkles className={`w-12 h-12 ${accentText} mx-auto mb-2`} />
                        <h3 className={`text-xl font-semibold ${textClass}`}>Define Extraction Goals</h3>
                        <p className={textMutedClass}>Provide a prompt for the AI to suggest relevant metrics.</p>
                      </div>
                       
                      <div>
                        <label className={`block ${textClass} font-medium mb-2`}>Your Prompt (Optional)</label>
                        <textarea
                          value={userPrompt}
                          onChange={(e) => setUserPrompt(e.target.value)}
                          placeholder="e.g., Extract the account holder name and the total revenue figure."
                          className={`w-full px-4 py-3 rounded-lg ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing}`}
                          rows={3}
                        />
                      </div>

                      {error && (
                        <div className="flex items-center gap-3 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg">
                          <AlertCircle className="w-5 h-5 text-red-300" />
                          <p className="text-red-300">{error}</p>
                        </div>
                      )}

                      <div className="flex gap-4">
                        <button
                          onClick={() => setStep(1)}
                          className="flex-1 py-4 bg-slate-600 hover:bg-slate-700 text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
                        >
                          <ArrowLeft className="w-5 h-5" />
                          <span>Back</span>
                        </button>
                        <button
                          onClick={handleStep2}
                          disabled={processing}
                          className={`flex-1 py-4 ${accentGradient} ${accentHover} disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3`}
                        >
                          {processing ? (
                            <>
                              <Loader className="w-5 h-5 animate-spin" />
                              <span>Suggesting...</span>
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-5 h-5" />
                              <span>Suggest Metrics</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </FadeIn>
                )}

                {/* Step 3: Review Metrics */}
                {step === 3 && (
                  <FadeIn key="step3">
                    {/* ... (Your existing Step 3 JSX) ... */}
                    <div className="space-y-6">
                      {/* --- MODIFIED: Added flex-wrap and new buttons --- */}
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div>
                          <h3 className={`text-xl font-semibold ${textClass}`}>Review & Customize</h3>
                          <p className={textMutedClass}>Select, edit, or add metrics before final processing.</p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={handleSelectAll}
                            className={`px-3 py-2 text-xs bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg transition-colors`}
                          >
                            Select All
                          </button>
                          <button
                            onClick={handleDeselectAll}
                            className={`px-3 py-2 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors`}
                          >
                            Deselect All
                          </button>
                          <button
                            onClick={addMetric}
                            className={`px-4 py-2 ${accentGradient} ${accentHover} text-white rounded-lg flex items-center gap-2 transition-colors`}
                          >
                            <Plus className="w-4 h-4" />
                            Add Custom
                          </button>
                        </div>
                      </div>
                      {/* --- END MODIFICATION --- */}


                      {suggestedMetrics.length > 0 && (
                        <div>
                          <h4 className={`${textClass} font-semibold mb-3`}>AI Suggestions:</h4>
                          <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                            {suggestedMetrics.map((metric, idx) => {
                              const isSelected = selectedMetrics.some(m => m.name === metric.name);
                              return (
                                <div
                                  key={idx}
                                  onClick={() => toggleMetricSelection(idx)}
                                  className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                                    isSelected
                                      ? `${darkMode ? 'bg-cyan-900 border-2 border-cyan-500' : 'bg-cyan-50 border-2 border-cyan-500'}`
                                      : `${darkMode ? 'bg-slate-700/50 hover:bg-slate-700' : 'bg-slate-100 hover:bg-slate-200'} border-2 border-transparent`
                                  }`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={isSelected}
                                    readOnly
                                    className="w-5 h-5 rounded text-cyan-600 focus:ring-cyan-500"
                                  />
                                  <div className="flex-1">
                                    <p className={`font-semibold ${textClass}`}>{metric.name}</p>
                                    <p className={`text-sm ${textMutedClass}`}>{metric.description}</p>
                                  </div>
                                  <span className={`text-xs px-2 py-1 rounded-full ${darkMode ? 'bg-slate-600' : 'bg-slate-300'} ${textClass}`}>
                                    {metric.type.toUpperCase()}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      <div>
                        <h4 className={`${textClass} font-semibold mb-3`}>
                          Final Metrics to Extract ({selectedMetrics.length}):
                        </h4>
                        <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                          {selectedMetrics.map((metric, idx) => (
                            <div
                              key={idx}
                              className={`flex items-center gap-3 p-3 rounded-lg ${
                                darkMode ? 'bg-slate-700' : 'bg-slate-100'
                              }`}
                            >
                              <Database className={`w-5 h-5 ${accentText}`} />
                              <div className="flex-1">
                                <p className={`font-semibold ${textClass}`}>{metric.name}</p>
                                <p className={`text-sm ${textMutedClass}`}>{metric.description}</p>
                              </div>
                              <span className={`text-xs px-2 py-1 rounded-full ${darkMode ? 'bg-slate-600' : 'bg-slate-300'} ${textClass}`}>
                                {metric.type.toUpperCase()}
                              </span>
                              <button
                                onClick={() => setEditingMetric({ ...metric, id: idx })}
                                className="p-1 hover:bg-slate-600 rounded-lg transition-colors"
                              >
                                <Edit className="w-4 h-4 text-cyan-400" />
                              </button>
                              <button
                                onClick={() => deleteMetric(idx)}
                                className="p-1 hover:bg-red-500/50 rounded-lg transition-colors"
                              >
                                <Trash2 className="w-4 h-4 text-red-400" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {error && (
                        <div className="flex items-center gap-3 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg">
                          <AlertCircle className="w-5 h-5 text-red-300" />
                          <p className="text-red-300">{error}</p>
                        </div>
                      )}

                      <div className="flex gap-4">
                        <button
                          onClick={() => setStep(2)}
                          className="flex-1 py-4 bg-slate-600 hover:bg-slate-700 text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
                        >
                          <ArrowLeft className="w-5 h-5" />
                          <span>Back</span>
                        </button>
                        <button
                          onClick={handleStep3}
                          disabled={selectedMetrics.length === 0 || processing}
                          className="flex-1 py-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
                        >
                          {processing ? (
                            <>
                              <Loader className="w-5 h-5 animate-spin" />
                              <span>Deploying...</span>
                            </>
                          ) : (
                            <>
                              <Database className="w-5 h-5" />
                              <span>Start Extraction & Deployment</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </FadeIn>
                )}
               
                {/* Step 4: Processing */}
                {step === 4 && processing && (
                  <FadeIn key="step4">
                    {/* ... (Your existing Step 4 JSX) ... */}
                    <div className="space-y-6 text-center">
                      <Activity className={`w-16 h-16 ${accentText} mx-auto mb-4 animate-pulse`} />
                      <h3 className={`text-2xl font-bold ${textClass}`}>{currentStage}</h3>
                      <div className={`w-full ${darkMode ? 'bg-slate-700' : 'bg-slate-200'} rounded-full h-4 overflow-hidden`}>
                        <div 
                          className={`h-full transition-all duration-500 ${accentGradient}`}
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <span className={`text-xl font-bold ${textClass} mt-2 block`}>{progress}% Complete</span>
                    </div>
                  </FadeIn>
                )}

                {/* Step 5: Results */}
                {step === 5 && results && (
                  <FadeIn key="step5">
                    {/* ... (Your existing Step 5 JSX) ... */}
                    <div className="space-y-6">
                      <div className="bg-green-500/20 backdrop-blur-lg rounded-xl p-6 border border-green-500/30">
                        <div className="flex flex-wrap items-center justify-between gap-4">
                          <div className="flex items-center gap-4">
                            <CheckCircle className="w-10 h-10 text-green-400" />
                            <div>
                              <h3 className="text-xl font-bold text-white">Success!</h3>
                              <p className="text-green-200">Metrics extracted and deployed.</p>
                            </div>
                          </div>
                          <div className="flex gap-3">
                            <button
                              onClick={() => setShowTableModal(true)}
                              className={`px-4 py-2 ${accentGradient} ${accentHover} text-white font-semibold rounded-lg shadow transition-colors`}
                            >
                              View Table Entries
                            </button>
                            <button
                              onClick={resetTask}
                              className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
                            >
                              New Process
                            </button>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {results.extracted_metrics_by_document ? (
                          Object.entries(results.extracted_metrics_by_document).map(([docName, metrics]) => (
                            <div key={docName} className={`${darkMode ? 'bg-slate-800' : 'bg-slate-100'} p-4 rounded-xl shadow-lg`}>
                              <h4 className={`font-semibold mb-3 pb-2 border-b ${darkMode ? 'border-slate-600' : 'border-slate-300'} ${textClass} truncate`}>
                                {docName}
                              </h4>
                              <div className="space-y-2">
                                {Object.entries(metrics).map(([key, value]) => (
                                  <div key={key} className="grid grid-cols-3 gap-4 items-start">
                                    <p className={`${textMutedClass} col-span-1 break-words capitalize`}>
                                      {key.replace(/_/g, ' ')}:
                                    </p>
                                    <p className={`font-bold ${accentText} col-span-2 text-right break-words`}>
                                      {String(value)}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-100'} p-4 rounded-xl`}>
                            <div className="space-y-2">
                              {results.extracted_metrics && Object.entries(results.extracted_metrics).map(([key, value]) => (
                                <div key={key} className="grid grid-cols-3 gap-4 items-start">
                                  {/* --- THIS LINE IS FIXED --- */}
                                  <p className={`${textMutedClass} col-span-1 break-words capitalize`}>
                                    {key.replace(/_/g, ' ')}:
                                  </p>
                                  <p className={`font-bold ${accentText} col-span-2 text-right break-words`}>
                                    {String(value)}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className={`p-6 rounded-xl ${darkMode ? 'bg-slate-700/50' : 'bg-slate-100/50'}`}>
                        <h4 className={`font-bold ${textClass} mb-3 flex items-center gap-2`}>
                          <Database className="w-5 h-5 text-green-400" /> Snowflake Deployment Details
                        </h4>
                        
                        {/* --- FIXED: Typo and added optional chaining --- */}
                        <p className={textMutedClass}>
                          <span className="font-semibold">Status:</span> {results.deployment?.status || 'N/A'}
                        </p>
                        <p className={textMutedClass}>
                          <span className="font-semibold">Target:</span> {results.deployment?.database}.{results.deployment?.schema}
                        </p>
                        {/* --- END FIX --- */}
                        
                      </div>
                    </div>
                  </FadeIn>
                )}
              </div>
            </div>
          )}
       
          {/* Edit Metric Modal */}
          {editingMetric && (
            // ... (Your existing Edit Metric Modal... no changes)
            <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
              <div className={`${darkMode ? 'bg-slate-900' : 'bg-white'} rounded-2xl shadow-2xl max-w-md w-full p-6`}>
                <h4 className={`text-xl font-bold ${textClass} mb-4`}>
                  {editingMetric.id !== undefined ? 'Edit Metric' : 'Add Metric'}
                </h4>
                <div className="space-y-4">
                  <div>
                    <label className={`block ${textClass} font-medium mb-2`}>Name (snake_case)</label>
                    <input
                      type="text"
                      value={editingMetric.name}
                      onChange={(e) => setEditingMetric({ ...editingMetric, name: e.target.value })}
                      className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing}`}
                      placeholder="metric_name"
                    />
                  </div>
                  <div>
                    <label className={`block ${textClass} font-medium mb-2`}>Type</label>
                    <select
                      value={editingMetric.type}
                      onChange={(e) => setEditingMetric({ ...editingMetric, type: e.target.value })}
                      className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing}`}
                    >
                      <option value="str">String</option>
                      <option value="int">Integer</option>
                      <option value="float">Float</option>
                      <option value="bool">Boolean</option>
                    </select>
                  </div>
                  <div>
                    <label className={`block ${textClass} font-medium mb-2`}>Description</label>
                    <textarea
                      value={editingMetric.description}
                      onChange={(e) => setEditingMetric({ ...editingMetric, description: e.target.value })}
                      className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-slate-700 text-white border-slate-600' : 'bg-white text-slate-900 border-slate-300'} border focus:outline-none focus:ring-2 ${accentRing}`}
                      rows={3}
                      placeholder="A description of the metric for the AI model."
                    />
                  </div>
                </div>
                <div className="flex gap-4 mt-6">
                  <button
                    onClick={() => setEditingMetric(null)}
                    className="flex-1 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveMetric}
                    className={`flex-1 py-2 ${accentGradient} ${accentHover} text-white rounded-lg transition-colors`}
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* --- NEW: TABLE MODAL RENDER --- */}
          {showTableModal && (
            <TableModal 
              results={results} 
              onClose={() => setShowTableModal(false)} 
              darkMode={darkMode}
              textClass={textClass}
              textMutedClass={textMutedClass}
              cardClass={cardClass}
              headerClass={tableHeaderClass}
              cellClass={tableCellClass}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;