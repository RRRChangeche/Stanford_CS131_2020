"""
CS131 - Computer Vision: Foundations and Applications
Assignment 4
Author: Donsuk Lee (donlee90@stanford.edu)
Date created: 09/2017
Last modified: 10/16/2020
Python Version: 3.5+
"""

# from email.utils import make_msgid
# from fcntl import LOCK_WRITE
import numpy as np
from skimage import color


def energy_function(image):
    """Computes energy of the input image.

    For each pixel, we will sum the absolute value of the gradient in each direction.
    Don't forget to convert to grayscale first.

    Hint: Use np.gradient here

    Args:
        image: numpy array of shape (H, W, 3)

    Returns:
        out: numpy array of shape (H, W)
    """
    H, W, _ = image.shape
    out = np.zeros((H, W))
    gray_image = color.rgb2gray(image)

    ### YOUR CODE HERE
    '''
    np.gradient return: 
    A list of ndarrays (or a single ndarray if there is only one dimension) 
    corresponding to the derivatives of f with respect to each dimension. 
    Each derivative has the same shape as f.
    ''' 
    dy, dx = np.gradient(gray_image)
    out = abs(dx) + abs(dy)
    ### END YOUR CODE

    return out


def compute_cost(image, energy, axis=1):
    """Computes optimal cost map (vertical) and paths of the seams.

    Starting from the first row, compute the cost of each pixel as the sum of energy along the
    lowest energy path from the top.

    We also return the paths, which will contain at each pixel either -1, 0 or 1 depending on
    where to go up if we follow a seam at this pixel.

    In the case that energies are equal, choose the left-most path. Note that
    np.argmin returns the index of the first ocurring minimum of the specified
    axis.

    Make sure your code is vectorized because this function will be called a lot.
    You should only have one loop iterating through the rows.

    We also recommend you create a stacked matrix with left, middle, and right costs
    to make your cost and paths calculations easier.

    Args:
        image: not used for this function
               (this is to have a common interface with compute_forward_cost)
        energy: numpy array of shape (H, W)
        axis: compute cost in width (axis=1) or height (axis=0)

    Returns:
        cost: numpy array of shape (H, W)
        paths: numpy array of shape (H, W) containing values -1 (up and left), 0 (straight up), or 1 (up and right)
    """
    energy = energy.copy()

    if axis == 0:
        energy = np.transpose(energy, (1, 0))

    H, W = energy.shape

    cost = np.zeros((H, W))
    paths = np.zeros((H, W), dtype=np.int)

    # Initialization
    cost[0] = energy[0]
    paths[0] = 0  # we don't care about the first row of paths

    ### YOUR CODE HERE
    # Calculate cost at each pixel
    for i in range(1, H):
        # Calculate cost map at each row 
        '''Cost map = M[i,j] = E[i, j] + min(M[i-1, j-1], M[i-1, j], M[i-1, j+1])'''
        M_left = cost[i-1][:W-1]
        M_mid = cost[i-1]
        M_right = cost[i-1][1:]

        # Edge cases - left side and right side file with large number
        M_left = np.insert(M_left, 0, 1<<32, axis=0)
        M_right = np.insert(M_right, W-1, 1<<32, axis=0)

        M = np.array([M_left, M_mid, M_right])
        cost[i] = energy[i] + np.min(M, axis=0)
        
        # Pick minimum cost at row i-1 as path
        '''
        M.shape = (3, W), argmin returns 0~2
        return 0 -> path should go through up and left
        return 1 -> path should go through up
        return 2 -> path should go through up and right
        '''
        paths[i] = np.argmin(M, axis=0) - 1

    ### END YOUR CODE

    if axis == 0:
        cost = np.transpose(cost, (1, 0))
        paths = np.transpose(paths, (1, 0))

    # Check that paths only contains -1, 0 or 1
    assert np.all(np.any([paths == 1, paths == 0, paths == -1], axis=0)), \
           "paths contains other values than -1, 0 or 1"

    return cost, paths


