import numpy as np
import os
from nilearn import image
import nibabel as nib
import matplotlib.pyplot as plt
from PIL import Image
from Visualisation import max_slice_of_planes_viewer_mc
import glob

original_dir = '/home/jara/Savine/Hammers_n30r83zipped' # get from: /archive/ebron/Hammers_n30r83/
list_mask = glob.glob(original_dir + '/*_mask.nii.gz')
# list_mask = glob.glob(original_dir + '/a*brain_mask_r5.nii.gz')
list_mask.sort()
# str_mask = '_brain_mask_r5.nii'
num_area = 83

sample_len = 30  # total number of subjects

images = []
targets = []
feat_path_list = []

sizes = np.zeros(shape=[sample_len, 3])
for i in range(1, sample_len+1, 1):
    # images in grey-scale
    fnamenum = str(i).zfill(2)
    fname = "".join('a' + str(fnamenum) + '.nii.gz')
    img_path = os.path.join(original_dir, fname)
    feat_path_list.append(img_path)
    img = nib.load(img_path)
    temp = img.get_data()
    sizes[i-1, :] = temp.shape
    images.append(temp)

    # target images
    target_path = os.path.join(original_dir, 'a' + str(fnamenum) + '-seg.nii.gz')
    target = nib.load(target_path)
    temp = target.get_data()
    temp = np.where(temp > num_area + 0.5, 0, temp)
    targets.append(temp)

    # mask list for bounding box
    # list_mask.append("".join('a' + str(fnamenum) + str_mask))


