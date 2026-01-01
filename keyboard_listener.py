from base_import import *

KEYPAIRPRE="`~1!2@3#4$5%6^7&8*9(0)-_=+[{]}\\|;:\'\",<.>/?"
KEYGROUPS={}
for i in range(len(KEYPAIRPRE)):
    KEYGROUPS[KEYPAIRPRE[i]]=(KEYPAIRPRE[i|1], KEYPAIRPRE[i&(-2)])
for ch in 'abcdefghijklmnopqrstuvwxyz':
    _keys_in_group = (ch.upper(), f"Ctrl^{ch.upper()}")
    for _k in _keys_in_group:
        KEYGROUPS[_k] = _keys_in_group

class KeyboardListener:
    def __init__(self, press_callbacks=[], release_callbacks=[], auto_start=True):
        self.press_callbacks=press_callbacks
        self.release_callbacks=release_callbacks

        self.keyboardListener=pynput.keyboard.Listener(self.callbackKey(self._callbackPress), self.callbackKey(self._callbackRelease, callgroup=True))
        self.mouseListener=pynput.mouse.Listener(on_click=self.callbackMouse(self._callbackPress, self._callbackRelease))
        assert self.keyboardListener.daemon
        assert self.mouseListener.daemon

        if auto_start:
            self.start()

    def start(self):
        self.keyboardListener.start()
        self.mouseListener.start()

    @staticmethod
    def translate(x):
        if len(x)==1 and 1<=ord(x)<=26:
            x=f"Ctrl^{chr(ord(x)+64)}"
        y=x.upper()
        if y.endswith('_L') or y.endswith('_R'):
            return y[:-2]
        else:
            return y

    def callbackKey(self, callback, callgroup=False):
        def onPress(key):
            if isinstance(key, pynput.keyboard.Key):
                c=key.name
            elif isinstance(key, pynput.keyboard.KeyCode):
                c=key.char
            else:
                return
            if c is None:
                return
            c=self.translate(c)
            if not all([0x20<=ord(ch)<=0x7e for ch in c]):
                return
            if callgroup:
                for d in KEYGROUPS.get(c, (c,)):
                    if d!=c:
                        callback(d)
            return callback(c)
        return onPress

    def callbackMouse(self, callbackPress, callbackRelease):
        def onClick(posX, posY, button, pressed):
            if not isinstance(button, pynput.mouse.Button):
                return
            if pressed:
                callbackPress(self.translate('button'+button.name))
            else:
                callbackRelease(self.translate('button'+button.name))
        return onClick
    
    def _callbackPress(self, key_str):
        "在监听器线程中调用的事件处理函数"
        return self.callbackPress(key_str)
    
    def _callbackRelease(self, key_str):
        return self.callbackRelease(key_str)
    
    def callbackPress(self, key_str):
        "在主线程中调用的事件处理函数"
        for callback in self.press_callbacks:
            callback(key_str)

    def callbackRelease(self, key_str):
        for callback in self.release_callbacks:
            callback(key_str)

class KeyboardListenerSignalPatched(KeyboardListener, QObject):
    signalPress = pyqtSignal(str)
    signalRelease=pyqtSignal(str)
    def __init__(self, press_callbacks=[], release_callbacks=[], auto_start=True):
        QObject.__init__(self)
        KeyboardListener.__init__(self, press_callbacks=[], release_callbacks=[], auto_start=False)
        self.signalPress.connect(self.callbackPress)
        self.signalRelease.connect(self.callbackRelease)
        self.press_callbacks=press_callbacks
        self.release_callbacks=release_callbacks
        if auto_start:
            self.start()

    def _callbackPress(self, key_str):
        "在监听器线程中调用的事件处理函数"
        self.signalPress.emit(key_str)

    def _callbackRelease(self, key_str):
        self.signalRelease.emit(key_str)


if __name__=="__main__":
    print("Testing KeyboardListener...")
    listener = KeyboardListener(
        press_callbacks=[lambda k: print(f"Pressed: {k}")],
        release_callbacks=[lambda k: print(f"Released: {k}")]
    )
    input("Press Enter to stop...\n")

