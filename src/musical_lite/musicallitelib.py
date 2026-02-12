import os
import sys
import time
import subprocess
import numpy as np


class Converter:
    """Class for converting audio files between formats."""

    @staticmethod
    def mp3_to_wav(mp3_path, wav_path):
        """Convert MP3 file to WAV file using ffmpeg."""
        command = [
            'ffmpeg',
            '-i', mp3_path,
            '-ar', '44100',  # Set audio sample rate to 44100 Hz
            '-ac', '2',       # Set number of audio channels to 2 (stereo)
            '-b:a', '192k',   # Set audio bitrate to 192 kbps
            '-f', 'wav',
            wav_path
        ]
        return subprocess.run(command, check=True)

    @staticmethod
    def wav_to_mp3(input_wav, output_mp3, bitrate="192k", quality="0"):
        """
        使用ffmpeg将WAV转换为MP3
        :param input_wav: 输入的WAV文件路径
        :param output_mp3: 输出的MP3文件路径
        :param bitrate: MP3的比特率(默认为"192k")
        """
        command = [
            "ffmpeg",
            "-i", input_wav,
            "-codec:a", "libmp3lame",
            "-q:a", quality,  # 质量参数(0-9，0最好)
            "-b:a", bitrate,
            output_mp3
        ]
        return subprocess.run(command, check=True)

    @staticmethod
    def video_to_mp3(video_path, mp3_path, quality="0"):
        """
        使用ffmpeg将视频文件转换为MP3音频文件
        :param video_path: 输入的视频文件路径
        :param mp3_path: 输出的MP3文件路径
        :param quality: MP3的质量参数(默认为"0"，范围0-9，0最好)
        """
        command = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # 不处理视频流
            "-q:a", quality,  # 质量参数(0-9，0最好)
            "-map", "a",  # 选择所有音频流
            mp3_path
        ]
        return subprocess.run(command, check=True)

    @staticmethod
    def read_audio_data(file_path):
        """
        读取一个音频文件

        :param file_path: 音频文件路径
        :return: pydub.AudioSegment对象
        """
        import pydub
        ext = os.path.splitext(file_path)[1].lower()
        ret = pydub.AudioSegment.from_file(file_path, format=ext[1:])
        assert isinstance(ret, pydub.AudioSegment), "Failed to read audio data"
        return ret
    
    @staticmethod
    def save_audio_data(
        time_series_data, 
        output_path,
        sample_rate=44100,
        format="mp3",
        title=None, 
        artist=None,
        album=None,
        cover_image_path=None
    ):
        """
        保存音频数据到文件
        :param time_series_data: 音频时间序列数据 (numpy ndarray)
        :param output_path: 输出文件路径
        :param sample_rate: 采样率 (默认: 44100)
        :param format: 输出音频格式 (默认: "mp3")
        :param title: 音频标题 (可选)
        :param artist: 艺术家名称 (可选)
        :param album: 专辑名称 (可选)
        :param cover_image_path: 封面图片路径 (可选)
        :return: None
        """
        import pydub
        if not isinstance(time_series_data, np.ndarray):
            raise ValueError("time_series_data must be a numpy ndarray")
        if not np.issubdtype(time_series_data.dtype, np.integer):
            raise ValueError("time_series_data must be of integer type")
        audio_segment = pydub.AudioSegment(
            time_series_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=time_series_data.dtype.itemsize,
            channels=1 if len(time_series_data.shape) == 1 else time_series_data.shape[1]
        )
        if title or artist or album:
            tags = {
                "title": title,
                "artist": artist,
                "album": album
            }
        else:
            tags = None
        if cover_image_path:
            cover = cover_image_path
        else:
            cover = None
        return audio_segment.export(
            output_path,
            format=format,
            tags=tags,
            cover=cover
        )


