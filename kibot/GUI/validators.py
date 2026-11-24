# Classes to validate the data entered in a widget
# Derived from wx.Validator

import wx
from .. import log
logger = log.get_logger()

# Keys that are under 256 but are special anyways
SPECIAL_KEYS = {wx.WXK_DELETE, wx.WXK_BACK, wx.WXK_TAB, wx.WXK_RETURN}
# Acceptable for a floating point number, plus '-' handled separately
NUMERIC_KEYS = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'}


class GenericValidator(wx.Validator):
    def __init__(self, parent, restriction, default):
        wx.Validator.__init__(self)
        self.parent = parent
        self.restriction = restriction
        self.default = default

    def TransferFromWindow(self) -> bool:
        return True

    def TransferToWindow(self) -> bool:
        return True


class NumberValidator(GenericValidator):
    def __init__(self, parent, restriction, default, on_text=None):
        super().__init__(parent, restriction, default)
        self.Bind(wx.EVT_CHAR, self.OnChar)  # Char filter
        self.Bind(wx.EVT_TEXT, self.OnText)  # Number validation
        self.on_text = on_text

    def Clone(self):
        return NumberValidator(self.parent, self.restriction, self.default, self.on_text)

    def Validate(self, win) -> bool:
        """ Check if the new value is usable """
        new_value = self.parent.Value
        if new_value == '':
            # Interpreted as empty -> use default
            return True
        # min/max
        min = self.restriction[0]
        max = self.restriction[1]
        # Allow just "-" if we accept negative numbers
        if new_value == '-' and min < 0:
            # The get_value member will convert it to None
            return True
        try:
            new_value_number = float(new_value)
        except ValueError:
            self.why_wrong = f'not a valid number: {new_value}'
            return False
        if new_value_number < min:
            self.why_wrong = f'too small: {new_value} < {min}'
            return False
        if new_value_number > max:
            self.why_wrong = f'too big: {new_value} > {max}'
            return False
        return True

    def unroll_value(self):
        t = self.parent
        t.ChangeValue(self.old_value)
        t.SetInsertionPoint(self.old_point)
        if self.old_modified:
            t.MarkDirty()
        logger.debug(f'unroll {self.old_value}')

    def OnText(self, event):
        """ Check if the new value is usable.
            If not unroll the change using the state memorized in OnChar """
        if not self.Validate(None):
            logger.debug(self.why_wrong)
            self.unroll_value()
        elif self.on_text:
            self.on_text(event)

    def OnChar(self, event):
        """ Filter characters that are usable for our data type.
            The text can become invalid anyways, like `--50`, let the OnText member fix it. """
        # Memorize current state so we can unroll it if the value becomes wrong
        self.old_value = self.parent.Value
        self.old_modified = self.parent.IsModified()
        self.old_point = self.parent.GetInsertionPoint()
        # Filter usable keys
        keycode = int(event.GetKeyCode())
        # Accept special characters
        if keycode > 255 or keycode in SPECIAL_KEYS:
            event.Skip()
            return
        # Accept number related chars
        c = chr(keycode)
        if c in NUMERIC_KEYS:
            event.Skip()
            return
        # Accept - only at the beginning
        if c == '-' and self.parent.GetInsertionPoint() == 0:
            event.Skip()
            return


class LowerCaseValidator(GenericValidator):
    """ Force lowercase """
    def __init__(self, parent, on_text=None):
        super().__init__(parent, None, None)
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.on_text = on_text

    def Clone(self):
        return LowerCaseValidator(self.parent, self.on_text)

    def set_value(self, new_val):
        t = self.parent
        point = self.parent.GetInsertionPoint()
        t.ChangeValue(new_val)
        t.SetInsertionPoint(point)
        logger.debug(f'set_value {new_val}')

    def OnText(self, event):
        """ Force lowercase if needed """
        low = self.parent.Value.lower()
        if low != self.parent.Value:
            self.set_value(low)
        elif self.on_text:
            self.on_text(event)
