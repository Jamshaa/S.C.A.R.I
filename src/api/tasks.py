import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Any


def get_python_executable(base_dir: Path) -> str:
    for candidate in [
        base_dir / ".venv" / "Scripts" / "python.exe",
        base_dir / "venv" / "Scripts" / "python.exe",
        base_dir / ".venv" / "bin" / "python",
        base_dir / "venv" / "bin" / "python",
    ]:
        if candidate.exists():
            return str(candidate)
    return "python"


def run_train_task(params: Any, *, base_dir: Path, status: Any, logger: Any) -> None:
    status.is_training = True
    status.progress = 0
    status.current_step = 0
    status.total_steps = params.timesteps
    status.stop_requested = False
    logger.info("Starting training task: %s for %s steps", params.name, params.timesteps)
    process = None
    try:
        cmd = [
            get_python_executable(base_dir),
            "-m",
            "src.train",
            "--timesteps",
            str(params.timesteps),
            "--config",
            params.config,
            "--output-name",
            params.name,
            "--cooling-mode",
            params.cooling_mode,
        ]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=str(base_dir),
            env=env,
            bufsize=1,
        )

        import queue

        def reader(pipe: Any, output_queue: "queue.Queue[str | None]") -> None:
            try:
                with pipe:
                    for line in iter(pipe.readline, ""):
                        output_queue.put(line)
            finally:
                output_queue.put(None)

        output_queue: "queue.Queue[str | None]" = queue.Queue()
        thread = threading.Thread(target=reader, args=(process.stdout, output_queue), daemon=True)
        thread.start()

        while True:
            try:
                line = output_queue.get(timeout=1)
            except queue.Empty:
                if status.stop_requested:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    status.last_log = "Training stopped by user request."
                    break
                if process.poll() is not None:
                    break
                continue
            if line is None:
                break
            status.last_log = line.strip()
            if status.stop_requested:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                status.last_log = "Training stopped by user request."
                break
            if "Training complete" in line:
                status.progress = 100
            if "total_timesteps" in line:
                try:
                    parts = [part.strip() for part in line.split("|") if part.strip()]
                    step_value = next((int(part) for part in parts if part.isdigit()), None)
                    if step_value is not None:
                        status.current_step = step_value
                        status.progress = min(99, int(step_value / params.timesteps * 100))
                except ValueError:
                    logger.debug("Could not parse training progress from log line: %s", line.strip())
        process.wait()
        if process.returncode == 0 and not status.stop_requested:
            status.progress = 100
            status.last_log = "Training completed successfully."
        elif not status.stop_requested:
            status.last_log = f"Training failed with exit code {process.returncode}"
    except Exception as exc:
        status.last_log = f"Error: {exc}"
        logger.error("Training crashed: %s", exc)
    finally:
        status.is_training = False


def run_eval_task(
    models_arg: str,
    steps: int,
    output_dir: Path,
    config_path: str,
    *,
    base_dir: Path,
    eval_status: Any,
) -> None:
    eval_status.is_evaluating = True
    eval_status.error = ""
    eval_status.result = None
    eval_status.stop_requested = False
    process = None
    cmd = [
        get_python_executable(base_dir),
        "-m",
        "src.evaluate",
        "--config",
        config_path,
        "--models",
        models_arg,
        "--output",
        str(output_dir),
        "--steps",
        str(steps),
    ]
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=str(base_dir),
            env=env,
        )
        if process.stdout is not None:
            for line in process.stdout:
                eval_status.last_log = line.strip()
                if eval_status.stop_requested:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    eval_status.last_log = "Evaluation stopped by user request."
                    break
        if eval_status.stop_requested:
            eval_status.error = "Stopped by user."
        elif process.returncode == 0:
            metrics_path = output_dir / "metrics.json"
            if metrics_path.exists():
                with metrics_path.open("r", encoding="utf-8") as handle:
                    eval_status.result = json.load(handle)
        else:
            eval_status.error = f"Evaluation process exited with code {process.returncode}"
    except Exception as exc:
        eval_status.error = str(exc)
    finally:
        eval_status.is_evaluating = False
