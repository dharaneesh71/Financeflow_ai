import React, { useState, useRef, useEffect } from 'react';
import { 
  Upload, FileText, Database, CheckCircle, AlertCircle, 
  Loader, TrendingUp, BarChart3, Sun, Moon, Terminal, 
  Activity, X, Sparkles, Search, Edit, Trash2, Plus, 
  ArrowRight, ArrowLeft
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [step, setStep] = useState(1); // 1: upload, 2: suggest, 3: review, 4: process, 5: results
  
  // File and processing state
  const [files, setFiles] = useState([]);
  const [uploadedFilePaths, setUploadedFilePaths] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  
  // Metric extraction state
  const [userPrompt, setUserPrompt] = useState('');
  const [suggestedMetrics, setSuggestedMetrics] = useState([]);
  const [selectedMetrics, setSelectedMetrics] = useState([]);
  const [editingMetric, setEditingMetric] = useState(null);
  
  // Results
  const [results, setResults] = useState(null);
  const [currentStage, setCurrentStage] = useState('');
  const [progress, setProgress] = useState(0);
  
  // UI state
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const fileInputRef = useRef(null);
  const logsEndRef = useRef(null);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setError('');
    setResults(null);
    setStep(1);
    addLog(`📁 Selected ${selectedFiles.length} file(s): ${selectedFiles.map(f => f.name).join(', ')}`, 'info');
  };

  const uploadFiles = async () => {
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
    if (files.length === 0) {
      setError('Please select at least one file');
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

  const handleStep2 = async () => {
    if (uploadedFilePaths.length === 0) {
      setError('Please upload files first');
      return;
    }

    try {
      setProcessing(true);
      setError('');
      addLog('💡 Requesting metric suggestions...', 'info');
      
      // Call process endpoint with user prompt to get suggestions
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
      addLog(`❌ Error: ${err.message}`, 'error');
    } finally {
      setProcessing(false);
    }
  };

  const handleStep3 = async () => {
    if (selectedMetrics.length === 0) {
      setError('Please select at least one metric to extract');
      return;
    }

    try {
      setProcessing(true);
      setError('');
      setCurrentStage('Processing Pipeline');
      setProgress(0);
      addLog('🔄 Starting processing pipeline...', 'info');
      
      // Step 1: Extract markdown (already done, but we need markdown paths)
      setCurrentStage('Step 1: Extracting Markdown');
      setProgress(10);
      addLog('📄 Extracting markdown...', 'info');
      
      // Step 2: Metrics already suggested
      setCurrentStage('Step 2: Metrics Suggested');
      setProgress(20);
      
      // Step 3: Review complete (user selected metrics)
      setCurrentStage('Step 3: Review Complete');
      setProgress(30);
      
      // Step 4: Extract metrics and create schema
      setCurrentStage('Step 4: Extracting Metrics');
      setProgress(40);
      addLog('🔍 Extracting metrics...', 'info');
      
      // Step 5: Deploy to Snowflake
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
      
      addLog('✅ Processing complete!', 'success');
      addLog(`✅ Created ${result.schema?.tables?.length || 0} tables`, 'success');
      addLog(`✅ Loaded ${result.deployment?.rows_loaded || 0} rows`, 'success');
      
    } catch (err) {
      setError(err.message);
      setCurrentStage('Error');
      setProgress(0);
      addLog(`❌ Error: ${err.message}`, 'error');
    } finally {
      setProcessing(false);
    }
  };

  const resetForm = () => {
    setFiles([]);
    setUploadedFilePaths([]);
    setResults(null);
    setError('');
    setCurrentStage('');
    setProgress(0);
    setStep(1);
    setUserPrompt('');
    setSuggestedMetrics([]);
    setSelectedMetrics([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
    addLog('🔄 Ready for new documents', 'info');
  };

  const addMetric = () => {
    setEditingMetric({
      name: '',
      type: 'str',
      description: ''
    });
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

  const toggleMetricSelection = (index) => {
    const metric = suggestedMetrics[index];
    const isSelected = selectedMetrics.some(m => m.name === metric.name);
    if (isSelected) {
      setSelectedMetrics(prev => prev.filter(m => m.name !== metric.name));
    } else {
      setSelectedMetrics(prev => [...prev, metric]);
    }
  };

  const bgClass = darkMode 
    ? 'bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900' 
    : 'bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50';
  
  const cardClass = darkMode
    ? 'bg-gray-800 bg-opacity-50 backdrop-blur-lg border border-gray-700'
    : 'bg-white bg-opacity-70 backdrop-blur-lg border border-gray-200';
  
  const textClass = darkMode ? 'text-white' : 'text-gray-900';
  const textMutedClass = darkMode ? 'text-gray-300' : 'text-gray-600';

  return (
    <div className={`min-h-screen ${bgClass} transition-colors duration-300`}>
      {/* Header */}
      <header className={`${darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} bg-opacity-50 backdrop-blur-md border-b`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-xl">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className={`text-2xl font-bold ${textClass}`}>FinanceFlow AI</h1>
                <p className={`text-sm ${textMutedClass}`}>LandingAI + Gemini + Snowflake</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowLogs(!showLogs)}
                className={`px-4 py-2 ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} rounded-lg flex items-center gap-2 transition-colors`}
              >
                <Terminal className="w-4 h-4" />
                <span className="text-sm font-medium">Logs</span>
                {logs.length > 0 && (
                  <span className="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">{logs.length}</span>
                )}
              </button>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} rounded-lg transition-colors`}
              >
                {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-blue-600" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Logs Panel */}
      {showLogs && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className={`${darkMode ? 'bg-gray-900' : 'bg-white'} rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] flex flex-col`}>
            <div className={`flex items-center justify-between p-6 border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
              <div className="flex items-center gap-3">
                <Terminal className="w-6 h-6 text-blue-400" />
                <h2 className={`text-2xl font-bold ${textClass}`}>System Logs</h2>
              </div>
              <button 
                onClick={() => setShowLogs(false)} 
                className={`p-2 hover:bg-gray-700 rounded-lg transition-colors ${textClass}`}
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className={`flex-1 overflow-y-auto p-6 ${darkMode ? 'bg-gray-950' : 'bg-gray-50'} font-mono text-sm`}>
              {logs.length === 0 ? (
                <p className="text-gray-500">No logs yet...</p>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className={`mb-2 ${
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'success' ? 'text-green-400' :
                    darkMode ? 'text-gray-400' : 'text-gray-700'
                  }`}>
                    <span className="text-gray-600">[{log.timestamp}]</span> {log.message}
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className={`text-5xl font-bold ${textClass} mb-4`}>
            Financial Document Intelligence
          </h2>
          <p className={`text-xl ${textMutedClass} max-w-3xl mx-auto`}>
            AI-powered extraction, metric suggestion, and Snowflake deployment
          </p>
        </div>

        {/* Step Indicator */}
        <div className={`${cardClass} rounded-2xl shadow-xl p-6 mb-8`}>
          <div className="flex items-center justify-between">
            {[1, 2, 3, 4, 5].map((s) => (
              <React.Fragment key={s}>
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg transition-all ${
                      step >= s
                        ? 'bg-blue-600 text-white'
                        : `${darkMode ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-500'}`
                    }`}
                  >
                    {step > s ? <CheckCircle className="w-6 h-6" /> : s}
                  </div>
                  <p className={`mt-2 text-sm font-medium ${
                    step >= s ? textClass : textMutedClass
                  }`}>
                    {s === 1 && 'Upload'}
                    {s === 2 && 'Suggest'}
                    {s === 3 && 'Review'}
                    {s === 4 && 'Process'}
                    {s === 5 && 'Results'}
                  </p>
                </div>
                {s < 5 && (
                  <div className={`flex-1 h-1 mx-2 ${
                    step > s
                      ? 'bg-blue-600'
                      : `${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`
                  }`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Step 1: Upload */}
        {step === 1 && (
          <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
            <div className="text-center mb-8">
              <Upload className={`w-16 h-16 ${darkMode ? 'text-blue-400' : 'text-blue-600'} mx-auto mb-4`} />
              <h3 className={`text-2xl font-semibold ${textClass} mb-2`}>Upload Document</h3>
              <p className={textMutedClass}>Upload a financial document to begin processing</p>
            </div>

            <div className="mb-6">
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
                className="flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl cursor-pointer transition-all transform hover:scale-105 shadow-lg"
              >
                <FileText className="w-5 h-5" />
                <span className="font-semibold">Choose Files</span>
              </label>
            </div>

            {files.length > 0 && (
              <div className="mb-6">
                <div className="space-y-2">
                  {files.map((file, idx) => (
                    <div key={idx} className={`flex items-center gap-3 ${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-3 rounded-lg`}>
                      <FileText className={`w-5 h-5 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
                      <span className={`${textClass} flex-1`}>{file.name}</span>
                      <span className={`${textMutedClass} text-sm`}>{(file.size / 1024).toFixed(1)} KB</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="mb-6 flex items-center gap-3 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-300" />
                <p className="text-red-200">{error}</p>
              </div>
            )}

            <button
              onClick={handleStep1}
              disabled={files.length === 0 || processing}
              className="w-full py-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
            >
              {processing ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <ArrowRight className="w-5 h-5" />
                  <span>Upload & Extract Markdown</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Step 2: Suggest Metrics */}
        {step === 2 && (
          <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
            <div className="text-center mb-8">
              <Sparkles className={`w-16 h-16 ${darkMode ? 'text-purple-400' : 'text-purple-600'} mx-auto mb-4`} />
              <h3 className={`text-2xl font-semibold ${textClass} mb-2`}>Suggest Metrics</h3>
              <p className={textMutedClass}>Let AI suggest metrics or provide your own requirements</p>
            </div>

            <div className="mb-6">
              <label className={`block ${textClass} font-medium mb-2`}>
                Optional: Describe what metrics you want to extract
              </label>
              <textarea
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                placeholder="e.g., I want to extract account holder name and number of deposits"
                className={`w-full px-4 py-3 rounded-lg ${darkMode ? 'bg-gray-700 text-white border-gray-600' : 'bg-white text-gray-900 border-gray-300'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
                rows={3}
              />
            </div>

            {error && (
              <div className="mb-6 flex items-center gap-3 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-300" />
                <p className="text-red-200">{error}</p>
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={() => setStep(1)}
                className="flex-1 py-4 bg-gray-600 hover:bg-gray-700 text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back</span>
              </button>
              <button
                onClick={handleStep2}
                disabled={processing}
                className="flex-1 py-4 bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
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
        )}

        {/* Step 3: Review and Select Metrics */}
        {step === 3 && (
          <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className={`text-2xl font-semibold ${textClass} mb-2`}>Review Metrics</h3>
                <p className={textMutedClass}>Select or edit metrics to extract</p>
              </div>
              <button
                onClick={addMetric}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Metric
              </button>
            </div>

            {/* Suggested Metrics */}
            {suggestedMetrics.length > 0 && (
              <div className="mb-6">
                <h4 className={`${textClass} font-semibold mb-3`}>Suggested Metrics:</h4>
                <div className="space-y-2">
                  {suggestedMetrics.map((metric, idx) => {
                    const isSelected = selectedMetrics.some(m => m.name === metric.name);
                    return (
                      <div
                        key={idx}
                        onClick={() => toggleMetricSelection(idx)}
                        className={`flex items-center gap-3 p-4 rounded-lg cursor-pointer transition-all ${
                          isSelected
                            ? `${darkMode ? 'bg-blue-900 border-2 border-blue-500' : 'bg-blue-50 border-2 border-blue-500'}`
                            : `${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'} border-2 border-transparent`
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleMetricSelection(idx)}
                          className="w-5 h-5"
                        />
                        <div className="flex-1">
                          <p className={`font-semibold ${textClass}`}>{metric.name}</p>
                          <p className={`text-sm ${textMutedClass}`}>{metric.description}</p>
                          <span className={`text-xs px-2 py-1 rounded ${darkMode ? 'bg-gray-600' : 'bg-gray-200'} ${textMutedClass}`}>
                            {metric.type}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Selected Metrics */}
            <div className="mb-6">
              <h4 className={`${textClass} font-semibold mb-3`}>
                Selected Metrics ({selectedMetrics.length}):
              </h4>
              <div className="space-y-2">
                {selectedMetrics.map((metric, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 p-4 rounded-lg ${
                      darkMode ? 'bg-gray-700' : 'bg-gray-100'
                    }`}
                  >
                    <div className="flex-1">
                      <p className={`font-semibold ${textClass}`}>{metric.name}</p>
                      <p className={`text-sm ${textMutedClass}`}>{metric.description}</p>
                      <span className={`text-xs px-2 py-1 rounded ${darkMode ? 'bg-gray-600' : 'bg-gray-200'} ${textMutedClass}`}>
                        {metric.type}
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        setEditingMetric({ ...metric, id: idx });
                      }}
                      className="p-2 hover:bg-gray-600 rounded-lg transition-colors"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteMetric(idx)}
                      className="p-2 hover:bg-red-600 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Edit Metric Modal */}
            {editingMetric && (
              <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <div className={`${darkMode ? 'bg-gray-900' : 'bg-white'} rounded-2xl shadow-2xl max-w-md w-full p-6`}>
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
                        className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 text-white border-gray-600' : 'bg-white text-gray-900 border-gray-300'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
                        placeholder="metric_name"
                      />
                    </div>
                    <div>
                      <label className={`block ${textClass} font-medium mb-2`}>Type</label>
                      <select
                        value={editingMetric.type}
                        onChange={(e) => setEditingMetric({ ...editingMetric, type: e.target.value })}
                        className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 text-white border-gray-600' : 'bg-white text-gray-900 border-gray-300'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
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
                        className={`w-full px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 text-white border-gray-600' : 'bg-white text-gray-900 border-gray-300'} border focus:outline-none focus:ring-2 focus:ring-blue-500`}
                        rows={3}
                        placeholder="Description of the metric"
                      />
                    </div>
                  </div>
                  <div className="flex gap-4 mt-6">
                    <button
                      onClick={() => setEditingMetric(null)}
                      className="flex-1 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={saveMetric}
                      className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="mb-6 flex items-center gap-3 p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-300" />
                <p className="text-red-200">{error}</p>
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={() => setStep(2)}
                className="flex-1 py-4 bg-gray-600 hover:bg-gray-700 text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
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
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Database className="w-5 h-5" />
                    <span>Extract & Deploy</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Processing */}
        {step === 4 && processing && (
          <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className={`text-2xl font-bold ${textClass} mb-2`}>{currentStage}</h3>
                  <p className={textMutedClass}>Processing your document...</p>
                </div>
                <Activity className={`w-12 h-12 ${darkMode ? 'text-blue-400' : 'text-blue-600'} animate-pulse`} />
              </div>
              
              <div className={`w-full ${darkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded-full h-4 overflow-hidden`}>
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              
              <div className="text-center">
                <span className={`text-3xl font-bold ${textClass}`}>{progress}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Results */}
        {step === 5 && results && (
          <div className="space-y-6">
            <div className="bg-green-500 bg-opacity-20 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-green-500 border-opacity-30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <CheckCircle className="w-12 h-12 text-green-400" />
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">Processing Complete!</h3>
                    <p className="text-green-200">Metrics extracted and deployed to Snowflake</p>
                  </div>
                </div>
                <button
                  onClick={resetForm}
                  className="px-6 py-3 bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg transition-colors"
                >
                  Process New Document
                </button>
              </div>
            </div>

            {/* Extracted Metrics */}
            {results.extracted_metrics && (
              <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
                <h3 className={`text-2xl font-semibold ${textClass} mb-6`}>Extracted Metrics</h3>
                <div className="space-y-4">
                  {Object.entries(results.extracted_metrics).map(([key, value]) => (
                    <div
                      key={key}
                      className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className={`font-semibold ${textClass} capitalize`}>
                            {key.replace(/_/g, ' ')}
                          </p>
                          <p className={`text-2xl font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
                            {value !== null && value !== undefined ? String(value) : 'N/A'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Deployment Info */}
            <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
              <h3 className={`text-2xl font-semibold ${textClass} mb-6`}>Snowflake Deployment</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-lg`}>
                  <p className={textMutedClass}>Tables Created</p>
                  <p className={`text-3xl font-bold ${textClass}`}>{results.schema?.tables?.length || 0}</p>
                </div>
                <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-lg`}>
                  <p className={textMutedClass}>Rows Loaded</p>
                  <p className={`text-3xl font-bold ${textClass}`}>{results.deployment?.rows_loaded || 0}</p>
                </div>
                <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-lg`}>
                  <p className={textMutedClass}>Status</p>
                  <p className={`text-xl font-bold ${textClass}`}>{results.deployment?.status || 'Unknown'}</p>
                </div>
              </div>
              <div className="space-y-2">
                <p className={textMutedClass}>
                  <span className="font-semibold">Database:</span> {results.deployment?.database}
                </p>
                <p className={textMutedClass}>
                  <span className="font-semibold">Schema:</span> {results.deployment?.schema}
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
