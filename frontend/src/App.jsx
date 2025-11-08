import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Database, CheckCircle, AlertCircle, Loader, TrendingUp, BarChart3, DollarSign, Sun, Moon, Terminal, Activity, Eye, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState('');
  const [stageDetails, setStageDetails] = useState('');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
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
    addLog(`Selected ${selectedFiles.length} file(s): ${selectedFiles.map(f => f.name).join(', ')}`, 'info');
  };

  const uploadFiles = async () => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    addLog('📤 Uploading files to backend...', 'info');
    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${errorText}`);
    }
    
    const result = await response.json();
    addLog(`✅ Files uploaded successfully: ${result.files.length} files`, 'success');
    return result;
  };

  const processDocuments = async (filePaths) => {
    addLog('🔄 Sending files for processing...', 'info');
    
    const response = await fetch(`${API_BASE}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_paths: filePaths }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Processing failed: ${errorText}`);
    }
    
    const result = await response.json();
    addLog('✅ Processing complete!', 'success');
    return result;
  };

  const handleProcess = async () => {
    if (files.length === 0) {
      setError('Please select at least one file');
      addLog('❌ No files selected', 'error');
      return;
    }

    setProcessing(true);
    setError('');
    setResults(null);
    setProgress(0);
    setLogs([]);

    try {
      // Stage 1: Upload
      setCurrentStage('Uploading Documents');
      setStageDetails('Transferring files to server...');
      setProgress(10);
      const uploadResult = await uploadFiles();
      setProgress(20);

      // Stage 2: Extract with LandingAI
      setCurrentStage('Extracting Data');
      setStageDetails('LandingAI is analyzing document structure and extracting fields...');
      addLog('🔍 LandingAI extracting financial data...', 'info');
      setProgress(30);

      // Stage 3: Process with backend
      const processResult = await processDocuments(uploadResult.files);
      
      setProgress(50);
      setCurrentStage('Analyzing Data');
      setStageDetails('Gemini AI is analyzing extracted data and detecting relationships...');
      addLog('🤖 Gemini analyzing financial data...', 'info');
      setProgress(60);

      setCurrentStage('Designing Schema');
      setStageDetails('Gemini AI is designing optimal database schema...');
      addLog('🏗️ Designing database schema...', 'info');
      setProgress(75);

      setCurrentStage('Deploying to Snowflake');
      setStageDetails('Creating tables and loading data to Snowflake...');
      addLog('❄️ Deploying to Snowflake...', 'info');
      setProgress(90);

      setResults(processResult);
      setProgress(100);
      setCurrentStage('Complete');
      setStageDetails('All data successfully processed and deployed!');
      
      addLog(`✅ SUCCESS: ${processResult.extraction_results?.length || 0} documents processed`, 'success');
      addLog(`✅ Created ${processResult.schema?.tables?.length || 0} tables in Snowflake`, 'success');
      addLog(`✅ Loaded ${processResult.deployment?.rows_loaded || 0} rows`, 'success');

    } catch (err) {
      setError(err.message);
      setCurrentStage('Error');
      setStageDetails('');
      setProgress(0);
      addLog(`❌ ERROR: ${err.message}`, 'error');
    } finally {
      setProcessing(false);
    }
  };

  const resetForm = () => {
    setFiles([]);
    setResults(null);
    setError('');
    setCurrentStage('');
    setStageDetails('');
    setProgress(0);
    addLog('🔄 Form reset, ready for new documents', 'info');
    if (fileInputRef.current) fileInputRef.current.value = '';
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
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <Terminal className="w-6 h-6 text-blue-400" />
                <h2 className={`text-2xl font-bold ${textClass}`}>System Logs</h2>
              </div>
              <button onClick={() => setShowLogs(false)} className="p-2 hover:bg-gray-700 rounded-lg">
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
                    'text-gray-400'
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
            AI-powered extraction, analysis, and deployment pipeline
          </p>
        </div>

        {/* Upload Section */}
        {!results && (
          <div className={`${cardClass} rounded-2xl shadow-2xl p-8 mb-8`}>
            <div className="text-center mb-8">
              <Upload className={`w-16 h-16 ${darkMode ? 'text-blue-400' : 'text-blue-600'} mx-auto mb-4`} />
              <h3 className={`text-2xl font-semibold ${textClass} mb-2`}>Upload Financial Documents</h3>
              <p className={textMutedClass}>Balance sheets, income statements, cash flow statements (PDF, PNG, JPG)</p>
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
                <h4 className={`${textClass} font-semibold mb-3`}>Selected Files ({files.length}):</h4>
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
              onClick={handleProcess}
              disabled={files.length === 0 || processing}
              className="w-full py-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
            >
              {processing ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Database className="w-5 h-5" />
                  <span>Start Processing</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Processing Stage Indicator */}
        {processing && (
          <div className={`${cardClass} rounded-2xl shadow-2xl p-8 mb-8`}>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className={`text-2xl font-bold ${textClass} mb-2`}>{currentStage}</h3>
                  <p className={textMutedClass}>{stageDetails}</p>
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

              {/* Stage Checkpoints */}
              <div className="grid grid-cols-5 gap-2 mt-6">
                {[
                  { name: 'Upload', progress: 20 },
                  { name: 'Extract', progress: 40 },
                  { name: 'Analyze', progress: 60 },
                  { name: 'Schema', progress: 80 },
                  { name: 'Deploy', progress: 100 }
                ].map((stage, idx) => (
                  <div key={idx} className="text-center">
                    <div className={`w-full h-2 rounded-full ${
                      progress >= stage.progress 
                        ? 'bg-green-500' 
                        : darkMode ? 'bg-gray-700' : 'bg-gray-300'
                    }`} />
                    <p className={`text-xs mt-2 ${
                      progress >= stage.progress ? 'text-green-400 font-bold' : textMutedClass
                    }`}>
                      {stage.name}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-6">
            <div className="bg-green-500 bg-opacity-20 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-green-500 border-opacity-30">
              <div className="flex items-center gap-4">
                <CheckCircle className="w-12 h-12 text-green-400" />
                <div>
                  <h3 className="text-2xl font-bold text-white mb-1">Processing Complete!</h3>
                  <p className="text-green-200">Successfully processed and deployed to Snowflake</p>
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-2">
                  <FileText className="w-8 h-8 text-white opacity-80" />
                  <span className="text-3xl font-bold text-white">{results.extraction_results?.length || 0}</span>
                </div>
                <p className="text-blue-100 font-semibold">Documents Processed</p>
              </div>

              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-2">
                  <Database className="w-8 h-8 text-white opacity-80" />
                  <span className="text-3xl font-bold text-white">{results.schema?.tables?.length || 0}</span>
                </div>
                <p className="text-purple-100 font-semibold">Tables Created</p>
              </div>

              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-2">
                  <BarChart3 className="w-8 h-8 text-white opacity-80" />
                  <span className="text-3xl font-bold text-white">{results.deployment?.rows_loaded || 0}</span>
                </div>
                <p className="text-green-100 font-semibold">Rows Loaded</p>
              </div>
            </div>

            {results.extraction_results && results.extraction_results.length > 0 && (
              <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
                <h3 className={`text-2xl font-bold ${textClass} mb-6 flex items-center gap-3`}>
                  <DollarSign className="w-7 h-7 text-green-400" />
                  Extracted Financial Data
                </h3>
                {results.extraction_results.map((result, idx) => (
                  <div key={idx} className="mb-6">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="px-4 py-2 bg-purple-500 bg-opacity-30 text-purple-200 rounded-lg font-semibold">
                        {result.document_type?.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className={textMutedClass}>{result.period}</span>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {result.extracted_fields?.slice(0, 6).map((field, fidx) => (
                        <div key={fidx} className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-lg`}>
                          <p className={`${textMutedClass} text-sm mb-1`}>{field.field_name}</p>
                          <p className={`text-2xl font-bold ${textClass}`}>${field.value?.toLocaleString()}</p>
                          <p className="text-xs text-green-400 mt-1">{(field.confidence * 100).toFixed(1)}% confidence</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {results.schema && (
              <div className={`${cardClass} rounded-2xl shadow-2xl p-8`}>
                <h3 className={`text-2xl font-bold ${textClass} mb-6 flex items-center gap-3`}>
                  <Database className="w-7 h-7 text-blue-400" />
                  Generated Database Schema
                </h3>
                <div className="space-y-4 mb-6">
                  {results.schema.tables?.map((table, idx) => (
                    <div key={idx} className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-lg`}>
                      <h4 className={`text-lg font-bold ${textClass} mb-3`}>{table.table_name}</h4>
                      <div className="space-y-2">
                        {table.columns?.slice(0, 5).map((col, cidx) => (
                          <div key={cidx} className="flex items-center gap-3 text-sm">
                            <span className="text-purple-400 font-mono">{col.name}</span>
                            <span className={textMutedClass}>{col.type}</span>
                            {col.constraints && <span className="text-blue-400 text-xs">{col.constraints}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                
                {results.schema.ddl_sql && (
                  <div className={`${darkMode ? 'bg-gray-950' : 'bg-gray-900'} rounded-lg p-4 overflow-x-auto`}>
                    <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap">
                      {results.schema.ddl_sql.substring(0, 500)}
                      {results.schema.ddl_sql.length > 500 && '...'}
                    </pre>
                  </div>
                )}
              </div>
            )}

            <button
              onClick={resetForm}
              className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold rounded-xl transition-all shadow-lg"
            >
              Process More Documents
            </button>
          </div>
        )}
      </main>

      <footer className={`${darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} bg-opacity-50 backdrop-blur-md border-t mt-20`}>
        <div className="max-w-7xl mx-auto px-6 py-8 text-center">
          <p className={textMutedClass}>
            Powered by <span className="text-blue-400 font-semibold">LandingAI</span> + <span className="text-purple-400 font-semibold">Gemini</span> + <span className="text-cyan-400 font-semibold">Snowflake</span>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;