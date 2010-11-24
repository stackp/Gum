from scalpel.effect import effects
import scalpel.edit

def replace_frames(sound, y):
    sound.frames = y

def monoize(sound, start, end):
    x = sound.frames
    y = scalpel.edit.mix_channels_auto(sound.frames, 1)
    do = (replace_frames, [sound, y])
    undo = (replace_frames, [sound, x])
    sound.history.add(do, undo)
    sound.changed()

effects['Monoize'] = monoize
