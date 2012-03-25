from gum.controllers import effect
from gum.views import EffectDialog

volume_last = 100

def volume(sound, start, end):

    def process(volume):
        gain = volume / 100.
        x = sound.frames[start:end]
        y = x * gain
        sound.paste(start, end, y)

    def callback(parameters):
        global volume_last
        volume = parameters['Volume']
        volume_last = volume
        process(volume)

    global volume_last
    d = EffectDialog('Volume')
    d.add_slider('Volume', volume_last, 0, 200, 0)
    d.callback = callback
    return d

effect.effects['Volume'] = volume
