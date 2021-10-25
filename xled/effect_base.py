import sys
import time

if sys.version_info.major == 2:
    from threading import _Timer
    TimerX = _Timer
else:
    from threading import Timer
    TimerX = Timer

class RepeatedTimer(TimerX):
    def run(self):
        lasttime = time.time()
        self.function(*self.args, **self.kwargs)
        while not self.finished.wait(max(0.0, self.interval - (time.time() - lasttime))):
            lasttime = time.time()
            self.function(*self.args, **self.kwargs)

effect_timer = None

class Effect(object):
    def __init__(self, ctr):
        self.ctr = ctr
        self.preferred_frames = 120
        self.preferred_fps = 8

    def reset(self, numframes=False):
        pass # provided by subclass

    def getnext(self):
        pass # provided by subclass

    def launch_rt(self):
        global effect_timer
        def doit():
            self.ctr.show_rt_frame(self.getnext())
        if effect_timer:
            effect_timer.cancel()
        effect_timer = RepeatedTimer(1.0 / self.preferred_fps, doit)
        self.reset(False)
        effect_timer.start()
        return True

    def stop_rt(self):
        global effect_timer
        if effect_timer:
            effect_timer.cancel()
        effect_timer = None

    def make_movie(self, numframes):
        frames = []
        self.reset(numframes)
        for i in range(numframes):
            frames.append(self.getnext())
        return self.ctr.to_movie(frames)

    def launch_movie(self):
        self.stop_rt()
        self.ctr.show_movie(self.make_movie(self.preferred_frames),
                            self.preferred_fps)

    def save_movie(self, name):
        self.ctr.save_movie(name,
                            self.make_movie(self.preferred_frames),
                            self.preferred_fps)


def stop_rt():
    global effect_timer
    if effect_timer:
        effect_timer.cancel()
        effect_timer = None
