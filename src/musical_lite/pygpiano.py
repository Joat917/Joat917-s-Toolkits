import os, sys
import numpy as np
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
from musicallitelib import Synthesizer

WHITE_KEY_WIDTH = 36
WHITE_KEY_HEIGHT = 200
BLACK_KEY_WIDTH = 24
BLACK_KEY_HEIGHT = 120
HALF_KEY_GAP = 1

class PianoWhiteKey:
    def __init__(self, note_name:str, area:int, index:int, bound_keyname:str=''):
        self.note_base = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        self.note_name = note_name
        self.rect = pygame.Rect(index*WHITE_KEY_WIDTH, 0, WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
        assert self.note_name in self.note_base, f"Invalid note name: {note_name}"
        self.area = area
        self.key_down = False
        self.bound_keyname = bound_keyname
        assert isinstance(self.area, int) and 0 <= self.area <= 8, f"Invalid area: {area}"

    @property
    def key_name(self):
        return f"{self.note_name}{self.area}"

    @property
    def midi_note(self):
        return (self.area + 1) * 12 + self.note_base[self.note_name]
    
    def paint(self, surface:pygame.Surface):
        left_black = self.note_name in ('D', 'E', 'G', 'A', 'B')
        right_black = self.note_name in ('C', 'D', 'F', 'G', 'A')
        color = (255, 200, 0) if self.key_down else (255, 255, 255)
        pygame.draw.rect(
            surface, color, 
            pygame.Rect(
                self.rect.left + (BLACK_KEY_WIDTH//2 if left_black else 0) + HALF_KEY_GAP, 
                self.rect.top + HALF_KEY_GAP, 
                self.rect.width - (BLACK_KEY_WIDTH//2 if left_black else 0) - (BLACK_KEY_WIDTH//2 if right_black else 0) - 2*HALF_KEY_GAP, 
                self.rect.height - 2*HALF_KEY_GAP
            )
        )
        pygame.draw.rect(
            surface, color, 
            pygame.Rect(
                self.rect.left + HALF_KEY_GAP, 
                self.rect.top + BLACK_KEY_HEIGHT + HALF_KEY_GAP, 
                self.rect.width - 2*HALF_KEY_GAP,
                self.rect.height - BLACK_KEY_HEIGHT - 2*HALF_KEY_GAP
            )
        )

        text_surface = pygame.font.SysFont('Arial', 12).render(self.key_name, True, (0, 0, 0))
        surface.blit(text_surface, (self.rect.centerx - text_surface.get_width()//2, self.rect.bottom - text_surface.get_height() - 5))
        
        if not self.key_down:
            text_surface_key = pygame.font.SysFont('Arial', 12).render('/'.join(self.bound_keyname), True, (128, 100, 0))
            surface.blit(text_surface_key, (self.rect.centerx - text_surface_key.get_width()//2, self.rect.bottom - text_surface.get_height() - text_surface_key.get_height() - 5))

    
class PianoBlackKey:
    def __init__(self, note_name:str, area:int, index:int, bound_keyname:str=''):
        self.note_base = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
        self.note_name = note_name
        self.rect = pygame.Rect(index*WHITE_KEY_WIDTH + (WHITE_KEY_WIDTH - BLACK_KEY_WIDTH//2), 0, BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
        assert self.note_name in self.note_base, f"Invalid note name: {note_name}"
        self.area = area
        assert isinstance(self.area, int) and 0 <= self.area <= 8, f"Invalid area: {area}"
        self.key_down = False
        self.bound_keyname = bound_keyname

    @property
    def key_name(self):
        return f"{self.note_name}_{self.area}"

    @property
    def midi_note(self):
        return (self.area + 1) * 12 + self.note_base[self.note_name]
    
    def paint(self, surface:pygame.Surface):
        color = (128, 100, 0) if self.key_down else (0, 0, 0)
        pygame.draw.rect(
            surface, color, 
            pygame.Rect(
                self.rect.left + HALF_KEY_GAP, 
                self.rect.top + HALF_KEY_GAP, 
                self.rect.width - 2*HALF_KEY_GAP, 
                self.rect.height - 2*HALF_KEY_GAP
            )
        )
        if not self.key_down:
            text_surface_key = pygame.font.SysFont('Arial', 12).render('/'.join(self.bound_keyname), True, (255, 200, 0))
            surface.blit(text_surface_key, (self.rect.centerx - text_surface_key.get_width()//2, self.rect.bottom - text_surface_key.get_height() - 5))


class PyPiano:
    def __init__(self):
        self.synthesizer = Synthesizer(strategy='string')
        self.keys = []
        self.sounds = {}
        self.current_area = 4
        self.current_playing = set()
        self.clock = pygame.time.Clock()

        self.create_keys()
        # pygame.mixer.init()
        self.create_sounds()
        self.showing_help = False

    def play_sound(self, midi_note):
        self.current_playing.add(midi_note)
        if midi_note in self.sounds:
            self.sounds[midi_note].stop()
        # freq = self.synthesizer.midi_to_freq(midi_note)
        # sound_data = self.synthesizer.generate_wave(freq, duration_sec=5)
        # sound_data = np.broadcast_to(sound_data, (2, len(sound_data))).T
        # sound = pygame.sndarray.make_sound((sound_data * 32767).astype(np.int16))
        # self.sounds[midi_note] = sound
        self.sounds[midi_note].play()

    def stop_sound(self, midi_note, fadeout=0):
        if midi_note not in self.sounds:
            return
        try:
            self.current_playing.remove(midi_note)
            self.sounds[midi_note].fadeout(fadeout)
        except KeyError:
            pass

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                for key in self.keys:
                    if pygame.key.name(event.key).upper() in key.bound_keyname:
                        if key.key_down:
                            continue
                        key.key_down = True
                        self.play_sound(key.midi_note)
                if event.key in [pygame.K_LALT, pygame.K_LEFT]:
                    self.change_area(-1)
                elif event.key in [pygame.K_RALT, pygame.K_RIGHT]:
                    self.change_area(1)
            elif event.type == pygame.KEYUP:
                for key in self.keys:
                    if pygame.key.name(event.key).upper() in key.bound_keyname:
                        key.key_down = False
                        self.stop_sound(key.midi_note, fadeout=200 if not pygame.key.get_pressed()[pygame.K_RSHIFT] else 1500)
                if event.key == pygame.K_RSHIFT:
                     for sound in self.sounds.values():
                         sound.stop()
        if not hasattr(self, 'unbound_keys'):
            self.unbound_keys = {chr(i) for i in range(97, 123)}  # A-Z
            self.unbound_keys.update({str(i) for i in range(10)})  # 0-9
            self.unbound_keys.update('`-=[]\\;\',./')
            for key in self.keys:
                for bound_key in key.bound_keyname:
                    self.unbound_keys.discard(bound_key.lower())
        if all((not k.key_down) for k in self.keys) and any(pygame.key.get_pressed()[pygame.key.key_code(k)] for k in self.unbound_keys):
            self.showing_help = True
        else:
            self.showing_help = False
        return True
    
    def create_keys(self):
        key_bindings = {
            'Z': ('C', 0), 'S': ('C#', 0), 'X': ('D', 0), 'D': ('D#', 0), 'C': ('E', 0),
            'V': ('F', 0), 'G': ('F#', 0), 'B': ('G', 0), 'H': ('G#', 0), 'N': ('A', 0),
            'J': ('A#', 0), 'M': ('B', 0), ',': ('C', 1), 'L': ('C#', 1), '.': ('D', 1), ';': ('D#', 1), '/': ('E', 1),
            'Q': ('C', -1), '2': ('C#', -1), 'W': ('D', -1), '3': ('D#', -1), 'E': ('E', -1),
            'R': ('F', -1), '5': ('F#', -1), 'T': ('G', -1), '6': ('G#', -1), 'Y': ('A', -1),
            '7': ('A#', -1), 'U': ('B', -1),  'I': ('C', 0), '9': ('C#', 0), 'O': ('D', 0), 
            '0': ('D#', 0), 'P': ('E', 0), '[': ('F', 0), '=': ('F#', 0), ']': ('G', 0), 
            # Add more bindings as needed
        }
        white_keys = sorted(
            {(note, area) for note, area in key_bindings.values() if '#' not in note}, 
            key=lambda x: (x[1], 'CDEFGAB'.index(x[0].replace('#', '')))
        )
        white_key_binded = {key_info: tuple(key for key,info in key_bindings.items() if info == key_info) for key_info in white_keys}
        white_key_indexes = {key_info: idx for idx, key_info in enumerate(white_keys)}
        black_keys = sorted(
            [(note, area) for note, area in key_bindings.values() if '#' in note], 
            key=lambda x: (x[1], 'CDEFGAB'.index(x[0].replace('#', '')))
        )
        black_key_binded = {key_info: tuple(key for key,info in key_bindings.items() if info == key_info) for key_info in black_keys}
        black_key_indexes = {(note, area): white_key_indexes.get((note.replace('#', ''), area), None) for note, area in black_keys}
        for (note, area), idx in white_key_indexes.items():
            self.keys.append(PianoWhiteKey(note, self.current_area+area, idx, bound_keyname=''.join(white_key_binded.get((note, area), ()))))
        for (note, area), idx in black_key_indexes.items():
            if idx is not None:
                self.keys.append(PianoBlackKey(note, self.current_area+area, idx, bound_keyname=''.join(black_key_binded.get((note, area), ()))))
    
    def create_sounds(self):
        pygame.mixer.init()
        for midi_note in set(key.midi_note for key in self.keys).difference(self.sounds.keys()):
            freq = self.synthesizer.midi_to_freq(midi_note)
            sound_data = self.synthesizer.generate_wave(freq, duration_sec=5)
            amplitude = np.max(np.abs(sound_data))
            sound_data = np.broadcast_to(sound_data, (2, len(sound_data))).T * 32767 / amplitude if amplitude > 0 else sound_data
            sound = pygame.sndarray.make_sound(sound_data.astype(np.int16))
            self.sounds[midi_note] = sound

    def change_area(self, delta):
        old_area = self.current_area
        self.current_area = max(1, min(7, self.current_area + delta))
        if self.current_area == old_area:
            return
        for key in self.keys:
            key.area = self.current_area + (key.area - old_area)
        self.create_sounds()

    def paint_keyboard(self):
        self.screen.fill((200, 200, 200))
        for key in self.keys:
            key.paint(self.screen)

    def paint_help(self):
        help_text = [
            "PyPiano - A Simple Virtual Piano",
            "Press corresponding keys to play notes. Mouse clicking is not supported.",
            "Hold Left Alt to shift down an octave, Right Alt to shift up an octave.",
            "Hold Right Shift for sustain pedal effect.", 
            "Hold any unbound key to show this help message.",
        ]
        self.screen.fill((137, 171, 205))
        for idx, line in enumerate(help_text):
            text_surface = pygame.font.SysFont('Arial', 16).render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (20, 20 + idx * 30))


    def run(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WHITE_KEY_WIDTH * 17, WHITE_KEY_HEIGHT))
        pygame.display.set_caption("PyPiano")
        running = True
        refresh_countdown = 0
        while running:
            self.clock.tick(200)
            running = self.event_loop()
            if refresh_countdown <=0:
                if self.showing_help:
                    self.paint_help()
                else:
                    self.paint_keyboard()
                pygame.display.flip()
                refresh_countdown = 5
            else:
                refresh_countdown -= 1
        pygame.quit()

if __name__ == "__main__":
    piano = PyPiano()
    piano.run()
    