def pad(array, reference_shape):
    """
    array: Array to be padded
    ref_shape: tuple of size of ndarray to create
    """
    result = np.zeros(reference_shape)  # Create an array of zeros with the reference shape
    diff = np.asarray(array.shape) - reference_shape
    offsets = abs(diff//2)
    result[offsets[0]:array.shape[0] + offsets[0], offsets[1]:array.shape[1] + offsets[1], offsets[2]:array.shape[2]
                   + offsets[2]] = array
    return result


########################################################################################################################
#   BOUNDING BOX

path = original_dir
# save_path = '/home/jara/Savine/Hammers_n30r83unzipped/full_bbox'

max_x_width = 0
max_y_width = 0
max_z_width = 0

masks = []

# Parameters and Initialization
history = {}

# Find common bounding box of all subjects in a cohort
for j, subject in enumerate(list_mask):
    print('%04d' % j, subject)

    mask_path = list_mask[j]
    mask = image.load_img(mask_path).get_data()
    masks.append(mask)

    # list the slices which are not empty
    xslice = []
    yslice = []
    zslice = []

    for x in range(mask.shape[0]):
        slice = mask[x, :, :]
        if slice.max() > 0:
            xslice.append(x)
    xslice.sort()

    for y in range(mask.shape[1]):
        slice = mask[:, y, :]
        if slice.max() > 0:
            yslice.append(y)
    yslice.sort()

    for z in range(mask.shape[2]):
        slice = mask[:, :, z]
        if slice.max() > 0:
            zslice.append(z)
    zslice.sort()

    # Error messages
    if 0 == len(xslice) or 0 == len(yslice):
        print('Warning: Please check your dataset, xslice or yslice is 0.')
        break
        # exit()
    if 0 == len(zslice):
        print('no value in mask!')
        break
        # exit()

    # find start and end
    xstart = min(xslice)
    xend = max(xslice)
    ystart = min(yslice)
    yend = max(yslice)
    zstart = min(zslice)
    zend = max(zslice)

    # record the max and min width in a cohort
    x_width = xend - xstart + 1
    y_width = yend - ystart + 1
    z_width = zend - zstart + 1

    if x_width > max_x_width:
        max_x_width = x_width
    if y_width > max_y_width:
        max_y_width = y_width
    if z_width > max_z_width:
        max_z_width = z_width

    print('No.', '%03d:' % j, 'x start from', '%03d,' % xstart, 'end by', '%03d,' % xend, 'width is',
          '%03d.' % x_width)
    print('        ', 'y start from', '%03d,' % ystart, 'end by', '%03d,' % yend, 'height is', '%03d.' % y_width)
    print('        ', 'z start from', '%03d,' % zstart, 'end by', '%03d,' % zend, 'depth is', '%03d.' % z_width)

    bbox = {'x_width': x_width, 'y_width': y_width, 'z_width': z_width, 'xstart': xstart, 'xend': xend,
            'ystart': ystart, 'yend': yend, 'zstart': zstart, 'zend': zend}
    history[subject] = bbox
        # break

history['max'] = {'max_x_width': max_x_width, 'max_y_width': max_y_width,
                         'max_z_width': max_z_width}
# np.save(os.path.join(save_path, '_redo_bbox_historyWholeBrain'), history)  # temp for repro subjects

print('max_x_width: ', max_x_width, 'max_y_width: ', max_y_width,
      'max_z_width: ', max_z_width)
# with open(os.path.join(save_path, '_redo_bbox_historyWholeBrain.txt'),
#               'w') as f:  # temp for repro subjects
#         f.write(str(history))

# # Step 2 calculate the border among all subjects
nDownSample = 16

x_width_crop = int(np.ceil(max_x_width/nDownSample)*nDownSample)
y_width_crop = int(np.ceil(max_y_width/nDownSample)*nDownSample)
z_width_crop = int(np.ceil(max_z_width/nDownSample)*nDownSample)

x_width_crop = 176  # size from Hammers
y_width_crop = 208  # size from ADNI
z_width_crop = 160  # size from ADNI

###############################################################################################################
# Step 3 crop the data
ref_shape = [x_width_crop, y_width_crop, z_width_crop]  #[176, 208, 160]
X_data = np.empty((sample_len, ref_shape[0], ref_shape[1], ref_shape[2]))
Y_data = np.empty((sample_len, ref_shape[0], ref_shape[1], ref_shape[2]))

X_test27282930_array = np.empty((4, ref_shape[0], ref_shape[1], ref_shape[2]))
Y_test27282930_array = np.empty((4, ref_shape[0], ref_shape[1], ref_shape[2]))
print('Reference cropped shape: ', ref_shape)

save_path = "".join('/home/jara/Savine/Hammers' + str(num_area) + 'RegionsSkullStripped' + str(ref_shape[0]) + '_' +
                    str(ref_shape[1]) + '_' + str(ref_shape[2]))
# save_path = os.path.join(original_dir, 'WholeBrain' + str(num_area) + 'Areas176_224_240')
if not os.path.exists(save_path):
    os.makedirs(save_path)

# IT'S CROPPING THE ORIGINAL IMAGE TO THE SIZE OF THE MASK UNNECESSARILY


def norm(array):
    """"
    makes mean of array zero and std of 1
    """
    array -= np.mean(array)
    array /= np.std(array)
    return array

# def pad_uneven(array, reference_shape, y_tail, z_tail):
#     """
#     array: Array to be padded
#     ref_shape: tuple of size of ndarray to create
#     """
#     result = np.zeros(reference_shape)  # Create an array of zeros with the reference shape
#     diff = np.asarray(array.shape) - reference_shape
#     offsets = abs(diff//2)
#     result[offsets[0]:array.shape[0] + offsets[0], offsets[1]:array.shape[1] + offsets[1], offsets[2]:array.shape[2]
#                    + offsets[2]] = array
#     return result


for i, key in enumerate(list_mask):
    # z_tail = 0
    # y_tail = 0
    # loading each image with label and lobe mask
    features = np.asarray(images[i])
    gt_data = np.asarray(targets[i])
    mask_data = np.asarray(masks[i])

    # load the start and the end in each bbox
    xstart = history[key]['xstart']
    xend = history[key]['xend']
    ystart = history[key]['ystart']
    yend = history[key]['yend']
    zstart = history[key]['zstart']
    zend = history[key]['zend']
    x_width = history[key]['x_width']
    y_width = history[key]['y_width']
    z_width = history[key]['z_width']

    crop_gt = gt_data[xstart:xend + 1, ystart:yend + 1, zstart:zend + 1]

    # x_diff = ref_shape[0] - x_width
    # diff_per_side = x_diff // 2
    # xstart -= diff_per_side
    # xend += diff_per_side
    #
    # y_diff = ref_shape[1] - y_width
    # diff_per_side = y_diff // 2
    # if (ystart - diff_per_side) < 0:
    #     y_tail = ystart
    #     ystart = 0
    #     yend += y_tail
    # else:
    #     ystart -= diff_per_side
    #     yend += diff_per_side
    #
    # z_diff = ref_shape[2] - z_width
    # diff_per_side = z_diff // 2
    # if (zstart - diff_per_side) < 0:
    #     z_tail = zstart
    #     zstart = 0
    #     zend += z_tail
    # else:
    #     zstart -= diff_per_side
    #     zend += diff_per_side

    crop_data = features[xstart:xend + 1, ystart:yend + 1, zstart:zend + 1]
    # print('scan,', np.unique(crop_data))
    # print('gt', np.unique(crop_gt))

    crop_mask = mask_data[xstart:xend + 1, ystart:yend + 1, zstart:zend + 1]

    # padding
    crop_gt = pad(crop_gt, ref_shape)
    # if z_tail == 0 and y_tail == 0:
    crop_data = pad(crop_data, ref_shape)

    crop_mask = pad(crop_mask, ref_shape)


    # else:
    #     crop_gt = pad_uneven(crop_data, ref_shape, y_tail, z_tail)
    crop_mask = pad(crop_mask, ref_shape)
    # max_slice_of_planes_viewer_mc(np.expand_dims(crop_data, axis=0), np.expand_dims(crop_data, axis=0), True)
    crop_data = np.where(crop_mask < 0.5, 0, crop_data)  # skull-stripping based on
    # max_slice_of_planes_viewer_mc(np.expand_dims(crop_data, axis=0), np.expand_dims(crop_data, axis=0), True)

    # normalization
    crop_data = norm(crop_data)
    # max_slice_of_planes_viewer_mc(np.expand_dims(crop_data, axis=0), np.expand_dims(crop_data, axis=0), True)

    # saving data
    num_subject = str(i+1).zfill(2)
    img = nib.Nifti1Image(crop_data, np.eye(4, 4))
    nib.save(img, os.path.join(save_path, 'a' + str(num_subject) + '.nii.gz'))

    img2 = nib.Nifti1Image(crop_gt, np.eye(4, 4))
    nib.save(img2, os.path.join(save_path, 'a' + str(num_subject) + '-seg.nii.gz'))

    # img3 = nib.Nifti1Image(crop_mask, np.eye(4, 4))
    # nib.save(img3, os.path.join(save_path, 'a' + str(num_subject) + 'mask.nii.gz'))

    X_data[i, :, :, :] = crop_data
    Y_data[i, :, :, :] = crop_gt

    if i > 26:
        X_test27282930_array[i-27, ] = crop_data
        Y_test27282930_array[i-27, ] = crop_gt

    # save as numpy
    # np.save(os.path.join(save_path, 'a' + str(num_subject)), crop_data, allow_pickle=True)
    # np.save(os.path.join(save_path, 'a' + str(num_subject) + '-seg'), crop_gt, allow_pickle=True)

# Don't need this
# np.save(os.path.join(save_path, 'X_data_array'), X_data, allow_pickle=True)
# np.save(os.path.join(save_path, 'Y_data_array'), Y_data, allow_pickle=True)

# Only this
np.save(os.path.join(save_path, 'X_test27282930_array'), X_test27282930_array, allow_pickle=True)
np.save(os.path.join(save_path, 'Y_test27282930_array'), Y_test27282930_array, allow_pickle=True)

axial_index, sagittal_index, coronal_index, sum_gt_total = max_slice_of_planes_viewer_mc(X_data, Y_data, True)

# And this
np.save(os.path.join(save_path, 'axial_index'), axial_index, allow_pickle=True)
np.save(os.path.join(save_path, 'sagittal_index'), sagittal_index, allow_pickle=True)
np.save(os.path.join(save_path, 'coronal_index'), coronal_index, allow_pickle=True)

