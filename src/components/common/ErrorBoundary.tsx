import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, LayoutDashboard, Copy, Check } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  copied: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    copied: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, copied: false };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Unhandled React Exception caught by ErrorBoundary:', error, errorInfo);
  }

  public handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  public handleGoDashboard = () => {
    window.location.href = '/dashboard';
  };

  public handleCopyError = () => {
    if (this.state.error?.stack) {
      navigator.clipboard.writeText(this.state.error.stack);
      this.setState({ copied: true });
      setTimeout(() => this.setState({ copied: false }), 2000);
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-6 text-foreground">
          <div className="max-w-lg w-full p-8 rounded-2xl border border-border bg-card shadow-2xl space-y-6 text-center">
            {/* Friendly Illustration Icon */}
            <div className="h-16 w-16 rounded-2xl bg-destructive/10 text-destructive flex items-center justify-center mx-auto shadow-inner">
              <AlertTriangle className="h-8 w-8" />
            </div>

            <div>
              <h2 className="text-xl font-bold tracking-tight">Something Went Wrong</h2>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                AgentFlow AI encountered an unexpected UI rendering error. The platform isolated the exception to prevent data loss.
              </p>
            </div>

            {/* Error Message Details */}
            <div className="p-3.5 bg-muted/40 rounded-xl font-mono text-[11px] text-left overflow-x-auto border border-border text-destructive space-y-1">
              <p className="font-semibold">{this.state.error?.name || 'Error'}: {this.state.error?.message || 'Unknown Exception'}</p>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-2 pt-2">
              <button
                onClick={this.handleRetry}
                className="flex-1 py-2.5 bg-primary text-primary-foreground text-xs font-semibold rounded-xl hover:bg-primary/90 transition flex items-center justify-center gap-1.5 shadow-sm"
              >
                <RefreshCw className="h-3.5 w-3.5" /> Try Again
              </button>

              <button
                onClick={this.handleGoDashboard}
                className="flex-1 py-2.5 border border-border bg-background hover:bg-muted text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1.5"
              >
                <LayoutDashboard className="h-3.5 w-3.5" /> Dashboard
              </button>

              <button
                onClick={this.handleCopyError}
                className="py-2.5 px-3 border border-border bg-background hover:bg-muted text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1 text-muted-foreground hover:text-foreground"
                title="Copy Stack Trace"
              >
                {this.state.copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
