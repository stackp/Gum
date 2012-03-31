from gum.controllers import effect
from gum.models import sound

def replace_frames(sound, y):
    sound.frames = y

def monoize(sound, start, end):
    x = sound.frames
    y = sound.mix_channels_auto(sound.frames, 1)
    do = (replace_frames, [sound, y])
    undo = (replace_frames, [sound, x])
    sound.history.add(do, undo)
    sound.changed()

effect.effects['Monoize'] = monoize
