# Ramiro Isa-Jara, ramiro.isaj@gmail.com
# Vision Interface to use for viewing and saving images from Video Camera Input
# Activate Pump with Analysis of Area of yeast growing ----- version 0.2.3
# This program uses 2 threads to avoid errors during the execution

import cv2
import math
import threading
import time as tm
import numpy as np
import pandas as pd
import PySimpleGUI as sg
from datetime import datetime
import Vision_well_def as Vw
import Vision_Control_def as Vs
import matplotlib.pyplot as plt


def thread_images(path_des_, name_, type_i_, time1_, values_, image_):
    saveIm.save(path_des_, name_, type_i_, time1_, values_, image_)


def thread_pump1(fluid_h_, fluid_l_, time_h_, time_l_):
    pumpC.control_time(fluid_h_, fluid_l_, time_h_, time_l_)


def thread_pump2(fluid_h_, fluid_l_, area_h_, area_l_, time_h_, area_):
    pumpC.control_area(fluid_h_, fluid_l_, area_h_, area_l_, time_h_, area_)


# -------------------------------
# Adjust size screen
# -------------------------------
Screen_size = 10
# -------------------------------
sg.theme('LightGrey1')
m1, n1 = 550, 300
img = np.ones((m1, n1, 1), np.uint8)*255

f1 = np.array([60])
fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
ax.plot(f1, 'o-')
ax.grid()

# --------------------------------------------------------------------------------------------------
portsWIN = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM10', 'COM11']
portsLIN = ['/dev/pts/2', '/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2', '/dev/ttyS3']

layout1 = [[sg.Radio('Windows', "RADIO1", enable_events=True, default=True, key='_SYS_')],
           [sg.Radio('Linux / Mac', "RADIO1", enable_events=True, key='_LIN_')], [sg.Text('')]]

layout2 = [[sg.Checkbox('*.jpg', default=True, key="_IN1_")], [sg.Checkbox('*.png', default=False, key="_IN2_")],
           [sg.Checkbox('*.tiff', default=False, key="_IN3_")]]

idx = ['0']
layout3 = [[sg.Radio('Minutes', "RADIO2", enable_events=True, default=True, key='_TMI_'),
           sg.Radio('Seconds ', "RADIO2", enable_events=True, key='_TSE_')],
           [sg.Text('Time to wait:', size=(10, 1)), sg.InputText('5', key='_INF_', enable_events=True, size=(7, 1))],
           [sg.Text('Id_ini image:', size=(10, 1)), sg.InputText('1', key='_IDI_', size=(7, 1))],
           [sg.Text('Video input: ', size=(10, 1)),
            sg.Combo(values=idx, size=(6, 1), enable_events=True, key='_VIN_')]]

layout3a = [[sg.T('', size=(5, 1)), sg.Radio('Control - Area', "RADIO3", enable_events=True, default=True,
             text_color='DarkBlue', key='_CTA_'),
             sg.T('', size=(7, 1)), sg.Radio('Control - Time', "RADIO3", enable_events=True, key='_CTT_',
            text_color='DarkBlue'), sg.T('', size=(5, 1))],
            [sg.Text('Buffer size:', size=(10, 1)), sg.InputText('5', key='_BUF_', size=(7, 1)),
             sg.Text('img.', size=(5, 1))],
            [sg.Text('Area MAX:', size=(10, 1)), sg.InputText('50', key='_AMX_', size=(7, 1), enable_events=True),
             sg.Text('%', size=(5, 1)),
             sg.Text('Time MIN fluid:', size=(14, 1)), sg.InputText('40', key='_TLS_', size=(7, 1), enable_events=True),
             sg.Text('min', size=(4, 1))],
            [sg.Text('Area MIN:', size=(10, 1)), sg.InputText('20', key='_AMN_', size=(7, 1), enable_events=True),
             sg.Text('%', size=(5, 1)),
             sg.Text('Time MAX fluid:', size=(14, 1)), sg.InputText('1', key='_THS_', size=(7, 1), enable_events=True),
             sg.Text('min', size=(4, 1))]]


layout4a = [[sg.Text('Radius Well: ', size=(12, 1)), sg.InputText('700', size=(6, 1), key='_RAW_'),
            sg.Text('um.', size=(8, 1))],
            [sg.Text('* Lowest fluid:', size=(12, 1)),
             sg.InputText('1', key='_LST_', size=(6, 1), enable_events=True), sg.Text('ul/min.', size=(5, 1))],
            [sg.Text('* Highest fluid:', size=(12, 1)),
             sg.InputText('100', key='_HST_', size=(6, 1), enable_events=True), sg.Text('ul/min.', size=(5, 1))]]

