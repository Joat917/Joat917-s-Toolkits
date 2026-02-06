import numpy as np
import time
from scipy.integrate import RK45
from PIL import Image, ImageDraw, ImageTk
import bisect

class Pendulum:
    def __init__(self, beta, eta, epsilon, theta_0=None, phi_0=None, alpha=None, seed=None, minE=0.5):
        """
模型说明：
一个质量为1、长度为1的均匀杆，在距离一端eta处放置支点固定在墙上，这一端链接另一个长度为beta，质量为alpha(默认=beta)的均匀杆于epsilon*beta处。
整个系统在大小为1的重力下运动，没有摩擦阻力。
theta是第一个杆偏离平衡的角度（垂直向下），phi是第二个杆偏离平衡的角度，其默认分布在极坐标内为偏心圆。
        """
        # 设置参数
        assert beta>0
        assert 0<=eta<=0.5
        assert 0<=epsilon<=0.5
        if alpha is None:
            alpha=beta
        else:
            assert alpha>0
        
        self.beta=beta
        self.eta=eta
        self.epsilon=epsilon
        self.alpha=alpha

        b=beta*(0.5-epsilon)
        self.v1=0.5-eta-alpha*eta
        self.v2=alpha*b
        self.t1=(0.5-eta)**2+1/12+alpha*eta**2
        self.t2=alpha*eta*b
        self.t3=1/12*alpha*beta**2+alpha*b**2

        self._tmp_arr_1=np.array([[self.t1,-self.t2],[-self.t2,self.t3]], np.float64)
        self._tmp_vec_2=np.array([0,0],np.float64)

        # 初始化初值条件
        self.rng=np.random.Generator(np.random.PCG64(seed))
        self.solver = None
        while self.solver is None or self.E<minE:
            y0=np.array([
                self._off_circle_distribution(e=0.0) if theta_0 is None else theta_0,
                self._off_circle_distribution(e=-0.0) if phi_0 is None else phi_0,
                self.rng.normal(0, 0.5), 
                self.rng.normal(0, 0.5)
            ], np.float64)  # theta, phi, theta_dot, phi_dot
            self.solver = RK45(self.derivs, 0, y0, np.inf, max_step=0.1)
        
        self.initial_E = self.E # 应当守恒

        # 确保自身参数类型
        for n in ["v1","v2","t1","t2","t3","beta","eta","epsilon","alpha"]:
            self.__setattr__(n, np.float64(self.__getattribute__(n)))

        pass

    @property
    def t(self):
        return self.solver.t
    
    @property
    def theta(self):
        return self.solver.y[0]
    
    @property
    def phi(self):
        return self.solver.y[1]
    
    @property
    def E(self):
        "计算当前系统的总能量"
        theta, phi, theta_dot, phi_dot = self.solver.y
        K=0.5*(self.t1*theta_dot**2+self.t3*phi_dot**2-2*self.t2*np.cos(theta-phi)*theta_dot*phi_dot)
        U=self.v1*(1-np.cos(theta))+self.v2*(1-np.cos(phi))
        return K+U

    def derivs(self, t, y):
        theta, phi, theta_dot, phi_dot = y
        self._tmp_arr_1[0,1]=self._tmp_arr_1[1,0]=-self.t2*np.cos(theta-phi)
        self._tmp_vec_2[0]=self.t2*np.sin(theta-phi)*phi_dot**2-self.v1*np.sin(theta)
        self._tmp_vec_2[1]=-self.t2*np.sin(theta-phi)*theta_dot**2-self.v2*np.sin(phi)
        theta_ddot, phi_ddot=np.linalg.solve(self._tmp_arr_1, self._tmp_vec_2)
        return np.array([theta_dot, phi_dot, theta_ddot, phi_ddot], np.float32)

    def _off_circle_distribution(self, e=-0.5):
        "给出一个弧度制角度。e=0的时候为均匀分布，e越接近1得到0度的可能性越大，e越接近-1得到180度的可能性越大。"
        theta=self.rng.uniform(0, 2*np.pi)
        if np.isclose(e, 0):
            return theta
        b=np.sqrt(1+e*e+2*e*np.cos(theta))
        c=(b*b+e*e-1)/(2*b*e)
        return np.arccos(c)
    
    def step(self):
        "推进一步，更新theta和phi的值"
        self.solver.step()

