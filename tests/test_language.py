import unittest
import flet as ft
from test_audit import start,event
from i18n import localize_tree,translate
from help_content import describe,EN_HELP

class LanguageTests(unittest.TestCase):
    def test_language_persists_and_does_not_change_contract_values(self):
        page,v=start({'scanner_live':False,'option_symbol':'BANKNIFTY','option_strike':'24000'})
        v['select'](2);picker=v['body'].controls[1]
        picker.value='हिंदी';picker.on_change(event(picker))
        self.assertEqual(page.client_storage.get('bot_king_preferences')['language'],'हिंदी')
        self.assertEqual(v['chain_symbol'].value,'BANKNIFTY')
        self.assertEqual(v['option_strike'].value,'24000')
        v['select'](1)
        self.assertEqual(v['chain_symbol'].label,'इंडेक्स / शेयर')
        _,restored=start(page.client_storage.get('bot_king_preferences'))
        self.assertEqual(restored['prefs']['language'],'हिंदी')
        restored['select'](2)
        picker=restored['body'].controls[1];picker.value='English';picker.on_change(event(picker))
        restored['select'](1)
        self.assertEqual(restored['chain_symbol'].label,'Index / Stock')
    def test_dropdown_translation_preserves_keys_and_selection(self):
        option=ft.dropdown.Option('Auto')
        control=ft.Dropdown(value='Auto',options=[option],label='Market data mode')
        localize_tree(control,'हिंदी')
        self.assertEqual(control.value,'Auto');self.assertEqual(option.key,'Auto')
        self.assertEqual(option.text,'ऑटो')
        localize_tree(control,'English')
        self.assertEqual(option.text,'Auto')
    def test_entered_values_and_passwords_are_never_translated(self):
        field=ft.TextField(label='Client Code',value='Settings',password=True)
        localize_tree(field,'हिंदी');self.assertEqual(field.value,'Settings')
    def test_dynamic_status_and_switch_back(self):
        text=ft.Text('No open paper positions')
        localize_tree(text,'हिंदी');self.assertEqual(text.value,'कोई खुली पेपर पोजीशन नहीं')
        text.value='Saved automatically';localize_tree(text,'हिंदी')
        self.assertEqual(text.value,'अपने आप सेव हुआ')
        localize_tree(text,'English');self.assertEqual(text.value,'Saved automatically')
    def test_help_in_both_languages_and_original_label_retained(self):
        _,v=start({'scanner_live':False,'language':'हिंदी'})
        v['select'](4)
        self.assertEqual(v['sl']._bk_original_label,'Stop loss %')
        self.assertIn('जोखिम',describe(v['sl']._bk_original_label,'हिंदी'))
        self.assertIn('paper demonstration',describe('Stop loss %','English'))
        self.assertIn('nine',describe('PCR','English'))
        self.assertIn('9',describe('PCR','हिंदी'))
    def test_both_languages_render_all_pages_without_duplicate_controls(self):
        _,v=start({'scanner_live':False})
        for language in ('हिंदी','English','हिंदी'):
            v['prefs']['language']=language
            for page in range(5):
                v['select'](page);seen=set()
                def walk(c):
                    self.assertNotIn(id(c),seen);seen.add(id(c))
                    for child in c._get_children():walk(child)
                for root in v['body'].controls:walk(root)
    def test_invalid_saved_language_falls_back(self):
        _,v=start({'scanner_live':False,'language':'invalid'})
        self.assertEqual(v['prefs']['language'],'English')
    def test_all_help_topics_have_english_translation(self):
        for key in EN_HELP:
            english=describe(key,'English')
            self.assertTrue(english)
            self.assertFalse(any('\u0900'<=c<='\u097f' for c in english))

