import React from 'react';
import { Check, Clock, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';
import { mockLifecycleSteps } from '../../data/mockData';

export function LifecycleStepper() {
  const getStepIcon = (index, status) => {
    if (status === 'completed') return <Check size={16} />;
    if (status === 'in-progress') return <Clock size={16} />;
    
    switch (index) {
      case 0: return <AlertTriangle size={16} />;
      case 1: return <Cpu size={16} />;
      case 2: return <Clock size={16} />;
      case 3: return <Cpu size={16} />;
      case 4: return <ShieldCheck size={16} />;
      default: return index + 1;
    }
  };

  return (
    <div className="card" style={{ marginBottom: '28px' }}>
      <div className="card-title">
        <span>Reconciliation Lifecycle Pipeline</span>
        <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-blue)' }}>
          Active Flow: VIO-2026-001 (Rahul Kumar)
        </span>
      </div>
      <div className="stepper-container">
        <div className="stepper-track"></div>
        {mockLifecycleSteps.map((step, idx) => (
          <div key={step.id} className={`step-item ${step.status}`}>
            <div className="step-node">
              {getStepIcon(idx, step.status)}
            </div>
            <div className="step-label">{step.name}</div>
            <div className="step-time">{step.timestamp}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
