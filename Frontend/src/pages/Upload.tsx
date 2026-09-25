import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Upload as UploadIcon, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

type UploadState = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

export const Upload: React.FC = () => {
  const { session } = useAuth();
  const [state, setState] = useState<UploadState>('idle');
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [uploadedDoc, setUploadedDoc] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file) return;

    if (file.size > 20 * 1024 * 1024) {
      setState('error');
      setErrorMsg('File exceeds the maximum limit of 20MB.');
      return;
    }
    if (!['application/pdf', 'text/plain'].includes(file.type)) {
      setState('error');
      setErrorMsg('Unsupported file type. Please upload a PDF or TXT file.');
      return;
    }

    setState('uploading');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8000/api/documents/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: formData,
      });

      if (!response.ok) {
        let msg = 'Failed to upload document.';
        try {
           const errData = await response.json();
           msg = errData.detail || msg;
        } catch(e) {}
        throw new Error(msg);
      }

      const data = await response.json();
      setUploadedDoc(data.document);
      
      if (data.document.status === 'processing') {
        setState('processing');
      } else if (data.document.status === 'completed') {
        setState('success');
      } else {
        setState('error');
        setErrorMsg('Document failed processing immediately.');
      }

    } catch (error: any) {
      setState('error');
      setErrorMsg(error.message || 'An unexpected error occurred.');
    }
  };

  useEffect(() => {
    if (state !== 'processing' || !uploadedDoc || !session) return;

    const pollStatus = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/documents/${uploadedDoc.id}/status`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`
          }
        });
        
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'completed') {
            setState('success');
          } else if (data.status === 'failed') {
            setState('error');
            setErrorMsg(data.error_message || 'Document processing failed.');
          }
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    };

    const intervalId = setInterval(pollStatus, 2000);
    return () => clearInterval(intervalId);
  }, [state, uploadedDoc, session]);

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (state === 'uploading' || state === 'processing') return;
    const droppedFile = e.dataTransfer.files[0];
    handleFile(droppedFile);
  }, [state, session]);

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleReset = () => {
    setState('idle');
    setErrorMsg('');
    setUploadedDoc(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full p-6 bg-slate-50 relative">
      <div className="max-w-xl w-full">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-800">Upload a Document</h2>
          <p className="text-slate-500 mt-2">Upload a PDF or TXT file up to 20MB to get started.</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          
          {state === 'idle' && (
            <div 
              onDrop={onDrop}
              onDragOver={onDragOver}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 rounded-xl p-12 flex flex-col items-center justify-center text-center hover:border-purple-500 hover:bg-purple-50 transition-colors cursor-pointer group"
            >
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-purple-100 transition-colors">
                 <UploadIcon className="w-8 h-8 text-slate-400 group-hover:text-purple-600 transition-colors" />
              </div>
              <p className="text-slate-700 font-medium text-lg">Click or drag file to this area to upload</p>
              <p className="text-slate-400 mt-1 text-sm">Supports PDF and TXT (Max 20MB)</p>
              <input 
                type="file" 
                className="hidden" 
                ref={fileInputRef}
                accept="application/pdf, text/plain"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFile(e.target.files[0]);
                  }
                }}
              />
            </div>
          )}

          {(state === 'uploading' || state === 'processing') && (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-12 h-12 text-purple-600 animate-spin mb-4" />
              <h3 className="text-lg font-medium text-slate-800">
                {state === 'uploading' ? 'Uploading your document...' : 'Extracting and analyzing text...'}
              </h3>
              <p className="text-slate-500 mt-2 text-sm max-w-xs">
                {state === 'uploading' 
                  ? 'Please wait while we securely store your file.' 
                  : 'Preparing chunks and generating embeddings. This may take a moment.'}
              </p>
            </div>
          )}

          {state === 'success' && (
            <div className="py-8 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                 <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-medium text-slate-800">Document ready!</h3>
              
              <div className="mt-6 flex items-center gap-3 bg-slate-50 px-4 py-3 rounded-lg border border-slate-200 w-full max-w-sm justify-center">
                 <FileText className="w-5 h-5 text-purple-600" />
                 <span className="text-slate-700 font-medium truncate">{uploadedDoc?.name}</span>
              </div>

              <div className="mt-8 flex gap-4 w-full justify-center">
                <button onClick={handleReset} className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 font-medium hover:bg-slate-50 transition-colors">
                  Upload Another
                </button>
                <button className="px-4 py-2 bg-purple-600 rounded-lg text-white font-medium hover:bg-purple-700 transition-colors shadow-sm">
                  Start Chat
                </button>
              </div>
            </div>
          )}

          {state === 'error' && (
            <div className="py-8 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                 <AlertCircle className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="text-lg font-medium text-slate-800">Process Failed</h3>
              <p className="text-red-600 mt-2 max-w-sm">{errorMsg}</p>
              
              <div className="mt-8">
                <button onClick={handleReset} className="px-6 py-2 bg-slate-800 rounded-lg text-white font-medium hover:bg-slate-900 transition-colors shadow-sm">
                  Try Again
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