class Pendulum_Manager:
    "管理生成的Pendulum对象"
    def __init__(self, a, b, c, d):
        """
参数说明：
a和b是次级独立杆子支点两侧的长度，c是主级杆子支点距离次杆支点端的距离，d是主杆支点与另一端的距离。
摆的初始参数均为默认值，如有需要可以在开始推演前自行调整。
        """
        a,b=sorted([a,b])
        self.p=Pendulum((a+b)/(c+d), c/(c+d), a/(a+b))
        self.t_list=[]
        self.theta_list=[]
        self.phi_list=[]

    def get_theta_phi(self, t):
        "给出给定时刻下的theta和phi参数。使用线性插值估计一个特定步长之间的值"
        assert t>=0
        while len(self.t_list)<2 or t>self.t_list[-2]:
            self.t_list.append(self.p.t)
            self.theta_list.append(self.p.theta)
            self.phi_list.append(self.p.phi)
            self.p.step()
        i=bisect.bisect_left(self.t_list, t)
        if np.isclose(t, self.t_list[i], atol=1e-3) or i+1>=len(self.t_list):
            return self.theta_list[i], self.phi_list[i]
        a=(self.t_list[i+1]-t)/(self.t_list[i+1]-self.t_list[i])
        b=(t-self.t_list[i])/(self.t_list[i+1]-self.t_list[i])
        return self.theta_list[i]*a+self.theta_list[i+1]*b, self.phi_list[i]*a+self.phi_list[i+1]*b


def test():
    "测试摆的部分，并绘制图像"
    from matplotlib import pyplot as plt
    a,b,c,d=2,3.5,1.6,7
    T=40
    p=Pendulum((a+b)/(c+d), c/(c+d), a/(a+b))
    theta_list=[p.theta]
    phi_list=[p.phi]
    t_list=[p.t]
    while p.t<T:
        p.step()
        theta_list.append(p.theta)
        phi_list.append(p.phi)
        t_list.append(p.t)
    plt.plot(t_list, theta_list)
    plt.plot(t_list, phi_list)

    p2=Pendulum((a+b)/(c+d), c/(c+d), a/(a+b))
    p2.theta=theta_list[0]+1e-3
    p2.phi=phi_list[0]-1e-3
    theta_list=[p2.theta]
    phi_list=[p2.phi]
    t_list=[p2.t]
    while p2.t<T:
        p2.step()
        theta_list.append(p2.theta)
        phi_list.append(p2.phi)
        t_list.append(p2.t)
    plt.plot(t_list, theta_list)
    plt.plot(t_list, phi_list)
    plt.legend(["theta1","phi1","theta2","phi2"])
    plt.show()


try:
    import tkinter as tk
    class DisplayTK(tk.Tk):
        def __init__(self, a,b,c,d,s=100, fps=10, timescale=1):
            "使用特定参数初始化摆，然后给定图片放大比例、帧率，初始化显示模块"
            super().__init__()
            self.geometry("+1000+400")
            self.overrideredirect(True)
            self.config(bg="black")
            self.attributes("-transparentcolor", "black")

            self.label=tk.Label(self)
            self.label.config(bg='black')
            self.label.pack()
            self.label.bind("<ButtonPress-1>", self.on_drag_start)
            self.label.bind("<B1-Motion>", self.on_drag_motion)
            self.label.bind("<Button-3>", self.show_context_menu)

            self.context_menu = tk.Menu(self, tearoff=0)
            self.context_menu.add_command(label="RESET", command=self.reset_pendulum)
            self.context_menu.add_command(label="TOPMOST", command=self.set_topmost)
            self.context_menu.add_command(label="CLOSE", command=self.destroy)

            self.a=a
            self.b=b
            self.c=c
            self.d=d
            self.s=s
            self.timescale=timescale

            self.image_generator=get_image_renderer(Pendulum_Manager(a,b,c,d), s=s, fps=fps/timescale)
            self.fps=fps
            self.top_most_status=False
            self.set_topmost()

            self._old_tick_time=0
            self.update_frame()

        def on_drag_start(self, event):
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.image_offset_x = self.winfo_x() - event.x_root
            self.image_offset_y = self.winfo_y() - event.y_root

        def on_drag_motion(self, event):
            x = event.x_root + self.image_offset_x
            y = event.y_root + self.image_offset_y
            self.geometry(f"+{x}+{y}")

        def show_context_menu(self, event):
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

        def update_frame(self):
            dt=self._old_tick_time+1/self.fps-time.perf_counter()
            if dt>0:
                self._old_tick_time+=1/self.fps
                self.after(int(dt*1000), self.update_frame)
            else:
                self._old_tick_time=time.perf_counter()
                self.after(1, self.update_frame)
            im=self.image_generator()
            phim=ImageTk.PhotoImage(im)
            self.label.config(image=phim)
            self.label.image=phim
                

        def set_topmost(self):
            if self.top_most_status:
                self.top_most_status=False
                self.attributes("-topmost", False)
            else:
                self.top_most_status=True
                self.attributes("-topmost", True)

        def reset_pendulum(self):
            self.image_generator=get_image_renderer(Pendulum_Manager(self.a,self.b,self.c,self.d), s=self.s, fps=self.fps/self.timescale)

