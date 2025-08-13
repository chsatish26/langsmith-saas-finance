import sys, os
from usecases.transaction_classifier_budget.module import run as run_a
from usecases.mortgage_prequal_advisor.module import run as run_b
from usecases.mortgage_rate_monitoring.module import run as run_c

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'all'
    base_out = os.path.join(os.path.dirname(__file__), 'outputs')
    if target in ('a','all'):
        run_a(output_dir=os.path.join(base_out,'a'))
    if target in ('b','all'):
        run_b(output_dir=os.path.join(base_out,'b'))
    if target in ('c','all'):
        run_c(output_dir=os.path.join(base_out,'c'))

if __name__ == '__main__':
    main()
