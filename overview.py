from math import ceil

# TODO: think and comment, comment, comment
""" Why this module exists

Needs to display a waveform.

Provides "data thumbnails". Pre-compute

"""


def overview(f, data, density):
    # density must be an integer
    left = 0
    end = len(data)
    res = []
    while left < end:
        right = left + density
        if right > end:
            right = end
        v = f(data[left:right])
        res.append(v)
        left = right 
    return res

def build(f, data, density=5000):
    if len(data) / density <= density:
        return [data]
    else:
        o = overview(f, data, density)
        return [data] + build(f, o, density)


def find_level(density, node_size):
    # density of level 0 = 1
    # density of level 1 = node_size 
    # density of level 2 = node_size**2
    # find highest level such that node_size**level < density
    level = 0
    while node_size**(level + 1) <= density:
        level = level + 1
    return level

def get_overview(f, start, end, density, data, node_size):
    # gotta CHECKME
    level = find_level(density, node_size)
    if level >= len(data):
        level = len(data) - 1
    density = int(round(density / float(node_size**level)))
    start = int(start / float(node_size**level ))
    end = int(ceil(end / float(node_size**level)))
    return overview(f, data[level][start:end], density)

# -- Tests

def test_build():
    values = range(30)
    print build(min, values, 5)
    print build(max, values, 5)
    print
    print build(min, values, 2)[1:]
    print build(max, values, 2)[1:]
    print


def test_find_level():
    assert find_level(1, 5) == 0
    assert find_level(4, 5) == 0
    assert find_level(5, 5) == 1
    assert find_level(24, 5) == 1
    assert find_level(25, 5) == 2

def test_get_overview():
    N = 30 * 60 * 44100
    values = range(N)
    density =  44100 / 10
    pre_density = 1000
    pre_comp = build(min, values, pre_density)
    print "pre-computed"
    print get_overview(min, 0, 2000*density, density, pre_comp, pre_density)
    print get_overview(max, 0, 2000*density, density, pre_comp, pre_density)
    
if __name__ == "__main__":
    test_build()
    test_find_level()
    test_get_overview()
