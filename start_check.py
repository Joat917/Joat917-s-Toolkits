from base_import import *
from popup_window import ConfirmationPopup

class CheckStarted:
    def __init__(self):
        self.pid_file = os.path.join(WORKING_DIR, "app.pid")
        self.force_kill = '--forceKillAllExistingInstances' in sys.argv
        pass

    def on_user_response(self, response:bool):
        if response:
            try:
                os.kill(self.get_existing_pid(), 9)
            except Exception:
                pass
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
        else:
            sys.exit(0)

    def get_existing_pid(self):
        try:
            with open(self.pid_file, "r") as f:
                existing_pid = int(f.read().strip())
            if existing_pid == os.getpid():
                return None
            if not psutil.pid_exists(existing_pid):
                return None
            return existing_pid
        except Exception:
            pass
        return
    
    def __enter__(self):
        existing_pid = self.get_existing_pid()
        if existing_pid is None:
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
            return True
        if self.force_kill:
            try:
                os.kill(existing_pid, 9)
            except Exception:
                pass
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
            return True
        else:
            popup = ConfirmationPopup(
                f"Another instance (PID: {existing_pid}) is already running. Do you want to terminate it?",
                title="Warning:",
                callback=self.on_user_response
            )
            popup.show_popup()
            # wait for user response
            while popup.user_response is None:
                QApplication.processEvents()
                time.sleep(0.05)
            return False

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except Exception:
            pass
