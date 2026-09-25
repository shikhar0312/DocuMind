import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import { LogOut, Search, Plus, FileText, Settings, User as UserIcon } from 'lucide-react'

export const Workspace: React.FC = () => {
  const { user, signOut } = useAuth()

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <div className="w-64 bg-slate-50 border-r border-slate-200 flex flex-col">
        <div className="p-4 flex items-center gap-2">
          <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-slate-900">DocuMind</span>
        </div>
        
        <div className="px-3 py-2">
          <button className="w-full flex items-center justify-between px-3 py-2 bg-white border border-slate-200 rounded-md shadow-sm text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              New Chat
            </span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 mt-4 px-2">
            Recent Chats
          </div>
          <div className="space-y-1">
            {/* Placeholder for chats */}
            <button className="w-full flex items-center gap-2 px-2 py-2 text-sm text-slate-700 rounded-md hover:bg-slate-100 bg-slate-100 font-medium">
              <FileText className="w-4 h-4 text-purple-600" />
              <span className="truncate">Quarterly Report Analysis</span>
            </button>
            <button className="w-full flex items-center gap-2 px-2 py-2 text-sm text-slate-600 rounded-md hover:bg-slate-100">
              <FileText className="w-4 h-4" />
              <span className="truncate">Employee Handbook</span>
            </button>
          </div>
        </div>

        <div className="p-4 border-t border-slate-200 space-y-1">
          <button className="w-full flex items-center gap-2 px-2 py-2 text-sm text-slate-600 rounded-md hover:bg-slate-100">
            <Settings className="w-4 h-4" />
            Settings
          </button>
          <div className="flex items-center justify-between px-2 py-2 mt-2">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                <UserIcon className="w-3 h-3 text-purple-600" />
              </div>
              <span className="text-sm font-medium text-slate-700 truncate">
                {user?.email}
              </span>
            </div>
            <button onClick={signOut} className="text-slate-400 hover:text-slate-600" title="Log out">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full bg-white relative">
        <header className="h-14 border-b border-slate-200 flex items-center px-6 bg-white">
          <h1 className="text-lg font-medium text-slate-800">Quarterly Report Analysis</h1>
        </header>
        
        <main className="flex-1 overflow-y-auto p-6 flex flex-col items-center">
          <div className="max-w-3xl w-full flex-1 flex flex-col justify-center items-center text-center space-y-4">
             <div className="w-16 h-16 bg-purple-50 rounded-full flex items-center justify-center">
                <Search className="w-8 h-8 text-purple-600" />
             </div>
             <h2 className="text-2xl font-semibold text-slate-800">How can I help you today?</h2>
             <p className="text-slate-500 max-w-md">Ask questions about your uploaded documents, and I'll find the answers grounded in your files.</p>
          </div>
        </main>

        <div className="p-4 bg-white border-t border-slate-100">
          <div className="max-w-3xl mx-auto relative">
            <div className="overflow-hidden rounded-xl border border-slate-300 shadow-sm bg-white focus-within:ring-1 focus-within:ring-purple-500 focus-within:border-purple-500 transition-shadow">
              <textarea
                rows={1}
                name="message"
                id="message"
                className="block w-full resize-none border-0 py-3 text-slate-900 placeholder:text-slate-400 focus:ring-0 sm:text-sm sm:leading-6 px-4 bg-transparent outline-none"
                placeholder="Ask a question about this document..."
                defaultValue={""}
              />
              <div className="py-2 px-3 flex justify-between items-center bg-slate-50 border-t border-slate-100">
                <div className="flex gap-2">
                   <button className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200 transition-colors">
                     <FileText className="w-3.5 h-3.5" />
                     Document.pdf
                   </button>
                </div>
                <button
                  type="submit"
                  className="inline-flex items-center rounded-md bg-purple-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600 transition-colors"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
          <div className="text-center mt-3">
             <span className="text-xs text-slate-400">AI can make mistakes. Check your source documents.</span>
          </div>
        </div>
      </div>
    </div>
  )
}