class Synthesizer:
    "波形合成器"
    def __init__(self, strategy = None, sample_rate=44100):
        """
        Args:
            strategy: 实现了 ISoundStrategy 的对象。默认为 StringStrategy。
        """
        self.sample_rate = sample_rate
        
        if strategy is None:
            self.strategy = 'square' # 默认使用8bit方波音色
        else:
            self.strategy = strategy

        self.decay_factor = 0.996  # 用于 Karplus-Strong 算法的衰减因子

    @staticmethod
    def generate_wave_string_strategy(freq, duration_sec, sample_rate=44100, decay_factor=0.996):
        """
        【物理建模】Karplus-Strong 算法。
        模拟拨弦乐器（吉他/古琴/古钢琴）。
        """
        N = int(sample_rate * duration_sec)
        if freq <= 0: return np.zeros(N)
        
        period = int(sample_rate / freq)
        assert period > 0, "Frequency too high for the given sample rate."
        assert N > period, "Duration too short for the given frequency."

        decay_factor **= 440/freq  # 根据频率调整衰减，使得高频音不会过快消失
        
        output = np.zeros(N)
        output[:period] = np.random.randn(period)
        for i in range(period, N):
            output[i] = decay_factor * 0.5 * (output[i - period] + output[i - period - 1])

        return output
    
    @staticmethod
    def generate_wave_sine_strategy(freq, duration_sec, sample_rate=44100):
        """
        【加法合成】正弦波 + 泛音 + ADSR 包络。
        听起来像简单的电子琴或风琴。
        """
        N = int(sample_rate * duration_sec)
        if freq <= 0: return np.zeros(N)

        t = np.arange(N) / sample_rate
        omega = 2 * np.pi * freq
        wave = 0.6 * np.sin(omega * t)
        wave += 0.3 * np.sin(omega * 2 * t) # 二次泛音
        wave += 0.1 * np.sin(omega * 3 * t) # 三次泛音
        
        # ADSR 包络 (防止噼里啪啦的爆音)
        attack = int(0.02 * sample_rate)
        release = int(0.1 * sample_rate)
        envelope = np.ones_like(wave)
        if N > attack > 0:
            envelope[:attack] = np.linspace(0, 1, attack)
        if N > release > 0:
            envelope[-release:] = np.linspace(1, 0, release)
            
        return wave * envelope
    
    @staticmethod
    def generate_wave_square_strategy(freq, duration_sec, sample_rate=44100):
        """
        【8-bit 风格】方波。
        听起来像任天堂 FC / NES 游戏机。
        """
        N = int(sample_rate * duration_sec)
        if freq <= 0: return np.zeros(N)

        t = np.arange(N) / sample_rate
        omega = 2 * np.pi * freq
        wave = 0.5 * np.sign(np.sin(omega * t))
        
        # 简单的 Decay 包络，让它有点打击感
        decay = np.exp(-np.linspace(0,2,N))
        
        return wave * decay
    
    @property
    def strategy(self):
        return self._strategy
    
    @strategy.setter
    def strategy(self, value):
        if isinstance(value, str):
            if value == 'string':
                self._strategy = 'string'
                self._strategy_func = lambda freq, duration_sec, sample_rate=self.sample_rate: self.generate_wave_string_strategy(freq, duration_sec, sample_rate, decay_factor=self.decay_factor)
            elif value == 'sine':
                self._strategy = 'sine'
                self._strategy_func = self.generate_wave_sine_strategy
            elif value == 'square':
                self._strategy = 'square'
                self._strategy_func = self.generate_wave_square_strategy
            else:
                raise ValueError(f"Unknown strategy string: {value}")
        elif callable(value):
            self._strategy = value.__name__
            self._strategy_func = value
        else:
            raise ValueError("Strategy must be a string or a callable function.")

    def generate_wave(self, freq, duration_sec):
        """
        生成指定频率和持续时间的音频波形数据。
        Args:
            freq: 频率 (Hz)
            duration_sec: 持续时间 (秒)
        Returns:
            numpy ndarray: 生成的音频波形数据
        """
        return self._strategy_func(freq, duration_sec, sample_rate=self.sample_rate)
    
    @staticmethod
    def midi_to_freq(midi_note:int):
        """将 MIDI 音符转换为频率 (Hz)。"""
        return 440.0 * (2 ** ((midi_note - 69) / 12))


