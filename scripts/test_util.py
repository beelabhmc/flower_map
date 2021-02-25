import numpy as np
from matplotlib import pyplot as plt


def create_arr(lst, *shape):
    if not shape:
        shape = (1, len(lst))
    arr = np.empty(len(lst), dtype=object)
    arr[:] = lst[:]
    return arr.reshape(shape)

def plot_img(imgs, titles=None, close=False):
    """
        a function for quickly visualizing a bunch of numpy matrices side-by-side
        in a grid format
        Input:
            imgs - a tuple containing...
                1) a list of np matrices, where the first matrix must an original
                   image from cv.imread
                2) an integer for the number of rows in the grid
                3) an integer for the number of cols in the grid
                Note that #2 * #3 must equal len(#1)
            titles - an array of the same len as #1 with titles for each image
            close - whether to stop execution of the calling script after plotting
    """
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