except ImportError:
    pass


from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QLabel, QMenu, QApplication
from PyQt5.QtGui import QPixmap, QImage
class DisplayQt(QWidget):
    def __init__(self, a,b,c,d,s=200, fps=10, timescale=1, parent=None):
        super().__init__(parent=parent)
        self.master = parent

        self._init_window(s)
        self._init_ui(s)

        self.a=a
        self.b=b
        self.c=c
        self.d=d
        self.s=s
        self.timescale=timescale

        self.image_generator=get_image_renderer(Pendulum_Manager(a,b,c,d), s=s, fps=fps/timescale)
        self.fps=fps
        self._old_tick_time=0
        self.update_frame()

    def _init_window(self, s):
        self.setWindowTitle("Chaotic Pendulum")
        self.setGeometry(1000, 400, 2*s, 2*s)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def _init_ui(self, s):
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 2*s, 2*s)
        self.label.setStyleSheet("background-color: transparent;")
        self.label.mousePressEvent = self.on_drag_start
        self.label.mouseMoveEvent = self.on_drag_motion
        self.label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label.customContextMenuRequested.connect(self.show_context_menu)

        self.context_menu = QMenu(self)
        self.context_menu.addAction("RESET", self.reset_pendulum)
        self.context_menu.addAction("CLOSE", self.close)
        
    def on_drag_start(self, event):
        self.drag_start_x = event.globalX()
        self.drag_start_y = event.globalY()
        self.image_offset_x = self.x() - event.globalX()
        self.image_offset_y = self.y() - event.globalY()

    def on_drag_motion(self, event):
        x = event.globalX() + self.image_offset_x
        y = event.globalY() + self.image_offset_y
        self.move(x, y)

    def show_context_menu(self, position):
        self.context_menu.exec_(self.label.mapToGlobal(position))

    def update_frame(self):
        dt=self._old_tick_time+1/self.fps-time.perf_counter()
        if dt>0:
            self._old_tick_time+=1/self.fps
            QTimer.singleShot(int(dt*1000), self.update_frame)
        else:
            self._old_tick_time=time.perf_counter()
            QTimer.singleShot(1, self.update_frame)
        im=self.image_generator()
        qim=QImage(im.tobytes(), im.width, im.height, QImage.Format_RGBA8888)
        pixmap=QPixmap.fromImage(qim)
        self.label.setPixmap(pixmap)
    
    def reset_pendulum(self):
        self.image_generator=get_image_renderer(Pendulum_Manager(self.a,self.b,self.c,self.d), s=self.s, fps=self.fps/self.timescale)