def backtrack_seam(paths, end):
    """Backtracks the paths map to find the seam ending at (H-1, end)

    To do that, we start at the bottom of the image on position (H-1, end), and we
    go up row by row by following the direction indicated by paths:
        - left (value -1)
        - middle (value 0)
        - right (value 1)

    Args:
        paths: numpy array of shape (H, W) containing values -1, 0 or 1
        end: the seam ends at pixel (H, end)

    Returns:
        seam: np.array of indices of shape (H,). The path pixels are the (i, seam[i])
    """
    H, W = paths.shape
    # initialize with -1 to make sure that everything gets modified
    seam = - np.ones(H, dtype=np.int)

    # Initialization
    seam[H-1] = end

    ### YOUR CODE HERE
    for i in range(H-2, -1, -1):
        # if paths[i+1][seam[i+1]] == -1:
        #     seam[i] = seam[i+1] - 1
        # elif paths[i+1][seam[i+1]] == 0:
        #     seam[i] = seam[i+1]
        # elif paths[i+1][seam[i+1]] == 1:
        #     seam[i] = seam[i+1] + 1
        seam[i] = seam[i+1] + paths[i+1][seam[i+1]]

    ### END YOUR CODE

    # Check that seam only contains values in [0, W-1]
    assert np.all(np.all([seam >= 0, seam < W], axis=0)), "seam contains values out of bounds"

    return seam


def remove_seam(image, seam):
    """Remove a seam from the image.

    This function will be helpful for functions reduce and reduce_forward.

    Args:
        image: numpy array of shape (H, W, C) or shape (H, W)
        seam: numpy array of shape (H,) containing indices of the seam to remove

    Returns:
        out: numpy array of shape (H, W-1, C) or shape (H, W-1)
             make sure that `out` has same type as `image`
    """

    # Add extra dimension if 2D input
    if len(image.shape) == 2:
        image = np.expand_dims(image, axis=2)

    out = None
    H, W, C = image.shape
    ### YOUR CODE HERE
    out = image[np.arange(W) != seam.reshape(-1,1)].reshape(H, W-1, C)
    ### END YOUR CODE
    out = np.squeeze(out)  # remove last dimension if C == 1

    # Make sure that `out` has same type as `image`
    assert out.dtype == image.dtype, \
       "Type changed between image (%s) and out (%s) in remove_seam" % (image.dtype, out.dtype)

    return out


def reduce(image, size, axis=1, efunc=energy_function, cfunc=compute_cost, bfunc=backtrack_seam, rfunc=remove_seam):
    """Reduces the size of the image using the seam carving process.

    At each step, we remove the lowest energy seam from the image. We repeat the process
    until we obtain an output of desired size.

    SUPER IMPORTANT: IF YOU WANT TO PREVENT CASCADING ERRORS IN THE CODE OF reduce(), USE FUNCTIONS:
        - efunc (instead of energy_function)
        - cfunc (instead of compute_cost)
        - bfunc (instead of backtrack_seam)
        - rfunc (instead of remove_seam)

    Args:
        image: numpy array of shape (H, W, 3)
        size: size to reduce height or width to (depending on axis)
        axis: reduce in width (axis=1) or height (axis=0)
        efunc: energy function to use
        cfunc: cost function to use
        bfunc: backtrack seam function to use
        rfunc: remove seam function to use

    Returns:
        out: numpy array of shape (size, W, 3) if axis=0, or (H, size, 3) if axis=1
    """

    out = np.copy(image)
    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    H = out.shape[0]
    W = out.shape[1]

    assert W > size, "Size must be smaller than %d" % W

    assert size > 0, "Size must be greater than zero"

    ### YOUR CODE HERE
    for _ in range(W-size):
        energy = efunc(out)
        cost, paths = cfunc(out, energy)
        seam = bfunc(paths, np.argmin(cost[-1]))
        out = rfunc(out, seam)
    ### END YOUR CODE

    assert out.shape[1] == size, "Output doesn't have the right shape"

    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    return out


