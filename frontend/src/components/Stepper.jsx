import { useState } from 'react';

const STEPS = [
  { id: 1, label: 'Setup' },
  { id: 2, label: 'Data Check' },
  { id: 3, label: 'L1 Review' },
  { id: 4, label: 'L2 Review' },
  { id: 5, label: 'Generate' },
  { id: 6, label: 'Result' },
];

export default function Stepper({ currentStep, onStepClick, completedSteps = [] }) {
  return (
    <div className="stepper">
      {STEPS.map((step, i) => {
        const isActive = step.id === currentStep;
        const isCompleted = completedSteps.includes(step.id);
        const isClickable = isCompleted || step.id <= currentStep;

        return (
          <div key={step.id} style={{ display: 'flex', alignItems: 'center', flex: i < STEPS.length - 1 ? 1 : 'unset' }}>
            <div
              className={`step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
              onClick={() => isClickable && onStepClick?.(step.id)}
              style={{ cursor: isClickable ? 'pointer' : 'default' }}
            >
              <span className="step-number">
                {isCompleted ? '✓' : step.id}
              </span>
              <span>{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`step-connector ${isCompleted ? 'completed' : ''}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
