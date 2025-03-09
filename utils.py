# -*- coding: utf-8 -*-

try:
    from PySide6 import QtWidgets, QtGui, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtGui, QtCore
    
"コメント追加"

# ---------------------------------------------------------------------------------- #
# COMMON
# ---------------------------------------------------------------------------------- #
def get_font():
    app = QtWidgets.QApplication.instance()
    return app.font()
    # print(f"フォント名: {default_font.family()}, サイズ: {default_font.pointSize(), default_font.pixelSize()}")

# ----------------------------------------------------------------------------------
# 展開・折りたたみ可能なウィジェット
# ----------------------------------------------------------------------------------
class CollapsibleFrame(QtWidgets.QWidget):
    toggled = QtCore.Signal(bool)  # 展開/折りたたみ時に発信されるシグナル

    kAlignLeft      = 0
    kAlignRight     = 1
    kAlignCenter    = 2
    
    kDefault        = 0
    kSolid          = 1
    kRounded        = 2
    kDashed         = 3
    
    kTriangle       = 0
    kArrow          = 1
    kPlusMinus      = 2
    kCircle         = 3

    def __init__(self, title="Title", color=QtGui.QColor(187, 187, 187), parent=None):
        super(CollapsibleFrame, self).__init__(parent)
        self._title                 = title
        self._title_color           = color
        self._title_alignment       = self.kAlignLeft
        self._title_bar_color       = QtGui.QColor(93, 93, 93)
        self._title_bar_height      = 20
        self._icon_color            = QtGui.QColor(238, 238, 238)
        self._icon_alignment        = self.kAlignLeft
        self._icon_style            = self.kTriangle
        self._frame_style           = self.kDefault
        self._rotation_angle        = 0
        
        self._is_collapsed          = False
        self._is_collapsable        = True
        self._is_title_visible      = True
        self._is_icon_visible       = True
        self._is_animation_enabled  = True
        
        self._frame_styles = {
            self.kDefault:      "#ContentFrame{border: none; background: rgb(255, 0, 0)}",
            self.kSolid:        "#ContentFrame{border: 2px solid gray;}",
            self.kRounded:      "#ContentFrame{border: 2px solid gray; border-radius: 6px;}",
            self.kDashed:       "#ContentFrame{border: 2px dashed gray;}",
        }
        
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        # メインレイアウト
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self._updateTitleBarHeight()

        # コンテンツフレーム
        self.frame = QtWidgets.QFrame(self)
        self.frame.setObjectName("ContentFrame")
        self._updateFrameStyle()
        self._frame_geometry = self.frame.geometry()

        # 内部レイアウト
        self.content_layout = QtWidgets.QVBoxLayout(self.frame)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        self.main_layout.addWidget(self.frame)

        # アニメーション
        # self.frame_animation = QtCore.QPropertyAnimation(self.frame, b"geometry")
        self.frame_animation = QtCore.QPropertyAnimation(self.frame, b"maximumHeight")
        self.frame_animation.setDuration(200)
        
        self.icon_animation = QtCore.QVariantAnimation()
        self.icon_animation.setDuration(200)
        self.icon_animation.valueChanged.connect(self._updateIconRotation)

    # override method
    def mousePressEvent(self, event):
        """タイトルバーのクリックで展開・折りたたみ"""
        if event.pos().y() < self._title_bar_height and self._is_collapsable:
            self._toggle()

    def paintEvent(self, event):
        """カスタム描画（タイトルバー + 三角形アイコン）"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # タイトルバー描画
        painter.setBrush(self._title_bar_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self._title_bar_height)

        # タイトル描画
        if self._is_title_visible:
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            font_metrics = QtGui.QFontMetrics(font)
            text_width = font_metrics.horizontalAdvance(self._title)
            
            # タイトル位置
            rect = self.rect()
            if self._title_alignment == self.kAlignLeft:
                if self._is_icon_visible and self._icon_alignment == self.kAlignLeft:
                    text_x = rect.left() + 25
                else:
                    text_x = rect.left() + 10
                
            elif self._title_alignment == self.kAlignRight:
                if self._is_icon_visible and self._icon_alignment == self.kAlignRight:
                    text_x = rect.right() - text_width - 25
                else:
                    text_x = rect.right() - text_width - 10
            else:
                text_x = rect.right() / 2 - text_width / 2 

            painter.setPen(self._title_color)
            text_rect = QtCore.QRect(text_x, 0, text_width, self._title_bar_height)
            painter.drawText(text_rect, QtCore.Qt.AlignVCenter, self._title)
        
        # アイコン描画
        if self._is_icon_visible:
            # アイコン位置
            if self._icon_alignment == self.kAlignLeft:
                icon_pos = QtCore.QPoint(10, self._title_bar_height / 2)
                
            elif self._icon_alignment == self.kAlignRight:
                icon_pos = QtCore.QPoint(self.width() - 10, self._title_bar_height / 2)

            else:
                if self._is_title_visible and self._title_alignment == self.kAlignCenter:
                    icon_pos = QtCore.QPoint(self.width() / 2 - text_width / 2 - 15, self._title_bar_height / 2)
                else:
                    icon_pos = QtCore.QPoint(self.width() / 2, self._title_bar_height / 2)

            if self._icon_style == self.kTriangle:
                self._drawTriangle(painter, icon_pos)
            elif self._icon_style == self.kArrow:
                self._drawArrow(painter, icon_pos)
            elif self._icon_style == self.kPlusMinus:
                self._drawPlusMinus(painter, icon_pos)
            elif self._icon_style == self.kCircle:
                self._drawCircle(painter, icon_pos)

    def resizeEvent(self, event):
        """ウィンドウのリサイズ時にフレームのジオメトリを更新"""
        super(CollapsibleFrame, self).resizeEvent(event)
        # レイアウト内のフレームのサイズを更新
        margin = 0
        width  = self.width() - 2 * margin
        height = self.height() - 2 * margin
        self.frame_geometry = QtCore.QRect(margin, margin + self._title_bar_height, width, height - self._title_bar_height)

    # public method
    def addWidget(self, widget):
        """コンテンツ領域にウィジェットを追加"""
        self.content_layout.addWidget(widget)

    def title(self):
        """タイトル名を返す
        Returns:
            string: タイトル名
        """        
        return self._title
    
    def titleColor(self):
        """タイトルのカラーを返す
        Returns:
            QtGui.QColor: 文字の色
        """        
        return self._title_color
    
    def titleAlignment(self):
        """タイトルの配置を返す

        Returns:
            int: kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """        
        return self._title_alignment
    
    def titleVisible(self):
        """タイトルの表示状態を返す

        Returns:
            bool: 表示状態
        """   
        return self._is_title_visible
    
    def titleBarColor(self):
        """タイトルバーの背景色を返す

        Returns:
            QtGui.QColor: 背景色
        """        
        return self._title_bar_color
    
    def titleBarHeight(self):
        """タイトルバーの高さを返す

        Returns:
            int: タイトルバーの高さ
        """        
        return self._title_bar_height
    
    def iconColor(self):
        """アイコンのカラーを返す
        Returns:
            QtGui.QColor: アイコンの色
        """        
        return self._icon_color    
    
    def iconAlignment(self):
        """アイコンの配置を返す

        Returns:
            int: kAlignLeft = 0 kAlignRight = 1 kAlignCenter = 2
        """        
        return self._icon_alignment
    
    def iconStyle(self):
        """アイコンのスタイルを返す

        Returns:
            int: kTriangle = 0 kPlusMinus = 1
        """        
        return self._icon_style
    
    def iconVisible(self):
        """アイコンの表示状態を返す

        Returns:
            bool: 表示状態
        """   
        return self._is_icon_visible
    
    def frameStyle(self):
        """フレームのスタイルを返す

        Returns:
            int: kDefault = 0 kSolid = 1 kRounded = 2 kDashed = 3
        """        
        return self._frame_style
        
    def isCollapsed(self):
        """フレームが折りたたまれているかどうか

        Returns:
            bool: 折りたたみ状態
        """        
        return self._is_collapsed
    
    def isCollapsable(self):
        """折りたたみが有効化どうか

        Returns:
            bool: 有効化状態
        """        
        return self._is_collapsable
    
    def isAnimationEnabled(self):
        """アニメーションが有効化どうか

        Returns:
            bool: 有効化状態
        """        
        return self._is_animation_enabled
    
    def setTitle(self, title):
        """タイトルを変更する"""
        self._title = title
        self.update()

    def setTitleColor(self, color):
        """タイトルの文字の色を変更する"""
        self._title_color = color
        self.update()

    def setTitleAlignment(self, alignment):
        """タイトルの配置を変更 (0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter)"""
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._title_alignment = alignment
            self.update()
        
    def setTitleVisible(self, visible):
        """タイトルの表示・非表示を切り替える"""
        self._is_title_visible = visible
        self.update()
        
    def setTitleBarColor(self, color):
        """タイトルバーの背景色を変更"""
        self._title_bar_color = color
        self.update()

    def setTitleBarHeight(self, height):
        """タイトルバーの高さを変更 最小15px"""
        self._title_bar_height = max(15, height)
        self._updateTitleBarHeight()
        self.update()

    def setIconColor(self, color):
        """アイコンの色を変更する"""
        self._icon_color = color
        self.update()

    def setIconAlignment(self, alignment):
        """アイコンの配置を変更 (0: kAlignLeft, 1: kAlignRight, 2: kAlignCenter)"""
        if alignment in [self.kAlignLeft, self.kAlignRight, self.kAlignCenter]:
            self._icon_alignment = alignment
            self.update()
            
    def setIconStyle(self, style):
        """アイコンの配置を変更 (0: left, 1: kArrow, 2: kPlusMinus, 3: kCircle)"""
        if style in [self.kTriangle, self.kArrow, self.kPlusMinus, self.kCircle]:
            self._icon_style = style
            self.update()

    def setIconVisible(self, visible):
        """タイトルの表示・非表示を切り替える"""
        self._is_icon_visible = visible
        self.update()

    def setFrameStyle(self, style):
        """フレームのスタイルを変更"""
        if style in [self.kDefault, self.kSolid, self.kRounded, self.kDashed]:
            self._frame_style = style
            self._updateFrameStyle()

    def setCollapsedEnabled(self, enabled):
        """折りたたみの効化を変更"""
        self._is_collapsable = enabled

    def setAnimationEnabled(self, enabled):
        """アニメーション有効化を変更"""
        self._is_animation_enabled = enabled

    def setContentsMargins(self, x, y, width, height):
        self.content_layout.setContentsMargins(x, y, width, height)

    def setSpacing(self, spacing):
        self.content_layout.setSpacing(spacing)

    # private method
    def _updateTitleBarHeight(self):
        self.main_layout.setContentsMargins(0, self._title_bar_height, 0, 0)
    
    def _updateFrameStyle(self):
        """フレームデザインを適用"""
        self.frame.setStyleSheet(self._frame_styles.get(self._frame_style, "border: 2px solid gray;"))

    def _updateIconRotation(self, value):
        """アイコンの回転角度を更新"""
        self._rotation_angle = value
        self.update()

    def _getContentHeight(self):
        """レイアウト内のすべてのウィジェットの合計最小高さを取得"""
        margin = 5
        total_height = margin
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item.widget():
                total_height += item.widget().minimumSizeHint().height() + margin
        return total_height

    def _toggle(self):
        """折りたたみ/展開を切り替え"""
        self._is_collapsed = not self._is_collapsed

        if self._is_animation_enabled:
            # 展開と折りたたみのアニメーション
            if self._is_collapsed:
                self.frame_animation.setStartValue(self.frame.height())
                self.frame_animation.setEndValue(0)
            else:
                self.frame_animation.setStartValue(0)
                self.frame_animation.setEndValue(max(self._getContentHeight(), self.frame_geometry.height()))

            self.frame_animation.start()
            
            # アイコン回転のアニメーション
            if self._icon_alignment == self.kAlignRight:
                start_angle = 0 if self._is_collapsed else 90
                end_angle = 90 if self._is_collapsed else 0
            else:
                start_angle = 0 if self._is_collapsed else -90
                end_angle = -90 if self._is_collapsed else 0
                
            self.icon_animation.setStartValue(start_angle)
            self.icon_animation.setEndValue(end_angle)
            self.icon_animation.start()
            
        else:
            self.frame.setVisible(not self._is_collapsed)
        
        self.toggled.emit(self._is_collapsed)
        self.update()

    def _drawTriangle(self, painter, center):
        """展開アイコン（三角形）の描画"""
        path = QtGui.QPainterPath()
        
        if self._is_animation_enabled:
            path.moveTo(center.x() - 5, center.y() - 4)
            path.lineTo(center.x() + 5, center.y() - 4)
            path.lineTo(center.x(), center.y() + 4)
            path.closeSubpath()
            
            transform = QtGui.QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(self._rotation_angle)
            transform.translate(-center.x(), -center.y())
            path = transform.map(path)
        else:
            if self._is_collapsed:
                path.moveTo(center.x() - 4, center.y() - 5)
                path.lineTo(center.x() - 4, center.y() + 5)
                path.lineTo(center.x() + 4, center.y())
            else:
                path.moveTo(center.x() - 5, center.y() - 4)
                path.lineTo(center.x() + 5, center.y() - 4)
                path.lineTo(center.x(), center.y() + 4)
        
        painter.setBrush(self._icon_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawPath(path)
        
    def _drawArrow(self, painter, center):
        """展開アイコン（矢印）の描画"""
        path = QtGui.QPainterPath()
        
        if self._is_animation_enabled:
            path.moveTo(center.x() - 5, center.y() - 2)
            path.lineTo(center.x(), center.y() + 3)
            path.lineTo(center.x() + 5, center.y() - 2)
            
            transform = QtGui.QTransform()
            transform.translate(center.x(), center.y())
            transform.rotate(self._rotation_angle)
            transform.translate(-center.x(), -center.y())
            path = transform.map(path)
        else:
            if self._is_collapsed:
                path.moveTo(center.x() - 2, center.y() - 5)
                path.lineTo(center.x() + 3, center.y())
                path.lineTo(center.x() - 2, center.y() + 5)
            else:
                path.moveTo(center.x() - 5, center.y() - 2)
                path.lineTo(center.x(), center.y() + 3)
                path.lineTo(center.x() + 5, center.y() - 2)

        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawPath(path)
        
    def _drawPlusMinus(self, painter, center):
        """展開アイコン（プラス、マイナス）の描画"""
        path = QtGui.QPainterPath()

        if self._is_collapsed:
            path.moveTo(center.x() - 4, center.y())
            path.lineTo(center.x() + 4, center.y())
            path.moveTo(center.x(), center.y() - 5)
            path.lineTo(center.x(), center.y() + 5)
        else:
            path.moveTo(center.x() - 5, center.y())
            path.lineTo(center.x() + 5, center.y())

        path.closeSubpath()

        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.drawPath(path)

    def _drawCircle(self, painter, center):
        """展開アイコン（プラス、マイナス）の描画"""
        pen = QtGui.QPen(self._icon_color)
        pen.setWidth(2)
        painter.setPen(pen)

        if self._is_collapsed:
            painter.setBrush(self._icon_color)
        else:
            painter.setBrush(QtCore.Qt.NoBrush)

        painter.drawEllipse(center, 5, 5)

# ----------------------------------------------------------------------------------
# カラーラベル
# ----------------------------------------------------------------------------------
class ColorLabel(QtWidgets.QWidget):
    def __init__(self, text, color=QtGui.QColor(255, 0, 0), parent=None):
        super(ColorLabel, self).__init__(parent)
        self._text          = text
        self._text_color    = QtGui.QColor(187, 187, 187)
        self._icon_size     = 10
        self._icon_color    = color
        self._margin        = 10
        self._font          = get_font()
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

    # override method
    def sizeHint(self):
        font_metrics = QtGui.QFontMetrics(self._font)
        text_width = font_metrics.width(self._text)
        return QtCore.QSize(self._icon_size + self._margin + text_width, max(self._icon_size, font_metrics.height()))
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # カラー矩形描画
        rect = QtCore.QRect(0, (self.height() - self._icon_size) // 2, self._icon_size, self._icon_size)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self._icon_color)
        painter.drawRect(rect)      
        
        # テキスト描画
        painter.setFont(self._font)
        text_x = self._icon_size + self._margin
        text_rect = QtCore.QRect(text_x, 0, self.width(), self.height())
        painter.setPen(self._text_color)
        painter.drawText(text_rect, QtCore.Qt.AlignVCenter, self._text)

    # public method
    def text(self):
        return self._text
    
    def textSize(self):
        return self.font.pointSize()
    
    def textColor(self):
        return self._text_color
    
    def iconSize(self):
        return self._icon_size

    def iconColor(self):
        return self._icon_color
    
    def margin(self):
        return self._margin
    
    def setText(self, text):
        self._text = text
        self.updateGeometry()
        self.update()
    
    def setTextSize(self, size):
        self._font.setPointSize(size)
        self.updateGeometry()
        self.update()
    
    def setTextColor(self, color):
        self._text_color = color
        self.update()
    
    def setIconSize(self, size):
        self._icon_size = size
        self.updateGeometry()
        self.update()
        
    def setIconColor(self, color):
        self._icon_color = color
        self.update()
    
    def setMargin(self, margin):
        self._margin = margin
        self.updateGeometry()
        self.update()

# ----------------------------------------------------------------------------------
# フローレイアウト
# ----------------------------------------------------------------------------------
class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)
        self._items = []
        self._vertical_spacing = 5
        
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(5)
            
    # override method
    def addItem(self, item):
        self._items.append(item)
        
    def count(self):
        return len(self._items)
    
    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0))
        return height

    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QtCore.QSize()
        
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
            
        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size
    
    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect)
    
    # public method
    def verticalSpacing(self):
        """アイテムの垂直の間隔

        Returns:
            int: 間隔
        """        
        return self._vertical_spacing
    
    def setVerticalSpacing(self, spacing):
        """アイテムの垂直の間隔を設定

        Args:
            spacing (int): 間隔
        """        
        self._vertical_spacing = spacing
        self.update()
    
    # private method
    def _do_layout(self, rect):
        """サイズによってアイテムを再配置

        Args:
            rect (QtCore.QRect): レイアウトサイズ
        """        
        if not self._items:
            return
        
        x = rect.x()
        y = rect.y()
        row_height = 0
        for item in self._items:
            widget = item.widget()
            size = widget.sizeHint()
            if x + size.width() > rect.right():
                x = rect.x()
                y += row_height + self._vertical_spacing
                row_height = 0
                
            item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), size))
            x += size.width() + self.spacing()
            row_height = max(row_height, size.height())
            
        return y + row_height - rect.y()


# ----------------------------------------------------------------------------------
# メニュースタックウィジェット
# ----------------------------------------------------------------------------------
class MenuButton(QtWidgets.QPushButton):
    def __init__(self, text, color=QtGui.QColor(255, 0, 0), parent=None):
        super(MenuButton, self).__init__(text, parent)
        self._color = QtGui.QColor(color)
        self._toggle_color = self._adjust_color_brightness(self._color, 0.8)
        
        self.setAcceptDrops(True)
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setStyle()
        
        self.toggled.connect(self.setStyle)
    
    # override method
    def mousePressEvent(self, event):
        """ドラッグ開始処理"""
        if event.button() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            mime_data.setText(self.text())

            drag.setMimeData(mime_data)

            pixmap = self.grab()  # ボタンのスナップショットを取得
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())  # ドラッグ時の位置調整

            self.setStyleSheet("opacity: 0.5;")  # ドラッグ中は透明度を下げる

            drag.exec_(QtCore.Qt.MoveAction)
            self.setStyle()  # ドラッグ終了後にスタイルを戻す
    
    # public method
    
    # private method
    def setStyle(self):
        """ボタンのスタイルを適用"""
        if self.isChecked():
            bg_color = self._toggle_color
        else:
            bg_color = self._color

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color.name()};
                color: white;
                border-radius: 5px;
                border: 2px solid {self._color.darker(150).name()};
            }}
            QPushButton:hover {{
                background-color: {self._adjust_color_brightness(bg_color, 1.2).name()};
            }}
            QPushButton:pressed {{
                background-color: {self._adjust_color_brightness(bg_color, 0.8).name()};
            }}
        """)

    def _adjust_color_brightness(self, color, factor):
        """カラーの明るさを調整"""
        return QtGui.QColor(
            min(255, int(color.red() * factor)),
            min(255, int(color.green() * factor)),
            min(255, int(color.blue() * factor))
        )
    
