from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyle, QStyledItemDelegate, QStyleOptionViewItem

from .theme import MUTED, TEXT

REL_ROLE = Qt.UserRole + 1


class StripeDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        color = QColor(index.data(REL_ROLE) or MUTED)
        painter.save()
        tint = QColor(color)
        tint.setAlpha(60 if option.state & QStyle.State_Selected else 34 if option.state & QStyle.State_MouseOver else 18)
        painter.fillRect(option.rect, tint)
        painter.fillRect(option.rect.adjusted(0, 0, option.rect.width() * -1 + 5, 0), color)
        painter.restore()
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.rect = option.rect.adjusted(14, 0, 0, 0)
        opt.state &= ~QStyle.State_Selected
        opt.state &= ~QStyle.State_MouseOver
        opt.palette.setColor(QPalette.Text, QColor(TEXT))
        opt.backgroundBrush = QBrush(Qt.transparent)
        QApplication.style().drawControl(QStyle.CE_ItemViewItem, opt, painter)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 32))
        return size