layout4b = [[sg.Text('Name: ', size=(9, 1)),
            sg.Combo(values=portsWIN, size=(9, 1), enable_events=True, key='_PORT_')],
            [sg.Text('Baudrate:', size=(9, 1)), sg.InputText('9600', key='_RTE_', size=(10, 1))],
            [sg.Text('Status:', size=(8, 1)), sg.Text('NOT CONNECT', size=(13, 1), key='_CON_', text_color='red')]]

layout5 = [[sg.Text('Name images: ', size=(12, 1)), sg.InputText('Experiment1_', size=(31, 1), key='_NAM_')],
           [sg.Text('Source path: ', size=(12, 1)), sg.InputText(size=(31, 1), key='_SOU_'), sg.FolderBrowse()],
           [sg.Text('Destiny path: ', size=(12, 1)), sg.InputText(size=(31, 1), key='_DES_'), sg.FolderBrowse()]]


layout7 = [[sg.T("", size=(15, 1)), sg.Text('Current time: ', size=(10, 1)), sg.Text('', size=(10, 1), key='_TAC_')],
           [sg.T("", size=(2, 1)),
            sg.Text('Start time: ', size=(8, 1)), sg.Text('-- : -- : --', size=(10, 1), key='_TIN_', text_color='blue'),
            sg.T("", size=(7, 1)),
            sg.Text('Finish time: ', size=(9, 1)), sg.Text('-- : -- : --', size=(10, 1), key='_TFI_', text_color='red')],
           [sg.Text('Waiting time: ', size=(11, 1)), sg.InputText('', key='_RES_', size=(12, 1)),
            sg.Text('...', size=(4, 1), key='_ITM_'),
            sg.Text('Total/images: ', size=(12, 1)), sg.InputText('', key='_CIM_', size=(10, 1))],
           [sg.Text('Name Image: ', size=(11, 1)), sg.InputText('', key='_NIM_', size=(12, 1)),
            sg.Text(' ', size=(4, 1)),
            sg.Text('Current Area: ', size=(12, 1)), sg.InputText('', key='_CAR_', size=(10, 1))],
           [sg.Text('Buffer image: ', size=(11, 1)), sg.InputText('', key='_BUM_', size=(12, 1)),
            sg.Text(' ', size=(4, 1)),
            sg.Text('Mean Area:', size=(12, 1)), sg.InputText('', key='_MAR_', size=(10, 1))]
           ]

v_img = [sg.Image(filename='', key="_IMA_")]
# columns
col_1 = [[sg.Frame('', [v_img])], [sg.T("", size=(5, 1))], [sg.Text('Percentage of Area:', size=(18, 1), text_color='DarkRed')], [sg.Canvas(key="_CANVAS_")]]
col_2 = [[sg.Frame('Operative System: ', layout1, title_color='Blue'),
          sg.Frame('Type image: ', layout2, title_color='Blue'), sg.Frame('Image settings: ', layout3, title_color='Blue')],
         [sg.Frame('Save directories: ', layout5, title_color='Blue')],
         [sg.Frame('Control settings: ', layout3a, title_color='Blue')],
         [sg.Frame('Pump settings: ', layout4a, title_color='Blue'),
          sg.Frame('Port settings: ', layout4b, title_color='Blue')],
         [sg.T(" ", size=(4, 1)), sg.Button('View', size=(8, 1)), sg.Button('Save', size=(8, 1)),
          sg.Button('Start', size=(8, 1)), sg.Button('Finish', size=(8, 1))],
         [sg.Frame('', layout7)]]

layout = [[sg.Column(col_1), sg.Column(col_2)]]