class NotePlayerBase:
    """Base class for playing musical notes."""
    def play_note(self, midi_note:int, duration_beats:float=1.0):
        """Play a musical note.
        Args:
            midi_note: MIDI note number (0-127)
            duration_beats: Duration of the note in beats
        """
        raise NotImplementedError("Subclasses must implement play_note method.")
    
    def rest(self, duration_beats:float=1.0):
        """Rest for a specified duration.
        Args:
            duration_beats: Duration of the rest in beats
        """
        raise NotImplementedError("Subclasses must implement rest method.")


class BeepPlayer(NotePlayerBase):
    def __init__(self, bpm=120):
        self.bpm = bpm
        import winsound
        self.winsound = winsound

    def play_note(self, midi_note, duration_beats = 1):
        freq = round(Synthesizer.midi_to_freq(midi_note))
        duration_ms = round(60_000 * duration_beats / self.bpm)
        self.winsound.Beep(freq, duration_ms)

    def rest(self, duration_beats = 1):
        sleep_time = 60 * duration_beats / self.bpm
        time.sleep(sleep_time)

class MidoPlayer(NotePlayerBase):
    def __init__(self, bpm=120):
        self.bpm = bpm
        import mido
        self.mido = mido
        self.port = mido.open_output()

    def play_note(self, midi_note, duration_beats = 1):
        msg_on = self.mido.Message('note_on', note=midi_note, velocity=64)
        msg_off = self.mido.Message('note_off', note=midi_note, velocity=64)
        self.port.send(msg_on)
        sleep_time = 60 * duration_beats / self.bpm
        time.sleep(sleep_time)
        self.port.send(msg_off)

    def rest(self, duration_beats = 1):
        sleep_time = 60 * duration_beats / self.bpm
        time.sleep(sleep_time)

class PygamePlayer(NotePlayerBase):
    def __init__(self, bpm=120, synth_strategy='square'):
        self.bpm = bpm
        self.synthesizer = Synthesizer(strategy=synth_strategy)
        import pygame
        pygame.mixer.init()
        self.pygame = pygame

    def play_note(self, midi_note, duration_beats = 1):
        freq = Synthesizer.midi_to_freq(midi_note)
        duration_ms = round(60_000 * duration_beats / self.bpm)
        wave_data = self.synthesizer.generate_wave(freq, duration_ms / 1000.0)
        wave_data_int16 = np.int16(wave_data * 32767)
        sound = self.pygame.sndarray.make_sound(wave_data_int16)
        sound.play()
        self.pygame.time.delay(duration_ms)

    def rest(self, duration_beats = 1):
        sleep_time_ms = round(60_000 * duration_beats / self.bpm)
        self.pygame.time.delay(sleep_time_ms)


class BPMDetectors:
    @staticmethod
    def get_bpm_simple(time_sequence):
        return 60 * (len(time_sequence)-1) / (time_sequence[-1] - time_sequence[0])
    
    @staticmethod
    def get_bpm_regression(time_sequence):
        from scipy.stats import linregress
        if len(time_sequence) <= 1:
            return 0.0
        x = np.arange(len(time_sequence))
        slope, intercept, r_value, p_value, std_err = linregress(x, time_sequence)
        return (60/slope, 60*std_err/slope**2)
    
    @staticmethod
    def get_bpm_fft(time_sequence, density=1000, kernel_width=0.1):
        time_data = np.linspace(time_sequence[0], time_sequence[-1], len(time_sequence)*1000)
        value_data = np.zeros_like(time_data)
        for t in time_sequence:
            value_data += np.exp(-0.5 * ((time_data - t) / kernel_width)**2)  # Gaussian kernel
        freqs = np.fft.rfftfreq(len(time_data), d=(time_data[1]-time_data[0]))
        spectrum = np.abs(np.fft.rfft(value_data))
        spectrum[0] = 0  # 去除直流分量
        peak_freq = freqs[np.argmax(spectrum)]
        return peak_freq * 60  # Convert to BPM
    
    def run_console(self):
        self.records = []
        self.start_time = time.perf_counter()
        import msvcrt
        while True:
            os.system('cls')
            print("回车以记录，按下C键以清空记录，按下X键以退出。")
            while True:
                c = msvcrt.getch()
                if c in [b'\000', b'\xe0']:
                    msvcrt.getch()
                if c in [b'\r', b'\n', b' ']:
                    self.records.append(time.perf_counter() - self.start_time)
                    if len(self.records) <= 1:
                        print("继续...")
                    else:
                        result_simple = self.get_bpm_simple(self.records)
                        result_reg, std_reg = self.get_bpm_regression(self.records)
                        result_fft = self.get_bpm_fft(self.records)
                        result_fft /= max(round(result_fft/result_simple), 1)
                        print("BPM是：{:.02f}±{:.02f} / {:.02f}±{:.02f} / {:.02f}".format(
                            result_simple, 0.1/len(self.records),
                            result_reg, std_reg,
                            result_fft, 
                        ))
                elif c in [b'c']:
                    self.records.clear()
                    break
                elif c in [b'x']:
                    return

