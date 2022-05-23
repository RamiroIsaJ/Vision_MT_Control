# Ramiro Isa-Jara, ramiro.isaj@gmail.com
# Vision Interface to use for viewing and saving images from Video Camera Input
# with Analysis of area from experiments with well and Control PUMP ----- version 0.2.1

import cv2
import os
import glob
import numpy as np
import pandas as pd
from datetime import datetime
from skimage import morphology
import matplotlib.pyplot as plt
from skimage.color import rgb2hsv
from skimage.filters import threshold_otsu
from sklearn.neighbors import NearestNeighbors


class ReadLastImage:
    def __init__(self, path, type_, id_ima, ini_t, id_sys):
        self.path = path
        self.type = type_
        self.id_ima = id_ima
        self.id_sys = id_sys
        self.ini_time = ini_t
        self.time_c = None

    def diff_time(self, t_end):
        t_diff = (t_end - self.ini_time).total_seconds()
        return t_diff

    def ready_img(self, time_c, values):
        self.time_c = time_c
        now_time = datetime.now()
        time_sleep = self.diff_time(now_time)
        if values['_TMI_']:
            time_sleep /= 60
        rest_time = np.round(self.time_c - time_sleep, 4)
        # -----------------------------------------------------------------
        if rest_time < 0 or self.id_ima == 1:
            self.ini_time = datetime.now()
            return True
        else:
            return False

    def f_sorted(self, files_):
        symbol = '\\' if self.id_sys == 0 else '/'
        ids = []
        for f in files_:
            parts = f.split(symbol)
            name_i = parts[len(parts) - 1]
            ids.append(name_i.split('.')[0].split('_')[-1])
        ids = list(map(int, ids))
        ids.sort(key=int)
        file_r = []
        for i in range(len(files_)):
            parts = files_[i].split(symbol)
            name = parts[len(parts) - 1].split('.')
            exp = name[0].split('_')
            if len(exp) >= 2:
                n_exp = exp[0]
                for j in range(1, len(exp)-1):
                    n_exp += '_' + exp[j]
                n_name = n_exp + '_' + str(ids[i]) + '.' + name[1]
            else:
                n_name = str(ids[i]) + '.' + name[1]

            if self.id_sys == 0:
                n_file = parts[0] + symbol
            else:
                n_file = (symbol + parts[0])
            for j in range(1, len(parts)-1):
                n_file += (parts[j] + symbol)
            n_file += n_name
            file_r.append(n_file)
        return file_r

    def load_image(self):
        symbol = '\\' if self.id_sys == 0 else '/'
        filenames = [img for img in glob.glob(self.path+'*'+self.type)]
        filenames = self.f_sorted(filenames)
        if len(filenames) > 0:
            name = filenames[-1]
            parts = name.split(symbol)
            name_i = parts[len(parts)-1]
            image_ = cv2.imread(name)
        else:
            image_, name_i = [], []
        return image_, name_i


