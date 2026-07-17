"use client";

import { useState } from "react";

export default function Home() {
  // Active Tab
  const [activeTab, setActiveTab] = useState("dashboard"); // 'dashboard' | 'explorer'
  
  // Input fields
  const [company, setCompany] = useState("Apple");
  const [quarter, setQuarter] = useState("Q3-2024");
  const [pdfFile, setPdfFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [transcriptFile, setTranscriptFile] = useState(null);
  
  // Status states
  const [uploadStatus, setUploadStatus] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestionResult, setIngestionResult] = useState(null);
  const [backendError, setBackendError] = useState(null);

  // RAG Query states
  const [query, setQuery] = useState("Did the CEO's spoken remarks about debt match the written risk factors?");
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryResponse, setQueryResponse] = useState(null);

  // Base API URL
  const API_URL = "http://localhost:8088";

  const handleFileUpload = async (file, type) => {
    if (!file) return null;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("file_type", type);
    formData.append("company", company);
    formData.append("quarter", quarter);

    const res = await fetch(`${API_URL}/api/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw new Error(`Failed to upload ${type} file`);
    }
    return await res.json();
  };

  const triggerIngest = async () => {
    setUploadStatus("");
    setIsUploading(true);
    setIngestionResult(null);
    setBackendError(null);

    try {
      // Validation: Must select at least one file to upload
      if (!pdfFile && !audioFile && !transcriptFile) {
        throw new Error("Please select a PDF filing or transcript file to upload first.");
      }

      setUploadStatus("Uploading files to server...");
      
      // Upload files
      if (pdfFile) await handleFileUpload(pdfFile, "pdf");
      if (audioFile) await handleFileUpload(audioFile, "audio");
      if (transcriptFile) await handleFileUpload(transcriptFile, "transcript");

      setUploadStatus("Files uploaded. Initializing semantic chunking & database ingestion...");
      setIsIngesting(true);

      const formData = new FormData();
      formData.append("company", company);
      formData.append("quarter", quarter);

      const res = await fetch(`${API_URL}/api/ingest`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Backend ingestion process failed");
      }

      const data = await res.json();
      setIngestionResult(data);
      setUploadStatus("Ingestion completed successfully!");
    } catch (err) {
      setBackendError(err.message || "Failed to communicate with local FastAPI backend.");
    } finally {
      setIsUploading(false);
      setIsIngesting(false);
    }
  };

  const runAnalysis = async () => {
    setIsQuerying(true);
    setQueryResponse(null);
    setBackendError(null);

    try {
      const res = await fetch(`${API_URL}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company, quarter, query }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to retrieve analysis from backend");
      }

      const data = await res.json();
      setQueryResponse(data);
    } catch (err) {
      setBackendError(err.message || "Failed to fetch comparative analysis.");
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-[#09090b]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <span className="font-bold text-lg text-white">M</span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              Multimodal Earnings Analyzer
            </h1>
            <p className="text-xs text-zinc-400">SEC Filings vs CEO Audio Calls</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-xs font-semibold px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Gemini 2.5 Flash Online
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Side: Setup & Files */}
        <section className="lg:col-span-4 flex flex-col gap-6">
          
          {/* Company Context Card */}
          <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-sm flex flex-col gap-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">1. Target Parameters</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1.5 font-medium">Company Name</label>
                <input
                  id="company-name"
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1.5 font-medium">Fiscal Period</label>
                <input
                  id="fiscal-period"
                  type="text"
                  value={quarter}
                  onChange={(e) => setQuarter(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Ingestion & Ingestion Status */}
          <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-sm flex flex-col gap-4 flex-1">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">2. Ingest Multi-Modal Sources</h2>
            
            {/* File upload fields */}
            <div className="flex flex-col gap-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1 font-medium">Written Filing (PDF)</label>
                <input
                  id="pdf-upload"
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setPdfFile(e.target.files[0])}
                  className="text-xs text-zinc-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-white hover:file:bg-zinc-700 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1 font-medium">Earnings Call Audio (MP3/WAV)</label>
                <input
                  id="audio-upload"
                  type="file"
                  accept="audio/*"
                  onChange={(e) => setAudioFile(e.target.files[0])}
                  className="text-xs text-zinc-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-white hover:file:bg-zinc-700 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1 font-medium">Or Transcript File (JSON/TXT - Optional)</label>
                <input
                  id="transcript-upload"
                  type="file"
                  accept=".json,.txt"
                  onChange={(e) => setTranscriptFile(e.target.files[0])}
                  className="text-xs text-zinc-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-white hover:file:bg-zinc-700 cursor-pointer"
                />
              </div>
            </div>

            <button
              id="ingest-button"
              disabled={isUploading || isIngesting}
              onClick={triggerIngest}
              className="mt-2 w-full bg-gradient-to-r from-violet-600 to-indigo-500 hover:from-violet-500 hover:to-indigo-400 text-white font-semibold py-2.5 rounded-xl text-sm transition-all shadow-md shadow-indigo-600/10 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isUploading || isIngesting ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  <span>Processing...</span>
                </>
              ) : (
                "Ingest & Analyze Core"
              )}
            </button>

            {uploadStatus && (
              <p className="text-xs text-indigo-400 mt-2 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                {uploadStatus}
              </p>
            )}

            {backendError && (
              <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl p-3 mt-2">
                <strong>Error:</strong> {backendError}
                <div className="mt-1 font-mono text-[10px]">Verify backend server is running at port 8088.</div>
              </div>
            )}

            {ingestionResult && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl p-3 flex flex-col gap-1.5 mt-2">
                <p className="text-xs font-semibold">Ingestion completed successfully!</p>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-zinc-300">
                  <span className="bg-zinc-950/40 p-1.5 rounded-md">📄 {ingestionResult.pdf_chunks} PDF Chunks</span>
                  <span className="bg-zinc-950/40 p-1.5 rounded-md">🔊 {ingestionResult.audio_chunks} Audio Segments</span>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Right Side: RAG Workspace & Citations */}
        <section className="lg:col-span-8 flex flex-col gap-6">
          
          {/* Navigation Tabs */}
          <div className="flex gap-2 p-1.5 bg-zinc-900/40 border border-zinc-800/80 rounded-xl self-start">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "dashboard" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Comparative Query Panel
            </button>
            <button
              onClick={() => setActiveTab("explorer")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "explorer" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Analysis Templates
            </button>
          </div>

          {/* TAB 1: Comparative Query Panel */}
          {activeTab === "dashboard" && (
            <div className="flex flex-col gap-6 flex-1">
              
              {/* Question Bar */}
              <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-sm flex flex-col gap-3">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">Ask the Cross-Analysis Engine</h2>
                <div className="flex gap-3">
                  <input
                    id="query-input"
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Compare CEO remarks with financial records..."
                    className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    id="query-button"
                    disabled={isQuerying}
                    onClick={runAnalysis}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isQuerying ? "Analyzing..." : "Compare"}
                  </button>
                </div>
              </div>

              {/* Response Workspace */}
              {isQuerying && (
                <div className="bg-zinc-900/20 border border-zinc-800/40 rounded-2xl p-10 flex flex-col items-center justify-center gap-4 flex-1">
                  <svg className="animate-spin h-8 w-8 text-indigo-500" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  <p className="text-sm text-zinc-400">Retrieving filing pages and audio segments, running cross-analysis with Gemini...</p>
                </div>
              )}

              {queryResponse && (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 flex-1">
                  
                  {/* Left Column: Forensic Report */}
                  <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 flex flex-col gap-4">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400">Gemini Comparative Report</h3>
                    <div className="text-sm text-zinc-300 leading-relaxed overflow-y-auto max-h-[500px] pr-2 space-y-4 font-sans whitespace-pre-wrap">
                      {queryResponse.response}
                    </div>
                  </div>

                  {/* Right Column: Citations */}
                  <div className="flex flex-col gap-4">
                    
                    {/* PDF Citations */}
                    <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 flex-1 flex flex-col gap-3">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                        📄 Retrieved Written Filing Context
                      </h3>
                      <div className="overflow-y-auto max-h-[220px] flex flex-col gap-3 pr-2">
                        {queryResponse.pdf_context && queryResponse.pdf_context.length > 0 ? (
                          queryResponse.pdf_context.map((ctx, idx) => (
                            <div key={idx} className="bg-zinc-950/60 border border-zinc-800 p-3.5 rounded-xl flex flex-col gap-2">
                              <span className="text-[10px] font-bold text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded-full self-start">
                                Page {ctx.meta?.page_number || "N/A"}
                              </span>
                              <p className="text-xs text-zinc-300 leading-relaxed italic">"{ctx.text}"</p>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-zinc-500">No written context was retrieved.</p>
                        )}
                      </div>
                    </div>

                    {/* Audio Citations */}
                    <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 flex-1 flex flex-col gap-3">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                        🔊 Retrieved Audio Transcript Context
                      </h3>
                      <div className="overflow-y-auto max-h-[220px] flex flex-col gap-3 pr-2">
                        {queryResponse.audio_context && queryResponse.audio_context.length > 0 ? (
                          queryResponse.audio_context.map((ctx, idx) => (
                            <div key={idx} className="bg-zinc-950/60 border border-zinc-800 p-3.5 rounded-xl flex flex-col gap-2">
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                                  {ctx.meta?.start_time_seconds ? `${ctx.meta.start_time_seconds.toFixed(1)}s` : "0s"} - {ctx.meta?.end_time_seconds ? `${ctx.meta.end_time_seconds.toFixed(1)}s` : "0s"}
                                </span>
                                <span className="text-[10px] font-bold text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded-full">
                                  {ctx.meta?.speaker || "Speaker"}
                                </span>
                              </div>
                              <p className="text-xs text-zinc-300 leading-relaxed italic">"{ctx.text}"</p>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-zinc-500">No audio transcript context was retrieved.</p>
                        )}
                      </div>
                    </div>

                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Analysis Templates */}
          {activeTab === "explorer" && (
            <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-sm flex flex-col gap-6">
              <div>
                <h2 className="text-base font-bold text-white">Discrepancy Audit Queries</h2>
                <p className="text-xs text-zinc-400 mt-1">Select a comparison query to autofill the workspace.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Card 1 */}
                <div
                  onClick={() => {
                    setQuery("Did the CEO's spoken remarks about debt match the written risk factors?");
                    setActiveTab("dashboard");
                  }}
                  className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl cursor-pointer hover:border-violet-500/40 transition-all flex flex-col gap-2 hover:shadow-lg hover:shadow-violet-500/5 group"
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-0.5 rounded-full">
                      Debt & Liquidity
                    </span>
                    <span className="text-[11px] text-zinc-400 group-hover:text-indigo-400 transition-colors">Select &rarr;</span>
                  </div>
                  <h3 className="text-sm font-bold text-white mt-1">Written Defaults vs. Spoken Confidence</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Compare written warnings about debt maturity constraints with the CEO's spoken reassurance of zero default risk.
                  </p>
                </div>

                {/* Card 2 */}
                <div
                  onClick={() => {
                    setQuery("Did the CEO sound confident about revenue growth and margins?");
                    setActiveTab("dashboard");
                  }}
                  className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl cursor-pointer hover:border-violet-500/40 transition-all flex flex-col gap-2 hover:shadow-lg hover:shadow-violet-500/5 group"
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 rounded-full">
                      Revenue & Margins
                    </span>
                    <span className="text-[11px] text-zinc-400 group-hover:text-indigo-400 transition-colors">Select &rarr;</span>
                  </div>
                  <h3 className="text-sm font-bold text-white mt-1">Margin Expansion vs. Margin Contraction</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Audit spoken claims of 28% margins and optimized operating costs against reported margin contractions due to supply chain inflation.
                  </p>
                </div>

              </div>
            </div>
          )}

        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800 mt-auto py-4 text-center text-xs text-zinc-500">
        © 2026 Multimodal Earnings Analyzer. Built with Next.js, FastAPI, ChromaDB and Gemini.
      </footer>
    </div>
  );
}
