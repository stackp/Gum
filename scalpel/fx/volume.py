import effect
import gtkeffect

volume_last = 100

def volume(sound, start, end):

    def process(volume):
        gain = volume / 100.
        x = sound.frames[start:end]
        y = x * gain
        sound.paste(start, end, y)
        
    def ui(parent):
        global volume_last
        name_param = 'Volume'
        d = gtkeffect.Dialog('Volume')
        d.set_transient_for(parent)
        d.add_slider(name_param, volume_last, 0, 200)
        try:
            parameters = d.get_parameters()
        except:
            return
        volume = parameters[name_param]
        volume_last = volume
        process(volume)

    return ui


effect.effects['Volume'] = volume