def get_image_renderer(q:Pendulum_Manager, s=100, fps=10):
    "给一个摆的系统，返回一个函数，调用时依次生成摆每一帧的图片"
    p=q.p
    l=max(p.beta*(1-p.epsilon)+p.eta, 1-p.eta)
    canvas=Image.new('RGBA', (round(2*s*l),)*2)
    def paint_rectangle(pencil:ImageDraw.ImageDraw, center:tuple, direction:float, backwards:float, forwards:float, fill="white", scale=s, width=round(s/10), cos=np.cos, sin=np.sin):
        pencil.line((scale*(center[0]-backwards*sin(direction)), scale*(center[1]-backwards*cos(direction)), 
                     scale*(center[0]+forwards*sin(direction)), scale*(center[1]+forwards*cos(direction))), fill=fill, width=width)
    def paint_circle(pencil:ImageDraw.ImageDraw, center:tuple, radius:float, fill="red", scale=s):
        pencil.ellipse((scale*(center[0]-radius),scale*(center[1]-radius),scale*(center[0]+radius),scale*(center[1]+radius)), fill=fill, width=0)
    def render_image():
        t=0
        while True:
            theta, phi=q.get_theta_phi(t)
            t+=1/fps
            im=canvas.copy()
            pencil=ImageDraw.Draw(im)
            paint_rectangle(pencil, (l,l), theta, p.eta, 1-p.eta, width=round(s/10)+3, fill=(18,18,18,100))
            paint_rectangle(pencil, (l-p.eta*np.sin(theta),l-p.eta*np.cos(theta)), phi, p.beta*p.epsilon, p.beta*(1-p.epsilon), width=round(s/10)+3, fill=(18,18,18,100))
            paint_rectangle(pencil, (l,l), theta, p.eta, 1-p.eta)
            paint_circle(pencil, (l,l), 1/20, fill=(180, 180, 180))
            paint_rectangle(pencil, (l-p.eta*np.sin(theta),l-p.eta*np.cos(theta)), phi, p.beta*p.epsilon, p.beta*(1-p.epsilon))
            yield im
    image_renderer=render_image()
    def get_image():
        return image_renderer.send(None)
    return get_image

try:
    from basic_settings import *
    from main_widgets import WidgetBox, PlainText, SwitchButton, MainWindow, CustomMenu
    class DisplayAdvanced(DisplayQt):
        def _init_ui(self, s):
            self.label = QLabel(self)
            self.label.setGeometry(0, 0, 2*s, 2*s)
            self.label.setStyleSheet("background-color: transparent;")
            self.label.mousePressEvent = self.on_drag_start
            self.label.mouseMoveEvent = self.on_drag_motion
            self.label.setContextMenuPolicy(Qt.CustomContextMenu)
            self.label.customContextMenuRequested.connect(self.show_context_menu)

            self.context_menu = CustomMenu(self)
            self.context_menu.addAction("RESET", self.reset_pendulum)
            self.context_menu.addAction("CLOSE", self.close)

            if self.master is not None:
                self.master.trayWidget.add_action("Pendulum:Reset", self.reset_pendulum)

        def close(self):
            if self.master is not None:
                self.master.trayWidget.remove_action("Pendulum:Reset")
            super().close()

    class ChaoticPendulumWidget(WidgetBox):
        def __init__(self, mainwindow:MainWindow):
            super().__init__(parent=mainwindow, title="Chaotic Pendulum")
            self.pendulum_display = None
            self.toggle_button = SwitchButton(
                onturnon = self.enable_display,
                onturnoff = self.disable_display,
            )
            self.status_label = PlainText(
                text="Disabled", 
                parent=self,
            )
            self.sublayout = QHBoxLayout()
            self.sublayout.addWidget(self.toggle_button)
            self.sublayout.addWidget(self.status_label)
            self.layout.addLayout(self.sublayout)

        def enable_display(self):
            if self.pendulum_display is not None:
                self.disable_display()
            self.pendulum_display = DisplayAdvanced(2,3.5,1.6,7, fps=30, timescale=3, parent=self.master)
            self.pendulum_display.show()
            self.status_label.setText("Enabled")

        def disable_display(self):
            if self.pendulum_display is not None:
                self.pendulum_display.close()
                self.pendulum_display = None
            self.status_label.setText("Disabled")
except ImportError:
    pass


if __name__=="__main__":
    # DisplayTK(2,3.5,1.6,7, fps=30, timescale=3).mainloop()
    app = QApplication([])
    DisplayQt(2,3.5,1.6,7, fps=30, timescale=3).show()
    sys.exit(app.exec_()) 

