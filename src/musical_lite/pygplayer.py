import os, sys
import numpy as np
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
from musicallitelib import Converter, Spectrogram, Spectrogram2

FPS=60
MAX_DB = 50
ICON_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icon.png')

class PyGPlayer:
    def __init__(self, audio_file):
        pygame.mixer.init()
        self.audio_file = audio_file
        self.sound = pygame.mixer.Sound(audio_file)

        self.channel = None
        self.is_playing = False
        self.playing_start_time = None
        self.playing_last_time = None

        self.audio_segment = Converter.read_audio_data(audio_file)
        self.spectrogram = Spectrogram(np.mean(np.asarray(self.audio_segment.get_array_of_samples()).reshape(-1, self.audio_segment.sample_width),axis=1), self.audio_segment.frame_rate)
        
        # self.bins_count = 64
        # bin_edges = [20]
        # freq_index = 0
        # while len(bin_edges)<=self.bins_count:
        #     next_edge = (20000/bin_edges[-1])**(1/(self.bins_count-len(bin_edges)+1))*bin_edges[-1]
        #     bin_edges.append(max(next_edge, self.spectrogram.freqs[freq_index]*(1+1e-7)))
        #     while self.spectrogram.freqs[freq_index]<bin_edges[-1]:
        #         freq_index+=1
        # self.bin_edges = np.array(bin_edges)
        # print(self.bin_edges)
        # print(self.spectrogram.freqs[1]-self.spectrogram.freqs[0])

        # bin_edges = []
        # mido_freqs = [440*2**((i-69)/12) for i in range(128)]
        # mido_index = 0
        # while mido_freqs[mido_index]<20:
        #     mido_index+=1
        # while mido_freqs[mido_index]<5000:
        #     bin_edges.append(np.sqrt(mido_freqs[mido_index]*mido_freqs[mido_index+1]))
        #     mido_index+=1
        # bin_edges.append(20000)
        # i=1
        # while i<len(bin_edges)-1:
        #     if not np.any((self.spectrogram.freqs >= bin_edges[i]) & (self.spectrogram.freqs < bin_edges[i+1])):
        #         bin_edges.pop(i)
        #     else:
        #         i+=1
        # self.bin_edges = np.array(bin_edges)
        # self.bins_count = len(self.bin_edges)-1

        self.bin_freqs = np.concatenate([np.arange(22, 46+1, 1), np.array([440*2**((i/4-69)/12) for i in range(32*4,128*4)])])
        self.bin_edges = np.concatenate([np.arange(20, 44+1, 1), np.array([440*2**(((i-0.5)/4-69)/12) for i in range(32*4,128*4+1)])])

        # self.bin_freqs = np.concatenate([np.arange(22, 46+1, 4), np.array([440*2**((i-69)/12) for i in range(32,128)])])
        # self.spectrogram = Spectrogram2(np.mean(np.asarray(self.audio_segment.get_array_of_samples()).reshape(-1, self.audio_segment.sample_width),axis=1), self.audio_segment.frame_rate, self.bin_freqs)
        # self.bin_edges = np.concatenate([np.arange(20, 44+1, 4), np.array([440*2**(((i-0.5)-69)/12) for i in range(32,128+1)])])
        self.bins_count = len(self.bin_freqs)
        self.magnitudes_cache = np.zeros((self.bins_count, len(self.spectrogram.times)), dtype=np.float64)
        for i in range(self.bins_count):
            self.magnitudes_cache[i] = self.spectrogram.get_magnitude_at(self.bin_freqs[i])

        self.bins_heights = np.zeros(self.bins_count, dtype=np.float64)
        self.line_color = (128, 128, 128)
        
    def play(self):
        if not self.is_playing:
            self.channel = self.sound.play()
            self.is_playing = True
            self.playing_start_time = pygame.time.get_ticks()

    def pause(self):
        if self.is_playing:
            self.channel.pause()
            self.is_playing = False
            self.playing_last_time = pygame.time.get_ticks() - self.playing_start_time
            self.playing_start_time = None
        else:
            raise RuntimeError("Cannot pause when not playing")

    def unpause(self):
        if not self.is_playing and self.channel is not None:
            self.channel.unpause()
            self.is_playing = True
            self.playing_start_time = pygame.time.get_ticks() - self.playing_last_time
            self.playing_last_time = None
        elif self.channel is not None:
            raise RuntimeError("Cannot unpause when not paused")
        else:
            raise RuntimeError("Cannot unpause when not started")

    def stop(self):
        if self.channel is not None:
            self.channel.stop()
        self.is_playing = False
        self.playing_start_time = None
        self.playing_last_time = None
        self.channel = None

    # def get_magnitude_data(self, segment_index):
    #     magnitude_data = self.spectrogram.magnitudes_normalized[:, segment_index]
    #     magnitude_binned = np.zeros(self.bins_count, dtype=np.float64)
    #     for i in range(self.bins_count):
    #         magnitude_binned[i] = np.max(magnitude_data[(self.spectrogram.freqs >= self.bin_edges[i]) & (self.spectrogram.freqs < self.bin_edges[i+1])])
    #     return magnitude_binned
    def get_magnitude_data(self, segment_index):
        return self.magnitudes_cache[:, segment_index]

    def paint(self, surface:pygame.Surface, height_ratio=1.0):
        # 绘制频谱
        if self.is_playing:
            elapsed_time = pygame.time.get_ticks() - self.playing_start_time
        elif self.playing_last_time is not None:
            elapsed_time = self.playing_last_time
        else:
            self._paint_spectrogram_2d(surface, self.spectrogram.times[0], height_ratio)
            self._paint_grid(surface)
            self._paint_UI(surface)
            return
        if elapsed_time/1000 >= self.spectrogram.times[-1]:
            self.stop()
            self._paint_spectrogram_2d(surface, self.spectrogram.times[-1], height_ratio)
            self._paint_grid(surface)
            self._paint_UI(self.screen)
            return
        self._paint_spectrogram_2d(surface, elapsed_time, height_ratio)
        self._paint_grid(surface)
        self._paint_UI(surface)

    @staticmethod
    def _freq_to_midi_string(freq:float):
        if freq<=0:
            return "N/A"
        midi_num = 69 + 12*np.log2(freq/440)
        midi_index = round(midi_num*4)/4
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_name = note_names[int(midi_index)%12]
        octave = int(midi_index//12)-1
        if abs(midi_index - round(midi_index))<0.01:
            return f"{note_name}{octave}"
        elif midi_index - round(midi_index)>0:
            return f"{note_name}{octave}+{round((midi_index - round(midi_index))*100)}'"
        else:
            return f"{note_name}{octave}-{round((round(midi_index)-midi_index)*100)}'"

    def _paint_grid(self, surface:pygame.Surface):
        # 绘制鼠标指针位置对应的频率
        if pygame.mouse.get_focused():
            mouse_x, _ = pygame.mouse.get_pos()
            current_bin_index = min(max(int(mouse_x/surface.get_width()*self.bins_count), 0), self.bins_count-1)
            pygame.draw.rect(
                surface, 
                (0, 64, 192), 
                (
                    round(current_bin_index/self.bins_count*surface.get_width()), 
                    0,
                    round(surface.get_width()/self.bins_count),
                    surface.get_height()
                )
            )
            text_surface = pygame.font.SysFont("Arial", 12).render(
                # f"{round(self.bin_edges[current_bin_index])}Hz ~ {round(self.bin_edges[current_bin_index+1])}Hz", 
                f"{round(self.bin_freqs[current_bin_index])}Hz({self._freq_to_midi_string(self.bin_freqs[current_bin_index])})", 
                True, (255, 255, 255)
            )
            surface.blit(
                text_surface, 
                (min(mouse_x+10, surface.get_width()-text_surface.get_width()-10), 100)
            )

            # 绘制频率标尺
            sep = self.bins_count//16
            for i in range(0, self.bins_count, sep)[1:]:
                pygame.draw.line(
                    surface,
                    self.line_color,
                    (round(i/self.bins_count*surface.get_width()), 0),
                    (round(i/self.bins_count*surface.get_width()), surface.get_height()),
                    1
                )
                surface.blit(
                    pygame.font.SysFont("Arial", 12).render(f"{round(self.bin_edges[i])}Hz", True, (255, 255, 255)),
                    (round(i/self.bins_count*surface.get_width())+2, 20)
                )
        
    def _paint_spectrogram(self, surface:pygame.Surface, elapsed_time, height_ratio=1.0, swiftness=20.0):
        current_segment_index = self.spectrogram.times.searchsorted(elapsed_time/1000)
        freq_binned = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        magnitude_binned = self.get_magnitude_data(current_segment_index)
        
        magnitude_in_dB = 20 * np.log10(magnitude_binned + 1e-7)
        magnitude_in_dB = np.where(np.isfinite(magnitude_in_dB), magnitude_in_dB, -60)  # 将非数替换为-60dB
        magnitude_in_dB = np.clip(magnitude_in_dB, -MAX_DB, 0)  # 限制在-60dB到0dB之间
        magnitude_ratio = magnitude_in_dB/MAX_DB+1
        delta_bin_heights = (1-0.5**(swiftness/FPS))*(magnitude_ratio - self.bins_heights)
        delta_bin_heights = np.where(
            delta_bin_heights<0, 
            np.minimum(
                -np.maximum(1,np.log10(self.bin_freqs)/2)/FPS, 
                delta_bin_heights
            ),
            delta_bin_heights
        )
        self.bins_heights = np.clip(self.bins_heights + delta_bin_heights, 0, 1)

        for i in range(self.bins_count):
            left = round(i/len(freq_binned)*surface.get_width())
            bottom = round(surface.get_height())
            width = round(surface.get_width()/len(freq_binned))
            height = round(self.bins_heights[i]*surface.get_height()*height_ratio)
            lightness = self.bins_heights[i]**2
            pygame.draw.rect(
                surface,
                # (
                #     round(min(magnitude_ratio[i]*2*255, 255) * lightness), 
                #     round(min((1-magnitude_ratio[i])*255*2, 255) * lightness),
                #     round(64 * lightness)
                # ),
                (
                    round(192 * magnitude_ratio[i] * lightness), 
                    round(192 * lightness),
                    round(64 * lightness)
                ),
                (left, bottom-height, width, height)
            )

    def _paint_UI(self, surface:pygame.Surface):
        # 绘制音频文件名
        audio_name = os.path.basename(self.audio_file)
        if all(32<=ord(c)<127 for c in audio_name):
            font = pygame.font.SysFont("Arial", 20)
        else:
            font = pygame.font.SysFont("SimHei", 20)
        surface.blit(
            font.render(audio_name, True, (255, 255, 255)),
            (10, 10)
        )

        # 绘制播放状态
        if self.is_playing:
            surface.blit(
                pygame.font.SysFont("Arial", 20).render("Playing", True, (0, 255, 0)),
                (10, 40)
            )
        elif self.playing_last_time is not None:
            surface.blit(
                pygame.font.SysFont("Arial", 20).render("Paused", True, (255, 255, 0)),
                (10, 40)
            )
        else:
            surface.blit(
                pygame.font.SysFont("Arial", 20).render("Stopped", True, (255, 0, 0)),
                (10, 40)
            )
        # 绘制当前时间
        if self.is_playing:
            elapsed_time = pygame.time.get_ticks() - self.playing_start_time
        elif self.playing_last_time is not None:
            elapsed_time = self.playing_last_time
        else:
            elapsed_time = 0
        total_time = round(self.spectrogram.times[-1]*1000)
        surface.blit(
            pygame.font.SysFont("Arial", 20).render(f"{elapsed_time//60000:02}:{(elapsed_time//1000)%60:02} / {total_time//60000:02}:{(total_time//1000)%60:02}", True, (255, 255, 255)),
            (10, 70)
        )

    def _paint_spectrogram_2d(self, surface:pygame.Surface, elapsed_time, height_ratio=1.0):
        import cv2
        self.line_color = (255, 255, 255)
        elapsed_time/=1000
        time_range = elapsed_time-5, elapsed_time+5
        segment_indices = np.where((self.spectrogram.times >= time_range[0]) & (self.spectrogram.times <= time_range[1]))[0]
        assert len(segment_indices)>0, "No spectrogram data in the specified time range."
        magnitude_data = np.array([self.get_magnitude_data(i) for i in segment_indices])
        magnitude_in_dB = 20 * np.log10(magnitude_data + 1e-7)
        magnitude_in_dB = np.where(np.isfinite(magnitude_in_dB), magnitude_in_dB, -60)  # 将非数替换为-60dB
        magnitude_in_dB = np.clip(magnitude_in_dB, -MAX_DB, 0)  # 限制在-60dB到0dB之间
        magnitude_ratio = magnitude_in_dB/MAX_DB+1 # height/axis0: frequency, width/axis1: time
        magnitude_ratio = magnitude_ratio.transpose()[:,::-1] # height: time(top:new, bottom:old), width: frequency
        picture_colored = np.stack([
            magnitude_ratio**3*255, 
            magnitude_ratio**2*192,
            magnitude_ratio**2*64
        ], axis=-1).astype(np.uint8)
        DY = (1-height_ratio)*surface.get_height()
        TY = height_ratio*surface.get_height()
        height = round(len(segment_indices)*(self.spectrogram.times[1]-self.spectrogram.times[0])/ (time_range[1]-time_range[0]) * TY)
        y_offset = round(max((time_range[1]-self.spectrogram.times[-1])/(time_range[1]-time_range[0]), 0)*TY+DY)
        picture_colored = cv2.resize(picture_colored, (height, surface.get_width()), interpolation=cv2.INTER_LINEAR)
        picture_surface = pygame.surfarray.make_surface(picture_colored)
        surface.blit(picture_surface, (0, y_offset))

        pygame.draw.line(
            surface,
            self.line_color,
            (0, round((time_range[1]-elapsed_time)/(time_range[1]-time_range[0])*TY+DY)),
            (surface.get_width(), round((time_range[1]-elapsed_time)/(time_range[1]-time_range[0])*TY+DY)),
            1
        )
        

    def event_handler(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.is_playing:
                    self.pause()
                elif self.channel is not None:
                    self.unpause()
                else:
                    self.play()
            elif event.key == pygame.K_s:
                self.stop()
        elif event.type == pygame.QUIT:
            self.stop()
            pygame.quit()
            sys.exit()
        elif event.type == pygame.DROPFILE:
            dropped_file = event.file
            if os.path.isfile(dropped_file):
                self.stop()
                self.screen.fill((0, 0, 0))
                text_surface = pygame.font.SysFont("Arial", 30).render("Loading...", True, (255, 255, 255))
                self.screen.blit(text_surface, ((self.screen.get_width()-text_surface.get_width())//2, (self.screen.get_height()-text_surface.get_height())//2))
                pygame.display.flip()
                self.__init__(dropped_file)
    
    def run(self):
        pygame.init()
        pygame.display.set_caption("Musical Lite Player")
        pygame.display.set_icon(pygame.image.load(ICON_PATH))
        self.screen = screen = pygame.display.set_mode((800, 600))
        self.clock = clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                self.event_handler(event)

            screen.fill((0, 0, 0))
            self.paint(screen)
            pygame.display.flip()
            clock.tick(FPS)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PyGPlayer - A simple audio player with spectrogram visualization")
    parser.add_argument("audio_file", nargs='?', default=None, help="Path to the audio file to play")
    args = parser.parse_args()
    assert args.audio_file is not None, "Please provide an audio file to play."
    player = PyGPlayer(args.audio_file)
    player.run()
