from base_import import *
from popup_window import ConfirmationPopup

def check_started():
    "检查是否存在已启动的实例，如果存在就弹窗，选择终止现有实例或取消启动。"
    pid_file = os.path.join(os.path.dirname(sys.argv[0]), "app.pid")

    existing_pid = None
    try:
        with open(pid_file, "r") as f:
            existing_pid = int(f.read().strip())
        if existing_pid == os.getpid():
            return True
        if not psutil.pid_exists(existing_pid):
            existing_pid = None
    except Exception:
        pass

    if existing_pid is None:
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
        return True
    if '--forceKillAllExistingInstances' in sys.argv:
        try:
            os.kill(existing_pid, 9)
        except Exception:
            pass
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
        return True
    else:
        def on_user_response(response):
            if response:
                try:
                    os.kill(existing_pid, 9)
                except Exception:
                    pass
                with open(pid_file, "w") as f:
                    f.write(str(os.getpid()))
            else:
                sys.exit(0)

        popup = ConfirmationPopup(
            f"Another instance (PID: {existing_pid}) is already running. Do you want to terminate it?",
            title="Instance Already Running",
            callback=on_user_response
        )
        popup.show_popup()
        # wait for user response
        while popup.user_response is None:
            QApplication.processEvents()
            time.sleep(0.05)
        return False
    
if __name__ == "__main__":
    "测试"
    app = QApplication(sys.argv)
    print(check_started())
    app.exec_()
    input("Press Enter to exit...")
    os.remove(os.path.join(os.path.dirname(sys.argv[0]), "app.pid"))
    sys.exit(0)