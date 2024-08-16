
def print_progress_bar(work, completed, total, bar_length=40):
    progress = completed / total
    block = int(round(bar_length * progress))
    progress_bar = f"[{'#' * block}{'.' * (bar_length - block)}]"
    progress_percent = f"{progress * 100:.2f}%"
    print(f"\033[91m{work}진행 상황: {progress_bar} {progress_percent} ({completed}/{total})\033[0m", flush=True)
