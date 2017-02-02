# -*- coding: utf-8 -*-
# Copyright 2015-2017 Zhixu Ni, AG Bioanalytik, BBZ, University of Leipzig.
# The software is currently  under development and is not ready to be released.
# A suitable license will be chosen before the official release of oxLPPdb.
# For more info please contact: zhixu.ni@uni-leipzig.de
import re


class BulkAbbrFormula(object):
    def __init__(self):

        pa_hg_elem = {'C': 0, 'H': 3, 'O': 4, 'P': 1, 'N': 0}
        pc_hg_elem = {'C': 5, 'H': 14, 'O': 4, 'P': 1, 'N': 1}
        pe_hg_elem = {'C': 2, 'H': 8, 'O': 4, 'P': 1, 'N': 1}
        pg_hg_elem = {'C': 3, 'H': 9, 'O': 6, 'P': 1, 'N': 0}
        pi_hg_elem = {'C': 6, 'H': 13, 'O': 9, 'P': 1, 'N': 0}
        pip_hg_elem = {'C': 6, 'H': 14, 'O': 12, 'P': 2, 'N': 0}
        ps_hg_elem = {'C': 3, 'H': 8, 'O': 6, 'P': 1, 'N': 1}

        self.lipid_hg_elem_dct = {'PA': pa_hg_elem, 'PC': pc_hg_elem, 'PE': pe_hg_elem,
                                  'PG': pg_hg_elem, 'PI': pi_hg_elem, 'PS': ps_hg_elem, 'PIP': pip_hg_elem}

        self.glycerol_bone_elem_dct = {'C': 3, 'H': 2}
        self.link_o_elem_dct = {'O': -1, 'H': 2}
        self.link_p_elem_dct = {'O': -1}

    @staticmethod
    def decode_abbr(abbr):

        pl_checker = re.compile(r'(P[ACEGSI])([(])(.*)([)])')
        pip_checker = re.compile(r'(PIP)([(])(.*)([)])')
        tg_checker = re.compile(r'(TG)([(])(.*)([)])')
        fa_checker = re.compile(r'(\d{1,2})([:])(\d)')
        fa_o_checker = re.compile(r'(O-)(\d{1,2})([:])(\d)')
        fa_p_checker = re.compile(r'(P-)(\d{1,2})([:])(\d)')

        # Check PL Type
        _pl_typ = ''
        bulk_fa_typ = ''
        bulk_fa_linker = ''
        bulk_fa_c = 0
        bulk_fa_db = 0
        lyso_fa_linker_dct = {'sn1': '', 'sn2': ''}

        if pl_checker.match(abbr):
            print ('PL')
            pl_re_chk = pl_checker.match(abbr)
            pl_typ_lst = pl_re_chk.groups()
            _pl_typ = pl_typ_lst[0]
            bulk_fa_typ = pl_typ_lst[2]
        if pip_checker.match(abbr):
            print ('PIP')
            pip_re_chk = pip_checker.match(abbr)
            pip_typ_lst = pip_re_chk.groups()
            _pl_typ = pip_typ_lst[0]
            bulk_fa_typ = pip_typ_lst[2]
        if tg_checker.match(abbr):
            print ('TG')
            pip_re_chk = pip_checker.match(abbr)
            pip_typ_lst = pip_re_chk.groups()
            _pl_typ = pip_typ_lst[0]
            bulk_fa_typ = pip_typ_lst[2]
        if fa_checker.match(abbr):
            print ('FA')
            _pl_typ = 'FA'
            bulk_fa_typ = abbr
        if fa_o_checker.match(abbr):
            print ('FA')
            _pl_typ = 'FA'
            bulk_fa_typ = abbr
        if fa_p_checker.match(abbr):
            print ('FA')
            _pl_typ = 'FA'
            bulk_fa_typ = abbr

        print(bulk_fa_typ)

        if fa_checker.match(bulk_fa_typ):
            bulk_fa_linker = 'A-A-'
            lyso_fa_linker_dct = {'A': ''}
            fa_chk = fa_checker.match(bulk_fa_typ)
            bulk_fa_lst = fa_chk.groups()
            bulk_fa_c = bulk_fa_lst[0]
            bulk_fa_db = bulk_fa_lst[2]
        elif fa_o_checker.match(bulk_fa_typ):
            bulk_fa_linker = 'O-A-'
            lyso_fa_linker_dct = {'O': '', 'A': 'O-'}  # link of the other sn after NL of this sn
            fa_chk = fa_o_checker.match(bulk_fa_typ)
            bulk_fa_lst = fa_chk.groups()
            bulk_fa_c = bulk_fa_lst[1]
            bulk_fa_db = bulk_fa_lst[3]
        elif fa_p_checker.match(bulk_fa_typ):
            bulk_fa_linker = 'P-A-'
            lyso_fa_linker_dct = {'P': '', 'A': 'P-'}  # link of the other sn after NL of this sn
            fa_chk = fa_p_checker.match(bulk_fa_typ)
            bulk_fa_lst = fa_chk.groups()
            bulk_fa_c = bulk_fa_lst[1]
            bulk_fa_db = bulk_fa_lst[3]

        bulk_fa_c = int(bulk_fa_c)
        bulk_fa_db = int(bulk_fa_db)

        lipid_info_dct = {'TYPE': _pl_typ, 'LINK': bulk_fa_linker, 'C': bulk_fa_c, 'DB': bulk_fa_db,
                          'LYSO_LINK': lyso_fa_linker_dct}

        return lipid_info_dct

    def get_neutral_elem(self, abbr):

        usr_lipid_info_dct = self.decode_abbr(abbr)

        if usr_lipid_info_dct['TYPE'] in self.lipid_hg_elem_dct.keys():
            tmp_lipid_elem_dct = self.lipid_hg_elem_dct[usr_lipid_info_dct['TYPE']].copy()
            tmp_lipid_elem_dct['O'] += 4
            tmp_lipid_elem_dct['C'] += self.glycerol_bone_elem_dct['C'] + usr_lipid_info_dct['C']
            tmp_lipid_elem_dct['H'] += (self.glycerol_bone_elem_dct['H'] + usr_lipid_info_dct['C'] * 2
                                        - usr_lipid_info_dct['DB'] * 2)  # DBE = DB + 2xC=O from FA

            if usr_lipid_info_dct['LINK'] == 'O-A-':
                tmp_lipid_elem_dct['O'] += -1
                tmp_lipid_elem_dct['H'] += 2
            elif usr_lipid_info_dct['LINK'] == 'P-A-':
                tmp_lipid_elem_dct['O'] += -1

            return tmp_lipid_elem_dct
        else:
            return {'C': 0, 'H': 0, 'O': 0, 'P': 0}

    def get_charged_elem(self, abbr, charge='[M-H]-'):

        lipid_elem_dct = self.get_neutral_elem(abbr)

        if charge == '[M-H]-':
            lipid_elem_dct['H'] += -1
        elif charge == '[M+HCOO]-' or charge == '[M+FA-H]-':
            lipid_elem_dct['H'] += 1
            lipid_elem_dct['C'] += 1
            lipid_elem_dct['O'] += 2
        elif charge == '[M+CH3COO]-':
            lipid_elem_dct['H'] += 3
            lipid_elem_dct['C'] += 2
            lipid_elem_dct['O'] += 2
        elif charge == '[M+H]+':
            lipid_elem_dct['H'] += 1
        elif charge == '[M+NH4]+':
            lipid_elem_dct['N'] += 1
            lipid_elem_dct['H'] += 4

        return lipid_elem_dct

    def get_formula(self, abbr, charge=''):

        if charge in ['neutral', 'Neutral', '', None]:

            elem_dct = self.get_neutral_elem(abbr)
        else:
            elem_dct = self.get_charged_elem(abbr, charge=charge)

        formula_str = 'C{C}H{H}O{O}'.format(C=elem_dct['C'], H=elem_dct['H'], O=elem_dct['O'])

        if 'P' in elem_dct.keys():
            if elem_dct['P'] == 1:
                formula_str += 'P'
            elif elem_dct['P'] > 1:
                formula_str += 'P%i' % elem_dct['P']

        if 'N' in elem_dct.keys():
            if elem_dct['N'] == 1:
                formula_str += 'N'
            elif elem_dct['N'] > 1:
                formula_str += 'N%i' % elem_dct['N']

        if 'Na' in elem_dct.keys():
            if elem_dct['Na'] == 1:
                formula_str += 'Na'
            elif elem_dct['Na'] > 1:
                formula_str += 'Na%i' % elem_dct['Na']

        if 'K' in elem_dct.keys():
            if elem_dct['K'] == 1:
                formula_str += 'K'
            elif elem_dct['K'] > 1:
                formula_str += 'K%i' % elem_dct['K']

        if charge in ['neutral', 'Neutral', '', None]:
            pass
        elif charge in ['[M-H]-', '[M+HCOO]-']:
            formula_str += '-'
        elif charge in ['[M+H]+', '[M+NH4]+']:
            formula_str += '+'

        return formula_str, elem_dct

if __name__ == '__main__':

    usr_bulk_abbr_lst = ['PC(36:3)', 'PC(O-36:3)', 'PC(P-36:3)']
    charge_lst = ['', '[M-H]-', '[M+HCOO]-']

    abbr2formula = BulkAbbrFormula()

    for usr_abbr in usr_bulk_abbr_lst:
        for _charge in charge_lst:
            usr_formula, usr_elem_dct = abbr2formula.get_formula(usr_abbr, charge=_charge)
            print(usr_abbr, _charge)
            print(usr_elem_dct)
            print(usr_formula)