class Spectrogram:
    def __init__(self, audio_data, sample_rate, nperseg=4096, noverlap=3072):
        from scipy.signal import stft
        self.audio_data = audio_data
        self.max_audio_value = np.max(np.abs(audio_data)).astype(np.float64)
        self.sample_rate = sample_rate
        self.freqs, self.times, self.Zxx = stft(audio_data, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)
        self.magnitudes = np.abs(self.Zxx) # unit: amplitude * Hz^-0.5
        self.magnitudes_normalized = self.magnitudes / self.max_audio_value * np.sqrt(self.freqs[1]-self.freqs[0])
        self.magnitude_per_segment = np.sqrt(np.mean(self.magnitudes_normalized * self.magnitudes_normalized, axis=0))
        

    def hps(self, segment_idx, n_harmonics=5):
        # 计算信号的FFT
        min_freq_index = self.freqs.searchsorted(20)
        max_freq_index = self.freqs.searchsorted(2000)
        spectrum = self.magnitudes[:, segment_idx]
        if np.mean(self.magnitudes_normalized[min_freq_index:max_freq_index, segment_idx]**2) < 0.1:
            return np.nan
        
        # 初始化HPS结果为原始频谱
        hps_result = np.copy(spectrum)
        
        # 执行谐波乘积
        for i in range(2, n_harmonics + 1):
            decimated_spectrum = spectrum[::i]  # 对频谱进行降采样
            # 确保长度匹配，必要时截断或填充
            if len(decimated_spectrum) < len(hps_result):
                decimated_spectrum = np.concatenate([decimated_spectrum, np.zeros(len(hps_result) - len(decimated_spectrum))])
            elif len(decimated_spectrum) > len(hps_result):
                decimated_spectrum = decimated_spectrum[:len(hps_result)]
            
            hps_result *= decimated_spectrum
        
        # 查找HPS峰值以估计基频
        
        peak_index = np.argmax(hps_result[min_freq_index:max_freq_index])
        fundamental_freq = self.freqs[peak_index]
        
        return fundamental_freq
    
    def plot_spectrogram(self):
        # Plot the STFT spectrum
        import matplotlib.axes
        import matplotlib.pyplot as plt
        fig, (ax1, ax2)=plt.subplots(2,1)
        ax1:matplotlib.axes.Axes
        ax2:matplotlib.axes.Axes
        freqs_data = self.freqs[self.freqs<2000]
        print(len(freqs_data), self.times[1]-self.times[0])
        magnitude_data = self.magnitudes_normalized[:len(freqs_data), :3000]
        magnitude_data = np.where(magnitude_data>0.1, 10*np.log10(magnitude_data), -10.1+magnitude_data)
        qm=ax1.pcolormesh(self.times[:3000], freqs_data, magnitude_data, shading='gouraud')
        ax1.set_title('Short-Time Frequency Spectrum')
        ax1.set_ylabel('Frequency [Hz]')
        ax1.set_xlabel('Time [sec]')
        fig.colorbar(qm, label='Magnitude')

        ax2.plot(self.times, self.magnitude_per_segment)
        ax2.set_title('Magnitude-Time Plot')
        ax2.set_ylabel('Magnitude')
        ax2.set_xlabel('Time [sec]')

        plt.tight_layout()
        plt.show()
