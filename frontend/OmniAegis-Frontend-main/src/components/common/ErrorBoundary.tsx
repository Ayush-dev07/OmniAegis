import React from 'react';
import GlassCard from './GlassCard';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // TODO: send to logging service
    // console.error(error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <GlassCard className="text-red-300">
          <div role="alert">
            <strong>Something went wrong.</strong>
            <div>{this.state.error?.message}</div>
          </div>
        </GlassCard>
      );
    }
    return this.props.children as JSX.Element;
  }
}

export default ErrorBoundary;