def duplicate_seam(image, seam):
    """Duplicates pixels of the seam, making the pixels on the seam path "twice larger".

    This function will be helpful in functions enlarge_naive and enlarge.

    Args:
        image: numpy array of shape (H, W, C)
        seam: numpy array of shape (H,) of indices

    Returns:
        out: numpy array of shape (H, W+1, C)
    """

    H, W, C = image.shape
    out = np.zeros((H, W + 1, C))

    ### YOUR CODE HERE
    for i in range(H):
        rowIdx = seam[i]
        value = image[i][rowIdx]
        out[i] = np.insert(image[i], rowIdx, value, axis=0).reshape(W+1, -1)
        # idx = seam[i]
        # out[i] = np.concatenate((image[i, 0:idx+1], image[i, idx:W]), axis = None).reshape(W+1, -1)  
    ### END YOUR CODE

    return out


def enlarge_naive(image, size, axis=1, efunc=energy_function, cfunc=compute_cost, bfunc=backtrack_seam, dfunc=duplicate_seam):
    """Increases the size of the image using the seam duplication process.

    At each step, we duplicate the lowest energy seam from the image. We repeat the process
    until we obtain an output of desired size.

    SUPER IMPORTANT: IF YOU WANT TO PREVENT CASCADING ERRORS IN THE CODE OF enlarge_naive(), USE FUNCTIONS:
        - efunc (instead of energy_function)
        - cfunc (instead of compute_cost)
        - bfunc (instead of backtrack_seam)
        - dfunc (instead of duplicate_seam)

    Args:
        image: numpy array of shape (H, W, C)
        size: size to increase height or width to (depending on axis)
        axis: increase in width (axis=1) or height (axis=0)
        efunc: energy function to use
        cfunc: cost function to use
        bfunc: backtrack seam function to use
        dfunc: duplicate seam function to use

    Returns:
        out: numpy array of shape (size, W, C) if axis=0, or (H, size, C) if axis=1
    """

    out = np.copy(image)
    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    H = out.shape[0]
    W = out.shape[1]

    assert size > W, "size must be greather than %d" % W

    ### YOUR CODE HERE
    for _ in range(size-W):
        energy = efunc(out)
        cost, paths = cfunc(out, energy)
        seam = bfunc(paths, np.argmin(cost[-1]))
        out = dfunc(out, seam)
    ### END YOUR CODE

    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    return out


def find_seams(image, k, axis=1, efunc=energy_function, cfunc=compute_cost, bfunc=backtrack_seam, rfunc=remove_seam):
    """Find the top k seams (with lowest energy) in the image.

    We act like if we remove k seams from the image iteratively, but we need to store their
    position to be able to duplicate them in function enlarge.

    We keep track of where the seams are in the original image with the array seams, which
    is the output of find_seams.
    We also keep an indices array to map current pixels to their original position in the image.

    SUPER IMPORTANT: IF YOU WANT TO PREVENT CASCADING ERRORS IN THE CODE OF find_seams(), USE FUNCTIONS:
        - efunc (instead of energy_function)
        - cfunc (instead of compute_cost)
        - bfunc (instead of backtrack_seam)
        - rfunc (instead of remove_seam)

    Args:
        image: numpy array of shape (H, W, C)
        k: number of seams to find
        axis: find seams in width (axis=1) or height (axis=0)
        efunc: energy function to use
        cfunc: cost function to use
        bfunc: backtrack seam function to use
        rfunc: remove seam function to use

    Returns:
        seams: numpy array of shape (H, W)

        if k = 2
        seam 1 locate at where element value == 1
        seam 2 locate at where element value == 2
        [0,2,0,0,1]
        [0,2,0,0,1]
        [2,0,0,1,0]
        [0,2,0,1,0]
        [0,2,1,0,0]
        [0,2,1,0,0]
    """

    image = np.copy(image)
    if axis == 0:
        image = np.transpose(image, (1, 0, 2))

    H, W, C = image.shape
    assert W > k, "k must be smaller than %d" % W

    # Create a map to remember original pixel indices
    # At each step, indices[row, col] will be the original column of current pixel
    # The position in the original image of this pixel is: (row, indices[row, col])
    # We initialize `indices` with an array like (for shape (2, 4)):
    #     [[1, 2, 3, 4],
    #      [1, 2, 3, 4]]
    indices = np.tile(range(W), (H, 1))  # shape (H, W)

    # We keep track here of the seams removed in our process
    # At the end of the process, seam number i will be stored as the path of value i+1 in `seams`
    # An example output for `seams` for two seams in a (3, 4) image can be:
    #    [[0, 1, 0, 2],
    #     [1, 0, 2, 0],
    #     [1, 0, 0, 2]]
    seams = np.zeros((H, W), dtype=np.int)

    # Iteratively find k seams for removal
    for i in range(k):
        # Get the current optimal seam
        energy = efunc(image)
        cost, paths = cfunc(image, energy)
        end = np.argmin(cost[H - 1])
        seam = bfunc(paths, end)

        # Remove that seam from the image
        image = rfunc(image, seam)

        # Store the new seam with value i+1 in the image
        # We can assert here that we are only writing on zeros (not overwriting existing seams)
        assert np.all(seams[np.arange(H), indices[np.arange(H), seam]] == 0), \
            "we are overwriting seams"
        seams[np.arange(H), indices[np.arange(H), seam]] = i + 1

        # We remove the indices used by the seam, so that `indices` keep the same shape as `image`
        indices = rfunc(indices, seam)

    if axis == 0:
        seams = np.transpose(seams, (1, 0))

    return seams