# -----------------------------------------------------------------
# Algorithm to detect circular region of well and area of yeast
# -----------------------------------------------------------------
class SegmentYeast:
    def __init__(self):
        self.img, self.img_ = None, None
        self.buffer_size = 0
        self.buffer, self.filters, self.f_contours = [], [], []

    def dist(self, xp, yp):
        return np.sqrt(np.sum((xp - yp) ** 2))

    def build_filters(self):
        k_size, sigma = 21, [4.0]
        for s in sigma:
            for theta in np.arange(0, np.pi, np.pi / 4):
                kern = cv2.getGaborKernel((k_size, k_size), s, theta, 10.0, 0.9, 0, ktype=cv2.CV_32F)
                kern /= 1.5 * kern.sum()
                self.filters.append(kern)

    def apply_gabor(self, img_g):
        gabor_img_ = np.zeros_like(img_g)
        for kern in self.filters:
            np.maximum(gabor_img_, cv2.filter2D(img_g, cv2.CV_8UC3, kern), gabor_img_)
        return gabor_img_

    def preprocessing(self):
        image_gray_ = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        clh = cv2.createCLAHE(clipLimit=5.0)
        clh_img = clh.apply(image_gray_)
        blurred = cv2.GaussianBlur(clh_img, (5, 5), 0)
        return clh_img, blurred

    def buffer_mean(self, k_, area_):
        val_mean = 0
        if k_ < self.buffer_size - 1:
            self.buffer.append(area_)
            k_ += 1
        else:
            c = np.array(self.buffer).reshape(-1, 1)
            model = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(c)
            distances, indices = model.kneighbors(c)
            outlier_index = np.where(distances.mean(axis=1) > 1.0)
            if len(outlier_index[0]) > 0:
                aux_ = [x for i1, x in enumerate(c) if i1 != outlier_index[0].all]
                val_mean = np.average(aux_)
            else:
                val_mean = np.average(np.array(c))
            k_ = 0
            self.buffer = []
        return k_, np.round(val_mean, 2)

    def calculate_contour(self, binary_):
        contours, hierarchy = cv2.findContours(binary_, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        area = []
        for c in contours:
            area.append(cv2.contourArea(c))
        area_min = max(area) / 3
        for c in contours:
            area = cv2.contourArea(c)
            if area > area_min:
                self.f_contours.append(c)

    def binary_contours(self, img_s, binary_):
        img_c = np.copy(img_s)
        contours, hierarchy = cv2.findContours(binary_, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img_c, contours, -1, (0, 0, 255), 2)
        return img_c

    def p_circle(self, binary_):
        cords = []
        self.calculate_contour(binary_)
        contour = sorted(self.f_contours, key=cv2.contourArea, reverse=True)
        for contour1 in contour:
            (x_, y_), radius_ = cv2.minEnclosingCircle(contour1)
            cords.append([x_, y_, radius_])
        cords = np.array(cords)
        (x_, y_), radius_ = cv2.minEnclosingCircle(contour[0])
        if len(contour) > 1:
            idx = np.where(cords == np.max(cords[:, 2]))[0]
            x1, y1 = cords[idx, 0], cords[idx, 1]
            if self.dist(np.array([x_, y_]), np.array([x1, y1])) < 200:
                x_, y_, radius_ = np.round((x_ + x1) / 2), np.round((y1 + y_) / 2), cords[idx, 2] + 5
        radius_ -= 15
        self.f_contours = []
        (x_, y_), radius_ = (int(np.round(x_)), int(np.round(y_))), int(np.round(radius_))
        return x_, y_, radius_

    def well_region(self):
        ima_gray, final_ima = self.preprocessing()
        gabor_img = self.apply_gabor(final_ima)
        thresh = threshold_otsu(gabor_img)
        thresh = cv2.threshold(gabor_img, thresh, 255, cv2.THRESH_TOZERO_INV)[1]
        total = thresh.shape[0] * thresh.shape[1]
        total_n = np.sum(thresh == 0)
        per = np.round(total_n / total, 2)
        if 0.38 > per >= 0.35:
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (4, 4))
            markers = cv2.morphologyEx(thresh, cv2.MORPH_ERODE, kernel, iterations=1)
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2))
            markers = cv2.morphologyEx(markers, cv2.MORPH_CLOSE, kernel, iterations=1)
        elif per < 0.35:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
            markers = cv2.morphologyEx(thresh, cv2.MORPH_ERODE, kernel, iterations=2)
        else:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            markers = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel, iterations=1)

        arr = markers > 0
        markers = morphology.remove_small_objects(arr, min_size=2000, connectivity=1).astype(np.uint8)
        markers = morphology.remove_small_holes(markers.astype(np.bool), area_threshold=4000, connectivity=1)
        markers = markers.astype(np.uint8)
        # compute well area
        x_, y_, radius_ = self.p_circle(markers)
        image_r = np.copy(self.img)
        cv2.circle(image_r, (x_, y_), radius_, (35, 255, 12), 3)
        return image_r, x_, y_, radius_

    def eval_cords(self, cords_, x_, y_, radius_):
        cords_ = np.array(cords_)
        xp, yp, rdp = np.round(np.average(cords_[:, 0])), np.round(np.average(cords_[:, 1])), np.round(
            np.average(cords_[:, 2]))
        distance, rel = self.dist(np.array([x_, y_]), np.array([xp, yp])), np.round(min(rdp, radius_) / max(rdp, radius_), 2)
        if distance < 50 and rel > 0.92:
            return True
        else:
            return False

    def seq_circular(self, cords_):
        image_r, cords_ = np.copy(self.img), np.array(cords_)
        x_ = int(np.round(np.average(cords_[:, 0])))
        y_ = int(np.round(np.average(cords_[:, 1])))
        radius_ = int(np.round(np.average(cords_[:, 2])))
        cv2.circle(image_r, (x_, y_), radius_, (35, 255, 12), 3)
        return image_r, x_, y_, radius_

    def gray_circle(self, binary_g, x_, y_):
        contour = cv2.findContours(binary_g, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = contour[0] if len(contour) == 2 else contour[1]
        contour = sorted(contour, key=cv2.contourArea, reverse=True)
        (xr, yr), rad_r = cv2.minEnclosingCircle(contour[0])
        distance = self.dist(np.array([x_, y_]), np.array([xr, yr]))
        if distance < 30 and rad_r > 50:
            binary_g = np.zeros_like(binary_g, dtype=np.uint8)
            cv2.circle(binary_g, (x_, y_), int(rad_r), 255, -1)
        return binary_g

    def sobel_filter(self):
        ima_gray = cv2.cvtColor(self.img_, cv2.COLOR_BGR2GRAY)
        ima_norm = ima_gray / np.max(ima_gray)
        thresh_norm_ = threshold_otsu(ima_norm)
        enhanced_ima = 1 - np.exp(-ima_norm ** 2 / 0.5)
        ima = np.array(enhanced_ima * 255).astype(np.uint8)
        dx = cv2.Sobel(ima, cv2.CV_32F, 1, 0, ksize=3)
        dy = cv2.Sobel(ima, cv2.CV_32F, 0, 1, ksize=3)
        gx = cv2.convertScaleAbs(dx)
        gy = cv2.convertScaleAbs(dy)
        combined = cv2.addWeighted(gx, 2.5, gy, 2.5, 0)
        thresh_val_ = threshold_otsu(combined)
        thresh_sobel_ = np.array((255 * (combined > thresh_val_))).astype(np.uint8)
        return thresh_sobel_, thresh_val_, thresh_norm_

    def hsv_space(self):
        hsv = rgb2hsv(self.img_)
        image = (255 * hsv[:, :, 1]).astype(np.uint8)
        th_hsv_ = threshold_otsu(image)
        thresh_hsv = (255 * np.array(image > 30)).astype(np.uint8)
        return thresh_hsv, th_hsv_

    def roi_region(self, bin_img, x_, y_, radius_, val_):
        roi_img = np.zeros_like(bin_img, dtype=np.uint8)
        rad_n = radius_ - val_
        cv2.circle(roi_img, (x_, y_), rad_n, 255, -1)
        idx = np.where(roi_img == 255)
        roi_img[idx] = bin_img[idx]
        return roi_img

    def opera_sobel(self, bin_sobel_, x_, y_, radius_, ctr_):
        morph_img = self.roi_region(bin_sobel_, x_, y_, radius_, 40)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
        binary = cv2.morphologyEx(morph_img, cv2.MORPH_DILATE, kernel, iterations=1)
        if ctr_:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            binary = cv2.morphologyEx(binary, cv2.MORPH_ERODE, kernel, iterations=1)
            arr = binary > 0
            binary = morphology.remove_small_objects(arr, min_size=100, connectivity=1)
        else:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            binary = cv2.morphologyEx(binary, cv2.MORPH_ERODE, kernel, iterations=2)
            arr = binary > 0
            binary = morphology.remove_small_objects(arr, min_size=5, connectivity=1)

        binary = morphology.remove_small_holes(binary.astype(np.bool), area_threshold=100000, connectivity=1)
        binary = (255 * binary).astype(np.uint8)
        return binary

    def opera_sobel_hsv(self, bin_sob_hsv, x_, y_, radius_):
        morph_img = self.roi_region(bin_sob_hsv, x_, y_, radius_, 40)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(morph_img, cv2.MORPH_DILATE, kernel, iterations=1)
        binary = morphology.remove_small_holes(binary.astype(np.bool), area_threshold=1000, connectivity=1)
        binary = binary.astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        binary = cv2.morphologyEx(binary, cv2.MORPH_ERODE, kernel, iterations=1)
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (4, 4))
        binary = cv2.morphologyEx(binary, cv2.MORPH_ERODE, kernel, iterations=2)
        arr = binary > 0
        binary = morphology.remove_small_objects(arr, min_size=50, connectivity=1)
        binary = morphology.remove_small_holes(binary.astype(np.bool), area_threshold=50000, connectivity=1)
        binary = (255 * binary).astype(np.uint8)
        return binary

    def opera_gray(self, bin_gray_, x_, y_, radius_):
        morph_gray = self.roi_region(bin_gray_, x_, y_, radius_, 50)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(morph_gray, cv2.MORPH_OPEN, kernel, iterations=1)
        binary = morphology.remove_small_holes(binary.astype(np.bool), area_threshold=1000, connectivity=1)
        binary = binary.astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_ERODE, kernel, iterations=1)
        arr = binary > 0
        binary = morphology.remove_small_objects(arr, min_size=100, connectivity=1)
        binary = morphology.remove_small_holes(binary.astype(np.bool), area_threshold=50000, connectivity=1)
        binary = (255 * binary).astype(np.uint8)
        binary = self.gray_circle(binary, x_, y_)
        return binary

    def binary_regions(self, x_, y_, radius_):
        _, original_gray = self.preprocessing()
        thresh_gray = threshold_otsu(original_gray)
        norm_img = cv2.normalize(self.img, None, alpha=-0.1, beta=1.1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
        self.img_ = (255 * norm_img).astype(np.uint8)
        # ---> obtain binary regions of images
        bin_sobel, th_sobel, th_norm = self.sobel_filter()
        bin_hsv, th_hsv = self.hsv_space()
        bin_gray = cv2.threshold(original_gray, thresh_gray, 255, cv2.THRESH_TOZERO_INV)[1]
        # ---> choose better binary image
        param = np.round(thresh_gray * th_norm)
        if (param >= 70 and th_sobel <= 145) or (param >= 79 and th_sobel >= 150 and th_hsv > 133) or \
                (param >= 80 and th_sobel >= 150):
            rel_ = np.round(min(th_hsv, th_sobel) / max(th_hsv, th_sobel), 2)
            if 0.80 < rel_ < 0.95:
                ctr = True if param > 85 or th_sobel > 140 else False
                ima_binary = self.opera_sobel(bin_sobel, x_, y_, radius_, ctr)
                return ima_binary
            else:
                bin_hsv_sobel = cv2.bitwise_or(bin_sobel, bin_hsv)
                ima_binary = self.opera_sobel_hsv(bin_hsv_sobel, x_, y_, radius_)
                return ima_binary
        else:
            ima_binary = self.opera_gray(bin_gray, x_, y_, radius_)
        return ima_binary

    def well_analysis(self, img_s, x_, y_, radius_):
        binary = self.binary_regions(x_, y_, radius_)
        idx = np.where(binary == 255)
        seg_image = self.binary_contours(img_s, binary)
        # image binary result
        binary2 = np.zeros_like(binary, dtype=np.uint8)
        cv2.circle(binary2, (x_, y_), radius_ + 1, 255, 1)
        binary2[idx] = binary[idx]
        # compute segmented area
        area_detected_ = np.sum(binary == 255)
        # compute well area
        well = np.zeros_like(binary, dtype=np.uint8)
        cv2.circle(well, (x_, y_), radius_, 255, -1)
        area_well_ = np.sum(well == 255)
        percent_well_ = np.round((area_detected_ * 100) / area_well_, 2)
        return seg_image, percent_well_

    def well_main(self, des, img_r, ima_name, type_i, i, k, x_, y_, radius_):
        img_final, percent_well = self.well_analysis(img_r, x_, y_, radius_)
        # Output image
        nom_img_sp = ima_name.split('.')[0] + type_i
        root_des = os.path.join(des, nom_img_sp)
        plt.imsave(root_des, img_final)
        print('-------------------------------------------------------------------------')
        print('Processing image  ----->  ' + str(i))
        print('Loading buffer of Percentage AREA...:  ' + str(k + 1) + ' of ' + str(self.buffer_size))
        k, mean_area = self.buffer_mean(k, percent_well)
        table = [['Percentage Area  : ', str(percent_well)],
                 ['Mean Area        : ', str(mean_area)]]
        for line in table:
            print('{:>10} {:>10}'.format(*line))
        print('')
        return k, percent_well, mean_area, img_final

    def ini_well(self, img, cont_ini, cords_well, buffer_size):
        self.img, self.buffer_size = img, buffer_size
        if cont_ini < 6:
            ima_res, x, y, radius = self.well_region()
            cords_well.append([x, y, radius])
        else:
            _, x, y, radius = self.well_region()
            ctr_range = self.eval_cords(cords_well, x, y, radius)
            if ctr_range:
                cords_well.append([x, y, radius])
            ima_res, x, y, radius = self.seq_circular(cords_well)
        cont_ini += 1
        return cont_ini, cords_well, ima_res, x, y, radius


def save_csv_file(data_, des, header):
    # Save data in csv file
    _root_result = os.path.join(des, header+'.csv')
    data_.to_csv(_root_result, index=False)
    print('----------------------------------------------')
    print('..... Save data in CSV file successfully .....')
    print('----------------------------------------------')


def graph_data(des, header):
    _root_data = os.path.join(des, header+'.csv')
    data_ = pd.read_csv(_root_data)
    y = np.array(data_['Percentage'])
    x = np.arange(1, len(y) + 1, 1)
    fig = plt.figure()
    plt.plot(x, y, 'o')
    plt.grid()
    plt.xlabel('N. of image')
    plt.ylabel('Percentage')
    _root_fig = os.path.join(des, 'Percentage_'+header+'.jpg')
    fig.tight_layout()
    plt.savefig(_root_fig)
    plt.close()


