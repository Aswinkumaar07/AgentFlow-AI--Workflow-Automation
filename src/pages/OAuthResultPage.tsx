import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertCircle, ArrowRight, RefreshCw, Zap } from 'lucide-react';
import { useOAuthStore } from '../store/useOAuthStore';
import { useAuthStore } from '../store/useAuthStore';
import { oauthApi } from '../api/oauth';
import { authApi } from '../api/auth';

export const OAuthResultPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const mode = searchParams.get('mode'); // 'auth' for user SSO, null/empty for tool connector
  const provider = searchParams.get('provider') || 'google';
  const status = searchParams.get('status') || 'success';
  const isSuccess = status === 'success';

  const [countdown, setCountdown] = useState<number>(2);

  const formattedProvider = provider.charAt(0).toUpperCase() + provider.slice(1).toLowerCase();
  const isUserAuth = mode === 'auth';

  useEffect(() => {
    if (isUserAuth && isSuccess) {
      const code = searchParams.get('code');
      if (code) {
        authApi.exchangeGoogleCode(code)
          .then((res) => {
            useAuthStore.getState().setAuth(res.user, res.access_token);
          })
          .catch((err) => {
            console.error('[AUTH-SSO] Error exchanging SSO code:', err);
          });
      }
    } else if (!isUserAuth && isSuccess) {

      // Connector account linked success — refresh connection status in Zustand store
      useOAuthStore.getState().fetchOAuthData().catch((err) => {
        console.error('[AUTH-6] Error refreshing OAuth data after callback:', err);
      });
    }
  }, [isUserAuth, isSuccess, searchParams]);


  useEffect(() => {
    if (!isSuccess) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          navigate(isUserAuth ? '/dashboard' : '/workflows');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isSuccess, isUserAuth, navigate]);

  const handleContinue = () => {
    navigate(isUserAuth ? '/dashboard' : '/workflows');
  };

  const handleRetry = async () => {
    try {
      if (isUserAuth) {
        const data = await authApi.getGoogleLoginUrl();
        if (data?.url) {
          window.location.href = data.url;
        }
      } else {
        await oauthApi.connectAccount(provider);
      }
    } catch (err) {
      console.error(`Failed to retry authorization for ${provider}:`, err);
      navigate(isUserAuth ? '/login' : '/connectors');
    }
  };

  return (
    <div className="min-h-screen bg-[#0E0918] text-white flex items-center justify-center p-4 relative overflow-hidden font-sans">
      {/* ── Ambient Background Orbs ──────────────────────────────────────── */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        <div
          className="absolute rounded-full"
          style={{
            width: 600,
            height: 600,
            top: '-15%',
            left: '30%',
            background: 'radial-gradient(circle, rgba(255, 109, 0, 0.14) 0%, transparent 70%)',
            filter: 'blur(90px)'
          }}
        />
        <div
          className="absolute rounded-full"
          style={{
            width: 500,
            height: 500,
            bottom: '0%',
            right: '20%',
            background: 'radial-gradient(circle, rgba(168, 85, 247, 0.08) 0%, transparent 70%)',
            filter: 'blur(90px)'
          }}
        />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(to right, rgba(255, 109, 0, 0.4) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 109, 0, 0.4) 1px, transparent 1px)`,
            backgroundSize: '48px 48px'
          }}
        />
      </div>

      {/* ── Centered Glass Card ─────────────────────────────────────────── */}
      <div className="relative w-full max-w-md bg-[#1B1728]/85 border border-[rgba(255,255,255,0.12)] rounded-2xl p-8 shadow-2xl backdrop-blur-2xl text-center z-10">
        {/* AgentFlow AI Header */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-white font-bold shadow-[0_4px_18px_rgba(255,109,0,0.40)]">
            <Zap className="h-6 w-6 fill-current" />
          </div>
          <span className="font-bold text-xl tracking-tight text-white">AgentFlow AI</span>
        </div>

        {isSuccess ? (
          <>
            {/* Success Icon Halo */}
            <div className="w-20 h-20 rounded-full bg-[#10B981]/15 border border-[#10B981]/30 flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(16,185,129,0.20)]">
              <CheckCircle2 className="w-10 h-10 text-[#34D399]" />
            </div>

            <h1 className="text-2xl font-bold text-white mb-2">
              {isUserAuth ? 'Sign In Successful' : 'Connection Successful'}
            </h1>
            <p className="text-[rgba(255,255,255,0.60)] text-sm mb-6 font-medium">
              {isUserAuth ? (
                <>Welcome back! Authenticated with <span className="font-bold text-white">{searchParams.get('email') || formattedProvider}</span>.</>
              ) : (
                <><span className="font-bold text-white">{formattedProvider}</span> connected successfully.</>
              )}
            </p>

            <div className="bg-[rgba(0,0,0,0.25)] border border-[rgba(255,255,255,0.10)] rounded-xl p-4 mb-6">
              <p className="text-xs text-[rgba(255,255,255,0.50)] mb-1 font-medium">
                {isUserAuth ? 'Redirecting to Dashboard...' : 'Returning to AgentFlow Studio...'}
              </p>
              <div className="flex items-center justify-center gap-2 text-xs font-mono text-[#FF6D00]">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Redirecting in {countdown}s</span>
              </div>
            </div>

            <button
              onClick={handleContinue}
              className="w-full py-3 px-4 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] hover:brightness-110 text-white font-bold rounded-xl shadow-[0_4px_20px_rgba(255,109,0,0.35)] transition-all flex items-center justify-center gap-2"
            >
              <span>{isUserAuth ? 'Continue to Dashboard' : 'Continue to AgentFlow'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </>
        ) : (
          <>
            {/* Failure Icon Halo */}
            <div className="w-20 h-20 rounded-full bg-[#EF4444]/15 border border-[#EF4444]/30 flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(239,68,68,0.20)]">
              <AlertCircle className="w-10 h-10 text-[#F87171]" />
            </div>

            <h1 className="text-2xl font-bold text-white mb-2">
              {isUserAuth ? 'Authentication Failed' : 'Connection Failed'}
            </h1>
            <p className="text-[rgba(255,255,255,0.60)] text-sm mb-8 font-medium">
              We couldn't authenticate with <span className="font-bold text-white">{formattedProvider}</span>.
            </p>

            <div className="space-y-3">
              <button
                onClick={handleRetry}
                className="w-full py-3 px-4 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] hover:brightness-110 text-white font-bold rounded-xl shadow-[0_4px_20px_rgba(255,109,0,0.35)] transition-all flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </button>

              <button
                onClick={handleContinue}
                className="w-full py-3 px-4 bg-[#13102A] hover:bg-[#231E3A] text-[rgba(255,255,255,0.80)] font-semibold rounded-xl border border-[rgba(255,255,255,0.12)] transition-all"
              >
                <span>{isUserAuth ? 'Return to Login' : 'Return to AgentFlow'}</span>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