def enlarge(image, size, axis=1, efunc=energy_function, cfunc=compute_cost, dfunc=duplicate_seam, bfunc=backtrack_seam, rfunc=remove_seam):
    """Enlarges the size of the image by duplicating the low energy seams.

    We start by getting the k seams to duplicate through function find_seams.
    We iterate through these seams and duplicate each one iteratively.

    SUPER IMPORTANT: IF YOU WANT TO PREVENT CASCADING ERRORS IN THE CODE OF enlarge(), USE FUNCTIONS:
        - efunc (instead of energy_function)
        - cfunc (instead of compute_cost)
        - dfunc (instead of duplicate_seam)
        - bfunc (instead of backtrack_seam)
        - rfunc (instead of remove_seam)
        - find_seams

    Args:
        image: numpy array of shape (H, W, C)
        size: size to reduce height or width to (depending on axis)
        axis: enlarge in width (axis=1) or height (axis=0)
        efunc: energy function to use
        cfunc: cost function to use
        dfunc: duplicate seam function to use
        bfunc: backtrack seam function to use
        rfunc: remove seam function to use

    Returns:
        out: numpy array of shape (size, W, C) if axis=0, or (H, size, C) if axis=1
    """

    out = np.copy(image)
    # Transpose for height resizing
    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    H, W, C = out.shape

    assert size > W, "size must be greather than %d" % W

    assert size <= 2 * W, "size must be smaller than %d" % (2 * W)

    ### YOUR CODE HERE
    seams = find_seams(out, size-W)
    seams = np.expand_dims(seams, axis=2)
    for i in range(size-W):
        # seam = np.where(seams == i+1)[1] + i
        # out = dfunc(out, seam)
        # seams += 1

        out = duplicate_seam(out, np.where(seams== i+1)[1])
        seams = duplicate_seam(seams, np.where(seams == i+1)[1])
    ### END YOUR CODE

    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    return out


