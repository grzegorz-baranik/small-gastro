import { Check } from 'lucide-react'

export interface WizardStep {
  id: number
  title: string
  status: 'pending' | 'current' | 'completed'
}

interface WizardStepperProps {
  steps: WizardStep[]
  currentStep: number
  onStepClick: (stepIndex: number) => void
}

export default function WizardStepper({
  steps,
  currentStep: _currentStep,
  onStepClick,
}: WizardStepperProps) {
  return (
    <nav className="flex items-center justify-center" aria-label="Progress" data-testid="wizard-stepper">
      <ol className="flex items-center space-x-4">
        {steps.map((step, index) => (
          <li key={step.id} className="flex items-center">
            {/* Step circle */}
            <button
              type="button"
              onClick={() => step.status === 'completed' && onStepClick(index)}
              disabled={step.status === 'pending'}
              data-testid={`wizard-step-${index}`}
              className={`
                relative flex items-center justify-center w-10 h-10 rounded-full border-2
                transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
                ${
                  step.status === 'completed'
                    ? 'bg-primary-600 border-primary-600 text-white cursor-pointer hover:bg-primary-700'
                    : step.status === 'current'
                      ? 'border-primary-600 text-primary-600 bg-white'
                      : 'border-gray-300 text-gray-400 bg-white cursor-not-allowed'
                }
              `}
              aria-current={step.status === 'current' ? 'step' : undefined}
            >
              {step.status === 'completed' ? (
                <Check className="w-5 h-5" aria-hidden="true" />
              ) : (
                <span className="text-sm font-medium">{step.id}</span>
              )}
            </button>

            {/* Step title */}
            <span
              className={`
                ml-2 text-sm font-medium hidden sm:block
                ${
                  step.status === 'completed'
                    ? 'text-primary-600'
                    : step.status === 'current'
                      ? 'text-primary-600'
                      : 'text-gray-500'
                }
              `}
            >
              {step.title}
            </span>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={`
                  w-8 sm:w-12 h-0.5 mx-2 sm:mx-4
                  ${
                    steps[index + 1].status !== 'pending'
                      ? 'bg-primary-600'
                      : 'bg-gray-300'
                  }
                `}
                aria-hidden="true"
              />
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
