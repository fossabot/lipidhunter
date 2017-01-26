# -*- coding: utf-8 -*-
# Copyright 2015-2017 Zhixu Ni, AG Bioanalytik, BBZ, University of Leipzig.
# The software is currently  under development and is not ready to be released.
# A suitable license will be chosen before the official release of oxLPPdb.
# For more info please contact: zhixu.ni@uni-leipzig.de

# try:  # python3
#     import configparser
# except NameError:  # python2
#     import ConfigParser as configparser

import ConfigParser as configparser
import glob
import os
import re
import time

import pandas as pd
from PySide import QtCore, QtGui

from LibLipidHunter import ExtractorMZML
from LibLipidHunter.LinkerMZML import hunt_link
from LibLipidHunter.LipidHunter_UI import Ui_MainWindow
from LibLipidHunter.HunterCore import huntlipids

import FileDialog


class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # links
        self.ui.logo_lb.setOpenExternalLinks(True)
        self.ui.tab_c_3_lb.setOpenExternalLinks(True)
        self.ui.tab_c_5_lb.setOpenExternalLinks(True)

        # slots for tab a
        QtCore.QObject.connect(self.ui.tab_a_addmzml_pb, QtCore.SIGNAL("clicked()"), self.a_load_mzml)
        QtCore.QObject.connect(self.ui.tab_a_addmzmlfolder_pb, QtCore.SIGNAL("clicked()"), self.a_load_mzmlfolder)
        QtCore.QObject.connect(self.ui.tab_a_clearall_pb, QtCore.SIGNAL("clicked()"), self.ui.tab_a_infiles_pte.clear)
        QtCore.QObject.connect(self.ui.tab_a_savexlsxfolder_pb, QtCore.SIGNAL("clicked()"), self.a_save_xls2folder)
        QtCore.QObject.connect(self.ui.tab_a_savecsv_pb, QtCore.SIGNAL("clicked()"), self.a_save_csv2folder)
        QtCore.QObject.connect(self.ui.tab_a_runextractor_pb, QtCore.SIGNAL("clicked()"), self.a_run_extractor)
        QtCore.QObject.connect(self.ui.tab_a_runmerge_pb, QtCore.SIGNAL("clicked()"), self.a_run_merger)

        # slots for tab b
        QtCore.QObject.connect(self.ui.tab_b_addmzml_pb, QtCore.SIGNAL("clicked()"), self.b_load_mzml)
        QtCore.QObject.connect(self.ui.tab_b_addmzmlfolder_pb, QtCore.SIGNAL("clicked()"), self.b_load_mzmlfolder)
        QtCore.QObject.connect(self.ui.tab_b_clearall_pb, QtCore.SIGNAL("clicked()"), self.ui.tab_b_infiles_pte.clear)
        QtCore.QObject.connect(self.ui.tab_b_savexlsxfolder_pb, QtCore.SIGNAL("clicked()"), self.b_save_xls2folder)
        QtCore.QObject.connect(self.ui.tab_b_runextract_pb, QtCore.SIGNAL("clicked()"), self.b_run_extractor)

        # slots for tab d
        QtCore.QObject.connect(self.ui.tab_d_lipidstable_pb, QtCore.SIGNAL("clicked()"), self.d_load_lipidstable)
        QtCore.QObject.connect(self.ui.tab_d_ms2info_pb, QtCore.SIGNAL("clicked()"), self.d_load_ms2info)
        QtCore.QObject.connect(self.ui.tab_d_ms2mzml_pb, QtCore.SIGNAL("clicked()"), self.d_load_mzml)
        QtCore.QObject.connect(self.ui.tab_d_xlsxpath_pb, QtCore.SIGNAL("clicked()"), self.d_save_output)
        QtCore.QObject.connect(self.ui.tab_d_runextract_pb, QtCore.SIGNAL("clicked()"), self.d_run_linker)

        # slots for tab e
        QtCore.QObject.connect(self.ui.tab_e_loadxlsxpath_pb, QtCore.SIGNAL("clicked()"), self.e_load_lipidsinfo)
        QtCore.QObject.connect(self.ui.tab_e_ms2mzml_pb, QtCore.SIGNAL("clicked()"), self.e_load_mzml)
        QtCore.QObject.connect(self.ui.tab_e_saveimgfolder_pb, QtCore.SIGNAL("clicked()"), self.e_save_img2folder)
        QtCore.QObject.connect(self.ui.tab_e_sumxlsxpath_pb, QtCore.SIGNAL("clicked()"), self.e_save_output)
        QtCore.QObject.connect(self.ui.tab_d_runhunter_pb, QtCore.SIGNAL("clicked()"), self.e_run_hunter)
        # slots for tab f
        QtCore.QObject.connect(self.ui.tab_f_fawhitelist_pb, QtCore.SIGNAL("clicked()"), self.f_load_fawhitelist)
        QtCore.QObject.connect(self.ui.tab_f_hgcfg_pb, QtCore.SIGNAL("clicked()"), self.f_load_hgcfg)
        QtCore.QObject.connect(self.ui.tab_f_scorecfg_pb, QtCore.SIGNAL("clicked()"), self.f_load_scorecfg)
        QtCore.QObject.connect(self.ui.tab_f_savesettings_pb, QtCore.SIGNAL("clicked()"), self.f_set_default_cfg)

        # load configurations
        config = configparser.ConfigParser()
        config.read('config.ini')
        if config.has_section('settings'):
            user_cfg = 'settings'
        else:
            if config.has_section('default'):
                user_cfg = 'default'
            else:
                user_cfg = ''
        if len(user_cfg) > 2:
            options = config.options(user_cfg)
            if 'fa_white_list_cfg' in options:
                self.ui.tab_f_fawhitelist_le.setText(config.get(user_cfg, 'fa_white_list_cfg'))
            if 'lipid_specific_cfg' in options:
                self.ui.tab_f_hgcfg_le.setText(config.get(user_cfg, 'lipid_specific_cfg'))
            if 'score_cfg' in options:
                self.ui.tab_f_scorecfg_le.setText(config.get(user_cfg, 'score_cfg'))

    @staticmethod
    def get_same_files(folder, filetype_lst):
        """
        find all files with same type in specified folder
        :param str folder: absolute file path
        :param list filetype_lst: e.g. ['*.mzml', '*.mzML']
        :return: a list of absolute file path
        :rtype: list
        """
        if folder is not u'':
            os.chdir(folder)
            _pre_found_lst = []
            for _filetype in filetype_lst:
                _tmp_found_lst = glob.glob(_filetype)
                # merge list
                _pre_found_lst += [f for f in _tmp_found_lst if f not in _pre_found_lst]
            filename_lst = _pre_found_lst
            abs_path_lst = list(os.path.abspath(ff) for ff in _pre_found_lst)
        else:
            filename_lst = []
            abs_path_lst = []

        return filename_lst, abs_path_lst

    def a_load_mzml(self):
        # check existed files
        _loaded_files = str(self.ui.tab_a_infiles_pte.toPlainText())
        _loaded_lst = _loaded_files.split('\n')

        a_load_mzml_dialog = QtGui.QFileDialog(self)
        a_load_mzml_dialog.setNameFilters([u'mzML spectra files (*.mzML *.mzml)'])
        a_load_mzml_dialog.selectNameFilter(u'mzML spectra files (*.mzML *.mzml)')
        if a_load_mzml_dialog.exec_():
            a_load_mzml_str = a_load_mzml_dialog.selectedFiles()[0]
            a_load_mzml_str = os.path.abspath(a_load_mzml_str)
            if a_load_mzml_str not in _loaded_lst:
                self.ui.tab_a_infiles_pte.insertPlainText(unicode(a_load_mzml_str))  # take unicode only
                self.ui.tab_a_infiles_pte.insertPlainText(u'\n')
            else:
                _msgBox = QtGui.QMessageBox()
                _msgBox.setText(u'Spectrum has been chosen already.')
                _msgBox.exec_()

    def a_load_mzmlfolder(self):
        # check existed files
        _loaded_files = str(self.ui.tab_a_infiles_pte.toPlainText())
        _loaded_lst = _loaded_files.split('\n')
        a_load_mzmlfolder_str = QtGui.QFileDialog.getExistingDirectory()
        _mzml_name_lst, _mzml_path_lst = self.get_same_files(a_load_mzmlfolder_str, filetype_lst=['*.mzml', '*.mzML'])
        _duplicated_str = ''
        for _mzml in _mzml_path_lst:
            if _mzml not in _loaded_lst:
                self.ui.tab_a_infiles_pte.insertPlainText(unicode(_mzml))
                self.ui.tab_a_infiles_pte.insertPlainText(u'\n')
            else:
                _duplicated_str = _duplicated_str + unicode(_mzml) + u'\n'
        if len(_duplicated_str) > 0:
            _msgBox = QtGui.QMessageBox()
            _msgBox.setText(_duplicated_str + u'Already chosen. \n Skipped')
            _msgBox.exec_()

    def a_save_xls2folder(self):
        a_save_xlsfolder_str = QtGui.QFileDialog.getExistingDirectory()
        self.ui.tab_a_xlsxfolder_le.setText(unicode(a_save_xlsfolder_str))

    def a_save_csv2folder(self):
        a_save_csvfolder_str = QtGui.QFileDialog.getSaveFileName(caption=u'Save file', filter=u'.csv')
        self.ui.tab_a_csvfolder_le.setText(unicode(a_save_csvfolder_str[0]))

    def a_run_extractor(self):
        if self.ui.vendor_waters_rb.isChecked():
            usr_vendor = 'waters'
        elif self.ui.vendor_thermo_rb.isChecked():
            usr_vendor = 'thermo'
        else:
            usr_vendor = 'waters'
        print('Vendor mode = %s' % usr_vendor)
        self.ui.tab_a_statusextractor_pte.clear()
        a_ms_th = self.ui.tab_a_msthreshold_spb.value()
        self.ui.tab_a_statusextractor_pte.insertPlainText(unicode('MS threshold (absolute): %i \n' % a_ms_th))
        extractor = ExtractorMZML.Extractor()
        _loaded_mzml_files = str(self.ui.tab_a_infiles_pte.toPlainText())
        _loaded_mzml_lst = _loaded_mzml_files.split('\n')

        _save_xlsx_folder_str = str(self.ui.tab_a_xlsxfolder_le.text())

        for _mzml in _loaded_mzml_lst:
            print('_mzml', _mzml)
            print('MS_TH', a_ms_th, type(a_ms_th))
            if os.path.isfile(_mzml):
                _mzml_path, _mzml_name = os.path.split(_mzml)
                self.ui.tab_a_statusextractor_pte.insertPlainText(unicode('Start processing...\n%s \n' % _mzml))

                _xlsx_path = _save_xlsx_folder_str + '\\' + _mzml_name[:-4] + 'xlsx'
                _ms_df = extractor.get_ms_all(_mzml, a_ms_th, vendor=usr_vendor)
                # _ms_df = _ms_df.drop_duplicates(subset=['mz'], keep='first')
                _ms_df.to_excel(_xlsx_path)
                self.ui.tab_a_statusextractor_pte.insertPlainText(unicode('Save as: \n%s.xlsx \n' % _mzml[0:-4]))
        self.ui.tab_a_statusextractor_pte.insertPlainText(u'Finished!')

    def a_run_merger(self):
        self.ui.tab_a_statusmerger_pte.insertPlainText(u'Start to proceed...')

        _save_csv_str = str(self.ui.tab_a_csvfolder_le.text())

        _save_xlsx_folder_str = str(self.ui.tab_a_xlsxfolder_le.text())

        _xlsx_name_lst, _xlsx_path_lst = self.get_same_files(_save_xlsx_folder_str, filetype_lst=['*.xlsx', '*.XLSX'])
        cm_pkl_lst = zip(_xlsx_name_lst, _xlsx_path_lst)

        cm_pkl_df = pd.DataFrame()
        for _cm in cm_pkl_lst:
            self.ui.tab_a_statusmerger_pte.insertPlainText(unicode('reading --> %s \n' % _cm[0]))
            _tmp_df = pd.read_excel(_cm[1])
            _tmp_df['file'] = _cm[0]
            cm_pkl_df = cm_pkl_df.append(_tmp_df)

        cm_pkl_df = cm_pkl_df[['mz', 'i']]
        cm_pkl_df = cm_pkl_df.sort_values(by=['mz', 'i'], ascending=[True, False])
        cm_pkl_df = cm_pkl_df.drop_duplicates(subset=['mz'], keep='first')
        cm_pkl_df = cm_pkl_df.reset_index(drop=True)

        if cm_pkl_df.shape[0] > 500000:
            cm_pkl_df_p1 = cm_pkl_df[:500000, :]
            print cm_pkl_df_p1.shape
            cm_pkl_df_p1.to_csv(''.join([_save_csv_str[0:-4], ['_1.csv']]))
            cm_pkl_df_p2 = cm_pkl_df[500000:, :]
            print cm_pkl_df_p2.shape
            cm_pkl_df_p2.to_csv(''.join([_save_csv_str[0:-4], ['_2.csv']]))
            _save_csv_str = ''.join([_save_csv_str[0:-4], ['_1.csv'], '\n', _save_csv_str[0:-4], ['_2.csv']])
        else:
            cm_pkl_df.to_csv(_save_csv_str)

        self.ui.tab_a_statusmerger_pte.insertPlainText(unicode('Merged and saved as %s' % _save_csv_str))

    def b_load_mzml(self):
        # check existed files
        _loaded_files = str(self.ui.tab_b_infiles_pte.toPlainText())
        _loaded_lst = _loaded_files.split('\n')

        b_load_mzml_dialog = QtGui.QFileDialog(self)
        b_load_mzml_dialog.setNameFilters([u'mzML spectra files (*.mzML *.mzml)'])
        b_load_mzml_dialog.selectNameFilter(u'mzML spectra files (*.mzML *.mzml)')
        if b_load_mzml_dialog.exec_():
            b_load_mzml_str = b_load_mzml_dialog.selectedFiles()[0]
            b_load_mzml_str = os.path.abspath(b_load_mzml_str)
            if b_load_mzml_str not in _loaded_lst:
                self.ui.tab_b_infiles_pte.insertPlainText(unicode(b_load_mzml_str))  # take unicode only
                self.ui.tab_b_infiles_pte.insertPlainText(u'\n')
            else:
                _msgBox = QtGui.QMessageBox()
                _msgBox.setText(u'Spectrum has been chosen already.')
                _msgBox.exec_()

    def b_load_mzmlfolder(self):
        # check existed files
        _loaded_files = str(self.ui.tab_b_infiles_pte.toPlainText())
        _loaded_lst = _loaded_files.split('\n')

        b_load_mzmlfolder_str = QtGui.QFileDialog.getExistingDirectory()
        _mzml_name_lst, _mzml_path_lst = self.get_same_files(b_load_mzmlfolder_str, filetype_lst=['*.mzml', '*.mzML'])
        _duplicated_str = ''
        for _mzml in _mzml_path_lst:
            if _mzml not in _loaded_lst:
                self.ui.tab_b_infiles_pte.insertPlainText(unicode(_mzml))
                self.ui.tab_b_infiles_pte.insertPlainText(u'\n')
            else:
                _duplicated_str = _duplicated_str + unicode(_mzml) + u'\n'
        if len(_duplicated_str) > 0:
            _msgBox = QtGui.QMessageBox()
            _msgBox.setText(_duplicated_str + u'Already chosen. \n Skipped')
            _msgBox.exec_()

    def b_save_xls2folder(self):
        b_save_xlsfolder_str = QtGui.QFileDialog.getExistingDirectory()
        self.ui.tab_b_outpufolder_le.setText(unicode(b_save_xlsfolder_str))
        
    def b_run_extractor(self):
        if self.ui.vendor_waters_rb.isChecked():
            usr_vendor = 'waters'
        elif self.ui.vendor_thermo_rb.isChecked():
            usr_vendor = 'thermo'
        else:
            usr_vendor = 'waters'
        print('Vendor mode = %s' % usr_vendor)
        self.ui.tab_b_statusrun_pte.clear()
        b_ms_th = self.ui.tab_b_msthreshold_spb.value()
        b_ms2_th = self.ui.tab_b_ms2threshold_spb.value()
        self.ui.tab_b_statusrun_pte.insertPlainText(unicode('MS threshold (absolute): %i \n' % b_ms_th))
        extractor = ExtractorMZML.Extractor()
        _loaded_mzml_files = str(self.ui.tab_b_infiles_pte.toPlainText())
        _loaded_mzml_lst = _loaded_mzml_files.split('\n')

        _save_xlsx_folder_str = str(self.ui.tab_b_outpufolder_le.text())

        for _mzml in _loaded_mzml_lst:
            if os.path.isfile(_mzml):
                _mzml_path, _mzml_name = os.path.split(_mzml)
                self.ui.tab_b_statusrun_pte.insertPlainText(unicode('Start processing...\n%s \n' % _mzml))

                _xlsx_path = _save_xlsx_folder_str + '\\' + _mzml_name[:-5] + '_all_scan_info.xlsx'
                _xlsx_ms2_path = _save_xlsx_folder_str + '\\' + _mzml_name[:-5] + '_ms2_info.xlsx'
                _ms_df = extractor.get_scan_events(_mzml, b_ms_th, b_ms2_th, vendor=usr_vendor)
                # _ms_df = _ms_df.drop_duplicates(subset=['mz'], keep='first')
                _ms_df.to_excel(_xlsx_path)
                _ms_df['function'] = _ms_df['function'].astype(int)
                _ms2_df = _ms_df[_ms_df['function'] > 1]
                _ms2_df = _ms2_df.reset_index()
                _ms2_df.to_excel(_xlsx_ms2_path)
                self.ui.tab_b_statusrun_pte.insertPlainText(unicode('Save as: \n%s.xlsx \n' % _mzml[0:-4]))
        self.ui.tab_b_statusrun_pte.insertPlainText(u'Finished!')

    def d_load_lipidstable(self):
        d_load_lipidstable_dialog = QtGui.QFileDialog(self)
        d_load_lipidstable_dialog.setNameFilters([u'MS Excel files (*.xlsx *.XLSX)'])
        d_load_lipidstable_dialog.selectNameFilter(u'MS Excel files (*.xlsx *.XLSX)')
        if d_load_lipidstable_dialog.exec_():
            self.ui.tab_d_lipidstable_le.clear()
            d_load_xlsx_str = d_load_lipidstable_dialog.selectedFiles()[0]
            d_load_xlsx_str = os.path.abspath(d_load_xlsx_str)
            self.ui.tab_d_lipidstable_le.setText(unicode(d_load_xlsx_str))

    def d_load_ms2info(self):
        d_load_ms2info_dialog = QtGui.QFileDialog(self)
        d_load_ms2info_dialog.setNameFilters([u'MS Excel files (*.xlsx *.XLSX)'])
        d_load_ms2info_dialog.selectNameFilter(u'MS Excel files (*.xlsx *.XLSX)')
        if d_load_ms2info_dialog.exec_():
            self.ui.tab_d_ms2info_le.clear()
            d_load_mzml_str = d_load_ms2info_dialog.selectedFiles()[0]
            d_load_mzml_str = os.path.abspath(d_load_mzml_str)
            self.ui.tab_d_ms2info_le.setText(unicode(d_load_mzml_str))

    def d_load_mzml(self):
        d_load_mzml_dialog = QtGui.QFileDialog(self)
        d_load_mzml_dialog.setNameFilters([u'mzML spectra files (*.mzML *.mzml)'])
        d_load_mzml_dialog.selectNameFilter(u'mzML spectra files (*.mzML *.mzml)')
        if d_load_mzml_dialog.exec_():
            self.ui.tab_d_ms2mzml_le.clear()
            d_load_mzml_str = d_load_mzml_dialog.selectedFiles()[0]
            d_load_mzml_str = os.path.abspath(d_load_mzml_str)
            self.ui.tab_d_ms2mzml_le.setText(unicode(d_load_mzml_str))

    def d_save_output(self):
        d_save_output_path = QtGui.QFileDialog.getSaveFileName(caption=u'Save file', filter=u'.xlsx')
        self.ui.tab_d_xlsxpath_le.clear()
        d_save_output_str = os.path.abspath(d_save_output_path[0])
        self.ui.tab_d_xlsxpath_le.setText(unicode(d_save_output_str))

    def d_run_linker(self):
        if self.ui.vendor_waters_rb.isChecked():
            usr_vendor = 'waters'
        elif self.ui.vendor_thermo_rb.isChecked():
            usr_vendor = 'thermo'
        else:
            usr_vendor = 'waters'
        print('Vendor mode = %s' % usr_vendor)

        print('linker started!')
        _pl_class_info = str(self.ui.tab_d_lipidclass_cmb.currentText())

        pl_class_checker = re.compile(r'(.*)( [\(])(\w{2,3})([\)] )(.*)')

        pl_class_match = pl_class_checker.match(_pl_class_info)

        if pl_class_match:
            pl_class_info_lst = pl_class_match.groups()
            _pl_class = pl_class_info_lst[2]
            _pl_charge = pl_class_info_lst[4]
        else:
            _pl_class = 'PC'
            _pl_charge = '[M+HCOO]-'

        _lipidstable_path_str = str(self.ui.tab_d_lipidstable_le.text())
        _ms2info_path_str = str(self.ui.tab_d_ms2info_le.text())
        _mzml_path_str = str(self.ui.tab_d_ms2mzml_le.text())
        _output_path_str = str(self.ui.tab_d_xlsxpath_le.text())

        ms2_delta = 0.9

        ident_df = pd.read_excel(_lipidstable_path_str, sheetname=0, header=0)
        ms2_df = pd.read_excel(_ms2info_path_str, sheetname=0)

        # obs_mz_lst = ident_df['Input Mass'].tolist()
        ident_idx_lst = ident_df.index.tolist()
        obs_idx_lst = ms2_df.index.tolist()

        step1_df = pd.DataFrame()
        self.ui.tab_d_statusrun_pte.clear()
        self.ui.tab_d_statusrun_pte.insertPlainText(u'Start! \n')

        for _idx, _ident_se in ident_df.iterrows():

            _obs_mz = _ident_se['Input Mass']
            _lib_mz = _ident_se['Matched Mass']
            _abbr = _ident_se['Abbreviation']
            _formula = _ident_se['Formula']
            _ion = _ident_se['Ion']

            _temp_df = pd.DataFrame()

            _obs_mz_l = _obs_mz - ms2_delta
            _obs_mz_h = _obs_mz + ms2_delta

            _query_code = '%f <= mz <= %f' % (_obs_mz_l, _obs_mz_h)

            _temp_df = ms2_df.query(_query_code)
            if _temp_df.shape[0] > 0:
                print('Found MS2!', _obs_mz)
                _temp_df['MS1_obs_mz'] = _obs_mz
                _temp_df['Lib_mz'] = _lib_mz
                _temp_df['Abbreviation'] = _abbr
                _temp_df['Formula'] = _formula
                _temp_df['Ion'] = _ion
                # print _temp_df
                step1_df = step1_df.append(_temp_df)
            else:
                pass
                # print(_obs_mz, 'No MS2 found!')

        _ms_th = self.ui.tab_d_msthreshold_spb.value()
        _ms2_th = self.ui.tab_d_ms2threshold_spb.value()
        _dda_top = self.ui.tab_d_dda_spb.value()
        _rt_start = self.ui.tab_d_rtstart_dspb.value()
        _rt_end = self.ui.tab_d_rtend_dspb.value()
        _mz_start = self.ui.tab_d_mzstart_dspb.value()
        _mz_end = self.ui.tab_d_mzend_dspb.value()

        # Construct parameters for the hunt_link function
        link_params_dct = {'MS_THRESHOLD': _ms_th, 'MS2_THRESHOLD': _ms2_th, 'DDA_TOP': _dda_top,
                           'RT_START': _rt_start, 'RT_END': _rt_end, 'MZ_START': _mz_start, 'MZ_END': _mz_end}

        final_output_df = hunt_link(pl_class=_pl_class, usr_mzml=_mzml_path_str, usr_df=step1_df,
                                    params_dct=link_params_dct, vendor=usr_vendor)

        final_output_df = final_output_df[final_output_df['MS1_obs_mz'] > 0]

        final_output_df.to_excel(_output_path_str)
        self.ui.tab_d_statusrun_pte.insertPlainText(unicode('Finished!'))

    def e_load_lipidsinfo(self):
        e_load_lipidstable_dialog = QtGui.QFileDialog(self)
        e_load_lipidstable_dialog.setNameFilters([u'MS Excel files (*.xlsx *.XLSX)'])
        e_load_lipidstable_dialog.selectNameFilter(u'MS Excel files (*.xlsx *.XLSX)')
        if e_load_lipidstable_dialog.exec_():
            self.ui.tab_e_loadxlsxpath_le.clear()
            e_load_xlsx_str = e_load_lipidstable_dialog.selectedFiles()[0]
            e_load_xlsx_str = os.path.abspath(e_load_xlsx_str)
            self.ui.tab_e_loadxlsxpath_le.setText(unicode(e_load_xlsx_str))

    def e_load_mzml(self):
        e_load_mzml_dialog = QtGui.QFileDialog(self)
        e_load_mzml_dialog.setNameFilters([u'mzML spectra files (*.mzML *.mzml)'])
        e_load_mzml_dialog.selectNameFilter(u'mzML spectra files (*.mzML *.mzml)')
        if e_load_mzml_dialog.exec_():
            self.ui.tab_e_ms2mzml_le.clear()
            e_load_mzml_str = e_load_mzml_dialog.selectedFiles()[0]
            e_load_mzml_str = os.path.abspath(e_load_mzml_str)
            self.ui.tab_e_ms2mzml_le.setText(unicode(e_load_mzml_str))

    def e_save_img2folder(self):
        e_save_img2folder_str = QtGui.QFileDialog.getExistingDirectory()
        self.ui.tab_e_saveimgfolder_le.setText(unicode(e_save_img2folder_str))

    def e_save_output(self):
        e_save_output_path = QtGui.QFileDialog.getSaveFileName(caption=u'Save file', filter=u'.xlsx')
        self.ui.tab_d_xlsxpath_le.clear()
        e_save_output_str = os.path.abspath(e_save_output_path[0])
        self.ui.tab_e_sumxlsxpath_le.setText(unicode(e_save_output_str))

    def e_run_hunter(self):
        if self.ui.vendor_waters_rb.isChecked():
            usr_vendor = 'waters'
        elif self.ui.vendor_thermo_rb.isChecked():
            usr_vendor = 'thermo'
        else:
            usr_vendor = 'waters'
        print('Vendor mode = %s' % usr_vendor)
        print('Hunter started!')
        _pl_class_info = str(self.ui.tab_e_lipidclass_cmb.currentText())

        pl_class_checker = re.compile(r'(.*)( [\(])(\w{2,3})([\)] )(.*)')

        pl_class_match = pl_class_checker.match(_pl_class_info)

        if pl_class_match:
            pl_class_info_lst = pl_class_match.groups()
            _pl_class = pl_class_info_lst[2]
            _pl_charge = pl_class_info_lst[4]
        else:
            _pl_class = 'PC'
            _pl_charge = '[M+HCOO]-'

        lipids_info_path_str = str(self.ui.tab_e_loadxlsxpath_le.text())
        mzml_path_str = str(self.ui.tab_e_ms2mzml_le.text())
        img_output_folder_str = str(self.ui.tab_e_saveimgfolder_le.text())
        xlsx_output_path_str = str(self.ui.tab_e_sumxlsxpath_le.text())

        rt_start = self.ui.tab_e_rtstart_dspb.value()
        rt_end = self.ui.tab_e_rtend_dspb.value()
        mz_start = self.ui.tab_e_mzstart_dspb.value()
        mz_end = self.ui.tab_e_mzend_dspb.value()
        dda_top = self.ui.tab_e_dda_spb.value()
        ms_th = self.ui.tab_e_msthreshold_spb.value()
        ms2_th = self.ui.tab_e_ms2threshold_spb.value()
        ms_ppm = self.ui.tab_e_msppm_spb.value()
        ms2_ppm = self.ui.tab_e_ms2ppm_spb.value()
        hg_th = self.ui.tab_e_hgthreshold_spb.value()
        hg_ppm = self.ui.tab_e_hgppm_spb.value()
        score_filter = self.ui.tab_e_score_spb.value()
        isotope_score_filter = self.ui.tab_e_isotopescore_spb.value()

        fa_white_list_cfg = self.ui.tab_f_fawhitelist_le.text()
        lipid_specific_cfg = self.ui.tab_f_hgcfg_le.text()
        score_cfg = self.ui.tab_f_scorecfg_le.text()

        hunter_param_dct = {'lipids_info_path_str': lipids_info_path_str, 'mzml_path_str': mzml_path_str,
                            'img_output_folder_str': img_output_folder_str,
                            'xlsx_output_path_str': xlsx_output_path_str, 'rt_start': rt_start, 'rt_end': rt_end,
                            'mz_start': mz_start, 'mz_end': mz_end, 'dda_top': dda_top, 'ms_th': ms_th,
                            'ms2_th': ms2_th, 'ms_ppm': ms_ppm, 'ms2_ppm': ms2_ppm, 'hg_th': hg_th, 'hg_ppm': hg_ppm,
                            'score_filter': score_filter, 'isotope_score_filter': isotope_score_filter,
                            'lipid_type': _pl_class, 'charge_mode': _pl_charge, 'fa_white_list_cfg': fa_white_list_cfg,
                            'lipid_specific_cfg': lipid_specific_cfg, 'score_cfg': score_cfg, 'vendor': usr_vendor}

        param_log_output_path_str = (str(self.ui.tab_e_saveimgfolder_le.text()) +
                                     '/LipidHunter_param-log_%s.txt'
                                     % (time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                                        )
                                     )

        config = configparser.ConfigParser()
        with open(param_log_output_path_str, 'w') as usr_param_cfg:
            config.add_section('parameters')
            for param in hunter_param_dct.keys():
                config.set('parameters', param, hunter_param_dct[param])
            config.write(usr_param_cfg)

        print(hunter_param_dct)
        tot_run_time = huntlipids(hunter_param_dct)
        self.ui.tab_e_statusrun_pte.insertPlainText('%.2f Sec\n' % tot_run_time)
        self.ui.tab_e_statusrun_pte.insertPlainText('>>> >>> >>> FINISHED <<< <<< <<<')

    def f_set_default_cfg(self):
        config = configparser.ConfigParser()
        with open('config.ini', 'w') as default_cfg:
            config.add_section('settings')
            config.set('settings', 'fa_white_list_cfg', self.ui.tab_f_fawhitelist_le.text())
            config.set('settings', 'lipid_specific_cfg', self.ui.tab_f_hgcfg_le.text())
            config.set('settings', 'score_cfg', self.ui.tab_f_scorecfg_le.text())
            config.write(default_cfg)
            
    def f_load_fawhitelist(self):
        f_load_lipidstable_dialog = QtGui.QFileDialog(self)
        f_load_lipidstable_dialog.setNameFilters([u'CSV files (*.csv *.CSV)'])
        f_load_lipidstable_dialog.selectNameFilter(u'CSV files (*.csv *.CSV)')
        if f_load_lipidstable_dialog.exec_():
            self.ui.tab_f_fawhitelist_le.clear()
            f_load_csv_str = f_load_lipidstable_dialog.selectedFiles()[0]
            f_load_csv_str = os.path.abspath(f_load_csv_str)
            self.ui.tab_f_fawhitelist_le.setText(unicode(f_load_csv_str))

    def f_load_hgcfg(self):
        f_load_lipidstable_dialog = QtGui.QFileDialog(self)
        f_load_lipidstable_dialog.setNameFilters([u'MS Excel files (*.xlsx *.XLSX)'])
        f_load_lipidstable_dialog.selectNameFilter(u'MS Excel files (*.xlsx *.XLSX)')
        if f_load_lipidstable_dialog.exec_():
            self.ui.tab_f_hgcfg_le.clear()
            f_load_xlsx_str = f_load_lipidstable_dialog.selectedFiles()[0]
            f_load_xlsx_str = os.path.abspath(f_load_xlsx_str)
            self.ui.tab_f_hgcfg_le.setText(unicode(f_load_xlsx_str))

    def f_load_scorecfg(self):
        f_load_lipidstable_dialog = QtGui.QFileDialog(self)
        f_load_lipidstable_dialog.setNameFilters([u'MS Excel files (*.xlsx *.XLSX)'])
        f_load_lipidstable_dialog.selectNameFilter(u'MS Excel files (*.xlsx *.XLSX)')
        if f_load_lipidstable_dialog.exec_():
            self.ui.tab_f_scorecfg_le.clear()
            f_load_xlsx_str = f_load_lipidstable_dialog.selectedFiles()[0]
            f_load_xlsx_str = os.path.abspath(f_load_xlsx_str)
            self.ui.tab_f_scorecfg_le.setText(unicode(f_load_xlsx_str))

if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())