def compute_forward_cost(image, energy):
    """Computes forward cost map (vertical) and paths of the seams.

    Starting from the first row, compute the cost of each pixel as the sum of energy along the
    lowest energy path from the top.
    Make sure to add the forward cost introduced when we remove the pixel of the seam.

    We also return the paths, which will contain at each pixel either -1, 0 or 1 depending on
    where to go up if we follow a seam at this pixel.

    Args:
        image: numpy array of shape (H, W, 3) or (H, W)
        energy: numpy array of shape (H, W)

    Returns:
        cost: numpy array of shape (H, W)
        paths: numpy array of shape (H, W) containing values -1, 0 or 1
    """

    image = color.rgb2gray(image)
    H, W = image.shape

    cost = np.zeros((H, W))
    paths = np.zeros((H, W), dtype=np.int)

    # Initialization
    cost[0] = energy[0]
    # for j in range(W):
        # if j > 0 and j < W - 1:
            # cost[0, j] += np.abs(image[0, j+1] - image[0, j-1])
    cost[0, 1:W-1] += np.abs(image[0, 2:] - image[0, :W-2])
    paths[0] = 0  # we don't care about the first row of paths

    ### YOUR CODE HERE
    for i in range(1, H):
        # Calculate forward cost map at each pixel
        '''
        Forward cost map = M[i,j] = min(
                                        M[i-1, j-1] + CL,
                                        M[i-1, j] + CV,
                                        M[i-1, j+1] + CR
                                    )
        where
            CL = |I[i-1, j] - I[i, j-1]| - |I[i, j+1] - I[i, j-1]|
            CV = |I[i, j+1] - I[i, j-1]|
            CR = |I[i-1, j] - I[i, j+1]| - |I[i, j-1] - I[i, j+1]|
        '''
        M_left = cost[i-1][:W-1]
        M_left = np.insert(M_left, 0, 1<<32, axis=0)
        M_mid = cost[i-1]
        M_right = cost[i-1][1:]
        M_right = np.insert(M_right, W-1, 1<<32, axis=0)

        # I[i, j-1]
        I_left = np.insert(image[i][:W-1], 0, 0, axis=0)
        # I[i-1, j]
        I_mid = image[i-1]
        # I[i, j+1]
        I_right = np.insert(image[i][1:], W-1, 0, axis=0)

        CV = np.abs(I_right - I_left)
        CV[0] = 0
        CV[-1] = 0
        CL = np.abs(I_mid - I_left) + CV
        CL[0] = 0
        CR = np.abs(I_mid - I_right) + CV
        CR[-1] = 0

        M = np.array([M_left+CL, M_mid+CV, M_right+CR])
        cost[i] = energy[i] + np.min(M, axis=0)
        
        # if i==2:
        #     print("Ileft", I_left)
        #     print("Imid", I_mid)
        #     print("Iright", I_right)
        #     print("CL", CL)
        #     print("CV", CV)
        #     print("CR", CR)
        #     print("Mleft", M_left)
        #     print("Mmid", M_mid)
        #     print("Mright", M_right)

        # Pick minimum cost at row i-1 as path
        '''
        M.shape = (3, W), argmin returns 0~2
        return 0 -> path should go through up and left
        return 1 -> path should go through up
        return 2 -> path should go through up and right
        '''
        paths[i] = np.argmin(M, axis=0) - 1
        ### END YOUR CODE
        
    # Check that paths only contains -1, 0 or 1
    assert np.all(np.any([paths == 1, paths == 0, paths == -1], axis=0)), \
           "paths contains other values than -1, 0 or 1"

    return cost, paths


