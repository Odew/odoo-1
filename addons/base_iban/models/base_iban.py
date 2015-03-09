# -*- coding: utf-8 -*-

import string
from openerp import _, api, models
from openerp.exceptions import UserError


# Reference Examples of IBAN
_ref_iban = {'al': 'ALkk BBBS SSSK CCCC CCCC CCCC CCCC',
             'ad': 'ADkk BBBB SSSS CCCC CCCC CCCC',
             'at': 'ATkk BBBB BCCC CCCC CCCC',
             'be': 'BEkk BBBC CCCC CCKK',
             'ba': 'BAkk BBBS SSCC CCCC CCKK',
             'bg': 'BGkk BBBB SSSS DDCC CCCC CC',
             'bh': 'BHkk BBBB SSSS SSSS SSSS SS',
             'cr': 'CRkk BBBC CCCC CCCC CCCC C',
             'hr': 'HRkk BBBB BBBC CCCC CCCC C',
             'cy': 'CYkk BBBS SSSS CCCC CCCC CCCC CCCC',
             'cz': 'CZkk BBBB SSSS SSCC CCCC CCCC',
             'dk': 'DKkk BBBB CCCC CCCC CC',
             'do': 'DOkk BBBB CCCC CCCC CCCC CCCC CCCC',
             'ee': 'EEkk BBSS CCCC CCCC CCCK',
             'fo': 'FOkk CCCC CCCC CCCC CC',
             'fi': 'FIkk BBBB BBCC CCCC CK',
             'fr': 'FRkk BBBB BGGG GGCC CCCC CCCC CKK',
             'ge': 'GEkk BBCC CCCC CCCC CCCC CC',
             'de': 'DEkk BBBB BBBB CCCC CCCC CC',
             'gi': 'GIkk BBBB CCCC CCCC CCCC CCC',
             'gr': 'GRkk BBBS SSSC CCCC CCCC CCCC CCC',
             'gl': 'GLkk BBBB CCCC CCCC CC',
             'hu': 'HUkk BBBS SSSC CCCC CCCC CCCC CCCC',
             'is': 'ISkk BBBB SSCC CCCC XXXX XXXX XX',
             'ie': 'IEkk BBBB SSSS SSCC CCCC CC',
             'il': 'ILkk BBBS SSCC CCCC CCCC CCC',
             'it': 'ITkk KBBB BBSS SSSC CCCC CCCC CCC',
             'kz': 'KZkk BBBC CCCC CCCC CCCC',
             'kw': 'KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC',
             'lv': 'LVkk BBBB CCCC CCCC CCCC C',
             'lb': 'LBkk BBBB CCCC CCCC CCCC CCCC CCCC',
             'li': 'LIkk BBBB BCCC CCCC CCCC C',
             'lt': 'LTkk BBBB BCCC CCCC CCCC',
             'lu': 'LUkk BBBC CCCC CCCC CCCC',
             'mk': 'MKkk BBBC CCCC CCCC CKK',
             'mt': 'MTkk BBBB SSSS SCCC CCCC CCCC CCCC CCC',
             'mr': 'MRkk BBBB BSSS SSCC CCCC CCCC CKK',
             'mu': 'MUkk BBBB BBSS CCCC CCCC CCCC CCCC CC',
             'mc': 'MCkk BBBB BGGG GGCC CCCC CCCC CKK',
             'me': 'MEkk BBBC CCCC CCCC CCCC KK',
             'nl': 'NLkk BBBB CCCC CCCC CC',
             'no': 'NOkk BBBB CCCC CCK',
             'pl': 'PLkk BBBS SSSK CCCC CCCC CCCC CCCC',
             'pt': 'PTkk BBBB SSSS CCCC CCCC CCCK K',
             'ro': 'ROkk BBBB CCCC CCCC CCCC CCCC',
             'sm': 'SMkk KBBB BBSS SSSC CCCC CCCC CCC',
             'sa': 'SAkk BBCC CCCC CCCC CCCC CCCC',
             'rs': 'RSkk BBBC CCCC CCCC CCCC KK',
             'sk': 'SKkk BBBB SSSS SSCC CCCC CCCC',
             'si': 'SIkk BBSS SCCC CCCC CKK',
             'es': 'ESkk BBBB SSSS KKCC CCCC CCCC',
             'se': 'SEkk BBBB CCCC CCCC CCCC CCCC',
             'ch': 'CHkk BBBB BCCC CCCC CCCC C',
             'tn': 'TNkk BBSS SCCC CCCC CCCC CCCC',
             'tr': 'TRkk BBBB BRCC CCCC CCCC CCCC CC',
             'ae': 'AEkk BBBC CCCC CCCC CCCC CCC',
             'gb': 'GBkk BBBB SSSS SSCC CCCC CC',
             }


