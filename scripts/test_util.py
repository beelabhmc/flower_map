import numpy as np
from matplotlib import pyplot as plt


def create_arr(lst, *shape):
    if not shape:
        shape = (1, len(lst))
    arr = np.empty(len(lst), dtype=object)
    arr[:] = lst[:]
    return arr.reshape(shape)

def plot_img(imgs, titles=None, close=False):
    if type(imgs) is tuple and type(imgs[0]) == list:
        imgs = create_arr(*imgs)
    fig, axes = plt.subplots(*imgs.shape, figsize=(15.3,7.4))
    for i, ax in np.ndenumerate(axes):
        if len(i) == 1:
            i = (0,) + i
        ax.imshow(imgs[i])
        if titles is not None:
            ax.set_title(titles[i])
        ax.axes.get_xaxis().set_visible(False)
        ax.axes.get_yaxis().set_visible(False)
    fig.tight_layout()
    print('showing plot')
    fig.show()
    if close:
        exit()