def energy_fast(image, energy, lower, upper):
    """Computes energy of the input image.

    For each pixel, we will sum the absolute value of the gradient in each direction.
    Don't forget to convert to grayscale first.

    Hint: Use np.gradient here

    Args:
        image: numpy array of shape (H, W, 3)

    Returns:
        out: numpy array of shape (H, W)
    """
    H, W, _ = image.shape
    out = np.zeros((H, W))
    gray_image = color.rgb2gray(image)

    ### YOUR CODE HERE
    '''
    np.gradient return: 
    A list of ndarrays (or a single ndarray if there is only one dimension) 
    corresponding to the derivatives of f with respect to each dimension. 
    Each derivative has the same shape as f.
    ''' 
    # only update the range that the seam covered
    # W_out = W_energy - 1
    # update left part
    if lower <= 1:
        # print(lower, upper)
        dy, dx = np.gradient(gray_image[:, 0:upper+1])
        updateRange = (abs(dx) + abs(dy))[:, :-1]   # range 0~upper+1
        out = np.concatenate((updateRange, energy[:, upper+1:]), axis=1)
    # update right part
    elif upper >= W-2:
        dy, dx = np.gradient(gray_image[:, lower-2:])
        updateRange = (abs(dx) + abs(dy))[:, 1: ] # range lower-3~end
        out = np.concatenate((energy[:, :lower-1], updateRange), axis=1)
    # update middle part
    else:
        dy, dx = np.gradient(gray_image[:, lower-2:upper+2])
        updateRange = (abs(dx) + abs(dy))[:, 1:-1] # range lower-1~upper+1
        out = np.concatenate((energy[:, :lower-1], updateRange, energy[:, upper+2:]), axis=1)
        
     # if i <= 1:
        #     energy = np.c_[efunc(out[:, 0: j+1])[:, :-1], energy[:, j+1: ]]
        # elif j >= out.shape[1]-2:
        #     energy = np.c_[energy[:, 0: i-1], efunc(out[:, i-2: ])[:, 1: ]]
        # else:
        #     energy = np.c_[energy[:, 0: i-1], efunc(out[:, i-2: j+2])[:, 1: -1], energy[:, j+2:]]
    # print("image", image.shape, "out", out.shape)
    ### END YOUR CODE

    return out


def reduce_fast(image, size, axis=1, efunc=energy_function, cfunc=compute_cost):
    """Reduces the size of the image using the seam carving process. Faster than `reduce`.

    Use your own implementation (you can use auxiliary functions if it helps like `energy_fast`)
    to implement a faster version of `reduce`.

    Args:
        image: numpy array of shape (H, W, C)
        size: size to reduce height or width to (depending on axis)
        axis: reduce in width (axis=1) or height (axis=0)
        efunc: energy function to use
        cfunc: cost function to use

    Returns:
        out: numpy array of shape (size, W, C) if axis=0, or (H, size, C) if axis=1
    """

    out = np.copy(image)
    # image = color.rgb2gray(image)
    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    H = out.shape[0]
    W = out.shape[1]

    assert W > size, "Size must be smaller than %d" % W

    assert size > 0, "Size must be greater than zero"

    ### YOUR CODE HERE
    energy =  energy_function(out)
    for _ in range(W-size):
        cost, paths = cfunc(out, energy)
        seam = backtrack_seam(paths, np.argmin(cost[-1]))
        out = remove_seam(out, seam)

        # update lower and upper bound 
        lower = np.min(seam)
        upper = np.max(seam)
        energy = efunc(out, energy, lower, upper)
    ### END YOUR CODE

    assert out.shape[1] == size, "Output doesn't have the right shape"

    if axis == 0:
        out = np.transpose(out, (1, 0, 2))

    return out


def remove_object(image, mask):
    """Remove the object present in the mask.

    Returns an output image with same shape as the input image, but without the object in the mask.

    Args:
        image: numpy array of shape (H, W, 3)
        mask: numpy boolean array of shape (H, W)

    Returns:
        out: numpy array of shape (H, W, 3)
    """
    assert image.shape[:2] == mask.shape

    H, W, _ = image.shape
    out = np.copy(image)

    ### YOUR CODE HERE

    # Reduce image 
    energy =  energy_function(out)
    weighted_energy = energy - (mask*1e10)
    while not np.all(mask == 0):
        cost, paths = compute_forward_cost(out, weighted_energy)
        seam = backtrack_seam(paths, np.argmin(cost[-1]))
        out = remove_seam(out, seam)
        mask = remove_seam(mask, seam)

        # update energy map  
        lower = np.min(seam)    # update lower bound 
        upper = np.max(seam)    # update upper bound
        energy = energy_fast(out, energy, lower, upper) # return W-1 width energy = out width
        weighted_energy = energy - (mask*1e10)

    # Enlarge image
    out = enlarge(out, W)
    ### END YOUR CODE

    assert out.shape == image.shape

    return out