def _format_iban(iban_str):
    '''
    This function removes all characters from given 'iban_str' that isn't a alpha numeric and converts it to upper case.
    '''
    res = ""
    if iban_str:
        for char in iban_str:
            if char.isalnum():
                res += char.upper()
    return res


def _pretty_iban(iban_str):
    "return iban_str in groups of four characters separated by a single space"
    res = []
    while iban_str:
        res.append(iban_str[:4])
        iban_str = iban_str[4:]
    return ' '.join(res)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.model
    def create(self, vals):
        # overwrite to format the iban number correctly
        if vals.get('state') == 'iban' and vals.get('acc_number'):
            vals['acc_number'] = _format_iban(vals['acc_number'])
            vals['acc_number'] = _pretty_iban(vals['acc_number'])
        return super(ResPartnerBank, self).create(vals)

    @api.multi
    def write(self, vals):
        # overwrite to format the iban number correctly
        if vals.get('state') == 'iban' and vals.get('acc_number'):
            vals['acc_number'] = _format_iban(vals['acc_number'])
            vals['acc_number'] = _pretty_iban(vals['acc_number'])
        return super(ResPartnerBank, self).write(vals)

    def is_iban_valid(self, iban):
        """ Check if IBAN is valid or not
            @param iban: IBAN as string
            @return: True if IBAN is valid, False otherwise
        """
        if not iban:
            return False
        iban = _format_iban(iban).lower()
        if iban[:2] in _ref_iban and len(iban) != len(_format_iban(_ref_iban[iban[:2]])):
            return False
        #the four first digits have to be shifted to the end
        iban = iban[4:] + iban[:4]
        #letters have to be transformed into numbers (a = 10, b = 11, ...)
        iban2 = ""
        for char in iban:
            if char.isalpha():
                iban2 += str(ord(char) - 87)
            else:
                iban2 += char
        #iban is correct if modulo 97 == 1
        return int(iban2) % 97 == 1

    @api.one
    @api.constrains('acc_number', 'state')
    def check_iban(self):
        '''
        Check the IBAN number
        '''
        def default_iban_check(iban_cn):
            return iban_cn and iban_cn[0] in string.ascii_lowercase and iban_cn[1] in string.ascii_lowercase

        if self.state == 'iban' and self.is_iban_valid(self.acc_number):
            iban_country = self.acc_number and self.acc_number[:2].lower()
            if default_iban_check(iban_country):
                if iban_country in _ref_iban:
                    raise UserError(_('The IBAN does not seem to be correct. You should have entered something like this %s' \
                                     '\n Where B = National bank code, S = Branch code,'
                                      ' C = Account No, K = Check digit' % _ref_iban[iban_country]))
                raise UserError(_('This IBAN does not pass the validation check, please verify it'))
            raise UserError(_('The IBAN is invalid, it should begin with the country code'))

    @api.one
    @api.constrains('bank_bic')
    def _check_bank(self):
        if self.state == 'iban' and not self.bank_bic:
            raise UserError(_('Please define BIC/Swift code on bank for bank type IBAN Account to make valid payments'))

    @api.multi
    def get_bban_from_iban(self):
        '''
        This function returns the bank account number computed from the iban account number,
        thanks to the mapping_list dictionary that contains the rules associated to its country.
        '''
        res = {}
        mapping_list = {
            #TODO add rules for others countries
            'be': lambda x: x[4:],
            'fr': lambda x: x[14:],
            'ch': lambda x: x[9:],
            'gb': lambda x: x[14:],
        }
        for record in self:
            if not record.acc_number:
                res[record.id] = False
                continue
            res[record.id] = False
            for code, function in mapping_list.items():
                if record.acc_number.lower().startswith(code):
                    res[record.id] = function(record.acc_number)
                    break
        return res