class VerticalMenu(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """縦にトグルボタンを並べるメニュー"""
        super(VerticalMenu, self).__init__(parent)
        self._drop_line_y = None
        self._drop_index = None
         
        self.setAcceptDrops(True)
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        

    def addMenuButton(self, text, color=QtGui.QColor(255, 0, 0)):
        """メニューにボタンを追加"""
        button = MenuButton(text, color)
        self.layout.addWidget(button)
        return button

    def dragEnterEvent(self, event):
        """ドラッグがメニュー上に入ったとき"""
        self._updateDropIndicator(event.pos())
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """ドラッグ中にインジケータ位置を更新"""
        self._updateDropIndicator(event.pos())
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        """ドラッグがメニューから離れたとき、インジケータをクリア"""
        self._drop_line_y = None
        self._drop_index = None
        self.update()
        event.accept()

    def dropEvent(self, event):
        """ドラッグ＆ドロップ処理"""
        dragged_text = event.mimeData().text()
        dragged_button = None

        # 既存のボタンを探す
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, MenuButton) and widget.text() == dragged_text:
                dragged_button = widget
                break

        if dragged_button:
            # 位置を更新
            self.layout.removeWidget(dragged_button)
            self.layout.insertWidget(self._drop_index, dragged_button)

        self._drop_line_y = None  # インジケータクリア
        self._drop_index = None
        self.update()

    def findDropPosition(self, pos):
        """ドロップ位置を計算"""
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and pos.y() < widget.y() + widget.height() // 2:
                return i
        return self.layout.count()
    
    def _updateDropIndicator(self, pos):
        """ドロップ位置に基づきインジケータ位置（Y座標）を更新"""
        index = self.findDropPosition(pos)
        self._drop_index = index  # ドロップインデックスを更新

        if index == 0:
            # インデックス0番目の場合、ボタンの上部に横線を描画
            if self.layout.count() > 0:
                widget = self.layout.itemAt(0).widget()
                self._drop_line_y = widget.y()  # 上端に合わせる
        else:
            if index < self.layout.count():
                widget = self.layout.itemAt(index).widget()
                if pos.y() < widget.y() + widget.height() // 2:
                    # ドラッグしたボタンより上の位置にドロップする場合
                    self._drop_line_y = widget.y()  # 上部に横線
                else:
                    # ドラッグしたボタンより下の位置にドロップする場合
                    self._drop_line_y = widget.y() + widget.height()  # 下部に横線
            else:
                # 最後の場合は、最後のウィジェットの下端
                if self.layout.count() > 0:
                    widget = self.layout.itemAt(self.layout.count() - 1).widget()
                    self._drop_line_y = widget.y() + widget.height()

        self.update()  # 再描画を要求

    def paintEvent(self, event):
        """通常の描画に加えて、ドロップインジケータ（横線）を描画"""
        super(VerticalMenu, self).paintEvent(event)
        if self._drop_line_y is not None:
            painter = QtGui.QPainter(self)
            pen = QtGui.QPen(QtGui.QColor("blue"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(0, self._drop_line_y, self.width(), self._drop_line_y)






