import threading

from src.utils.greendc import GreenDCCalculator


class TrainingStatus:
    is_training = False
    progress = 0
    current_step = 0
    total_steps = 0
    last_log = ""
    stop_requested = False


class EvaluationStatus:
    is_evaluating = False
    last_log = ""
    error = ""
    result = None
    stop_requested = False


status = TrainingStatus()
eval_status = EvaluationStatus()
greendc = GreenDCCalculator()
training_lock = threading.Lock()
evaluation_lock = threading.Lock()
