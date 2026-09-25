import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Navigate } from 'react-router-dom'
import { FileText, LogIn } from 'lucide-react'

export const Login: React.FC = () => {
  const { user, signInWithGoogle } = useAuth()

  if (user) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
            <FileText className="w-8 h-8 text-white" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900">
          DocuMind
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600 max-w">
          Unlock answers from your documents. Securely chat with your PDFs using grounded AI.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 border border-slate-200">
          <div>
            <button
              onClick={signInWithGoogle}
              className="w-full flex justify-center py-2.5 px-4 border border-slate-300 rounded-md shadow-sm bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-colors"
            >
              <LogIn className="w-5 h-5 mr-2 text-slate-400" />
              Continue with Google
            </button>
          </div>
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-slate-500">
                  Secure access via Supabase
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