# Create the Window
window = sg.Window('Vision_MT Well-Control', layout, font="Helvetica "+str(Screen_size), finalize=True)
window['_IMA_'].update(data=Vs.bytes_(img, m1, n1))
graph = Vs.draw_figure(window["_CANVAS_"].TKCanvas, fig)
# ----------------------------------------------------------------------------------
time_, id_image, time_h, time_l, fluid_h, fluid_l, port_name, bauds_, = 0, 1, 0, 0, 0, 0, 0, 0
area_h, area_l, c_port, id_sys, time_read, area_seq, area_total = 0, 0, -1, 0, 0, 0, 0
ctr_exp, binary_ref, percent_ref, cont_z = 0, 0, 0, 0
view_, save_, pump_, control, ctr_method = False, False, False, True, False
video, name, image, ini_time, ini_time_, path_ori, path_des, type_i = None, None, None, None, None, None, None, None
saveIm, pumpC, readIm, cords_well, cont_ini, i, k, buffer, buffer_size, p_area = None, None, None, [], 0, 0, 0, 0, 0, []
results = pd.DataFrame(columns=['Image', 'Percentage', 'Area'])
segYes = Vw.SegmentYeast()
segYes.build_filters()
# -----------------------------------------------------------------------------------

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read(timeout=50)
    window.Refresh()
    now = datetime.now()
    now_time = now.strftime("%H : %M : %S")
    window['_TAC_'].update(now_time)

    if event == sg.WIN_CLOSED:
        break

    if event == '_VIN_':
        index = Vs.camera_idx()
        window.Element('_VIN_').update(values=index)

    if event == '_LIN_':
        id_sys = 1
        window.Element('_PORT_').update(values=portsLIN)
    if event == '_SYS_':
        id_sys = 0
        window.Element('_PORT_').update(values=portsWIN)

    if event == '_INF_':
        if values['_INF_'] != '':
            time_ = int(values['_INF_']) if int(values['_INF_']) > 0 else 1

    if event == '_HST_':
        if values['_HST_'] != '':
            fluid_h = int(values['_HST_']) if int(values['_HST_']) > 10 else 0
    if event == '_THS_':
        if values['_THS_'] != '':
            time_h = float(values['_THS_']) if float(values['_THS_']) > 1 else 1
    if event == '_LST_':
        if values['_LST_'] != '':
            fluid_l = int(values['_LST_']) if int(values['_LST_']) > 1 else 0
    if event == '_TLS_':
        if values['_TLS_'] != '':
            time_l = float(values['_TLS_']) if float(values['_TLS_']) > 1 else 1

    if event == '_PORT_':
        port_name = values['_PORT_']
        bauds_ = int(values['_RTE_'])
        sg.Popup('Serial Port: ', values['_PORT_'])
        c_port = Vs.serial_test(port_name, bauds_)
        text = 'CONNECT' if c_port == 1 else 'ERROR'
        window.Element('_CON_').update(text)

    if event == 'Finish':
        print('FINISH')
        window['_IMA_'].update(data=Vs.bytes_(img, m1, n1))
        if pump_:
            ax.clear()
            ax.plot(f1, 'o-')
            ax.grid()
            graph.draw()
            # -------------------------------------------------------------------------------
            header = values['_NAM_'].split('_')[0]
            Vw.save_csv_file(results, path_des, header)
            Vw.graph_data(path_des, header)
            for i in range(1, 100, 25):
                sg.OneLineProgressMeter('Saving RESULTS in CSV files', i + 25, 100, 'single')
                tm.sleep(1)
            pumpC.stop_pump()
            # ---------------------------------------------------------------------------------
        pump_, ctr_method = False, False
        cords_well, buffer, p_area, buffer_size, cont_ini, i, k = [], [], [], 0, 0, 0, 0
        if view_:
            window.find_element('View').Update(disabled=False)
            now_time = now.strftime("%H : %M : %S")
            window['_TFI_'].update(now_time)
            view_, save_ = False, False
            video.release()

    if event == 'View':
        idx = values['_VIN_']
        if view_ is False and idx != '':
            video = cv2.VideoCapture(int(idx))
            video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            width, height = 1280, 720
            video.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            video.set(cv2.CAP_PROP_FRAME_HEIGHT, height
            now_time1 = now.strftime("%H : %M : %S")
            window['_TIN_'].update(now_time1)
            window['_TFI_'].update('-- : -- : --')
            view_ = True
            window.find_element('View').update(disabled=True)
        elif idx == '':
            sg.Popup('Error', ['Not selected Input Video'])
        else:
            sg.Popup('Warning', ['Process is running'])

    if view_:
        ret, image = video.read()
        if ret:
            window['_IMA_'].update(data=Vs.bytes_(image, m1, n1))

    if event == 'Save':
        print('SAVE PROCESS')
        id_image = int(values['_IDI_'])
        if values['_SYS_']:
            path_ori = Vs.update_dir(values['_SOU_']) + "\\"
            path_ori = r'{}'.format(path_ori)
        else:
            path_ori = values['_SOU_'] + '/'
        # -------------------------------------------------------------------
        if values['_TMI_']:
            window['_ITM_'].update('min')
        else:
            window['_ITM_'].update('sec')
        # -------------------------------------------------------------------
        if values['_IN2_']:
            type_i = ".png"
        elif values['_IN3_']:
            type_i = ".tiff"
        else:
            type_i = ".jpg"
        # ------------------------------------------------------------------
        if view_ and len(path_ori) > 1 and save_ is False:
            ini_time = datetime.now()
            time_ = float(values['_INF_'])
            saveIm = Vs.SaveImages(window, id_image, ini_time)
            name = values['_NAM_']
            save_ = True
        elif view_ and len(path_ori) > 1 and save_:
            sg.Popup('Warning', ['Save images is running...'])
        else:
            sg.Popup('Error', ['Information or process is wrong.'])

    if save_:
        thread = threading.Thread(name="Thread-{}".format(1),
                                  target=thread_images(path_ori, name, type_i, time_, values, image), args=(saveIm,))
        thread.setDaemon(True)
        thread.start()

    if event == 'Start':
        radius = float(values['_RAW_'])
        area_total = np.round(math.pi * radius ** 2, 2)
        if values['_SYS_']:
            path_des = Vs.update_dir(values['_DES_']) + "\\"
            path_des = r'{}'.format(path_des)
        else:
            path_des = values['_DES_'] + '/'
        # -------------------------------------
        fluid_h = int(values['_HST_'])
        fluid_l = int(values['_LST_'])
        # -------------------------------------
        if c_port == 1 and len(path_des) > 1 and pump_ is False:
            ini_time = datetime.now()
            time_read = np.round(1.10*time_, 2)
            if values['_CTA_']:
                ctr_method = True
                readIm = Vw.ReadLastImage(path_ori, type_i, id_image, ini_time, id_sys)
                area_h = float(values['_AMX_'])
                area_l = float(values['_AMN_'])
                buffer_size = int(values['_BUF_'])
            else:
                time_h = float(values['_THS_'])
                time_l = float(values['_TLS_'])
            # -------------------------------------
            ini_time_ = datetime.now()
            pumpC = Vs.ControlPump(window, ini_time_, control, port_name, bauds_)
            pump_ = True
        elif c_port == 1 and len(path_des) > 1 and pump_:
            sg.Popup('Warning', ['Control system is running..'])
        else:
            sg.Popup('Error', ['Port not connected or Information is wrong.'])

    if pump_:
        if ctr_method:
            confirm = readIm.ready_img(time_read, values, i)
            if confirm:
                image_l, name_l = readIm.load_image()
                cont_ini, cords_well, ima_res, x, y, radius = segYes.ini_well(image_l, cont_ini, cords_well, buffer_size)
                k, percentage_well, img_f, binary_ref, percent_ref, cont_z, mean_area = segYes.well_main(
                                                                                     path_des, ima_res, name_l, i, k,
                                                                                     ctr_exp, binary_ref, percent_ref,
                                                                                     cont_z, x, y, radius)
                area_yeast = np.round((area_total * percentage_well) / 100, 2)
                results = results.append({'Image': name_l, 'Percentage': percentage_well, 'Area': area_yeast},
                                         ignore_index=True)
                window['_IMA_'].update(data=Vs.bytes_(img_f, m1, n1))
                window['_NIM_'].update(name_l)
                window['_CAR_'].update(percentage_well)
                window['_BUM_'].update(k)
                # -----------------------------------------------
                if mean_area > 0:
                    area_seq = np.copy(mean_area)
                    window['_MAR_'].update(mean_area)
                    if ctr_exp == 0 and mean_area > area_h:
                        ini_time = datetime.now()
                        ctr_exp = 1
                        time_read = np.round(1.10*time_h, 2)
                        save_high_ = True
                        saveIm = Vs.SaveImages(window, i, ini_time)
                    if ctr_exp == 1 and mean_area < area_l:
                        ini_time = datetime.now()
                        ctr_exp = 0
                        time_read = np.round(1.10 * time_, 2)
                        saveIm = Vs.SaveImages(window, i, ini_time)
                # -----------------------------------------------
                    p_area.append(mean_area)
                    values_area = np.array(p_area)
                    ax.clear()
                    ax.plot(values_area, 'o-')
                    ax.grid()
                    graph.draw()
                # -----------------------------------------------
                i += 1

            thread = threading.Thread(name="Thread-{}".format(2),
                                      target=thread_pump2(fluid_h, fluid_l, area_h, area_l, time_h, area_seq),
                                      args=(pumpC,))
            thread.setDaemon(True)
            thread.start()

        else:
            thread = threading.Thread(name="Thread-{}".format(2),
                                      target=thread_pump1(fluid_h, fluid_l, time_h, time_l), args=(pumpC,))
            thread.setDaemon(True)
            thread.start()

    # processing threads and join in main thread to next iteration
    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()


print('CLOSE WINDOW')
window.close()
