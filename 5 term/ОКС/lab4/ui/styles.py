class AppStyles:
    COLORS = {
        "primary": "#A8D5BA",
        "secondary": "#9B87F5",
        "accent": "#f3d8ce",
        "monitor": "#F8BBD9",
        "light": "#E8D5CC",
        "dark": "#2D3436",
        "background": "#F9F7F7",
        "surface": "#FFFFFF",
        "surface_light": "#FDF6F3",
        "text": "#2D3436",
        "text_light": "#636E72",
        "border": "#D4C1B8",
        "frame_border": "#9B87F5",
        "log_background": "#FFFFFF",
        "log_text": "#2D3436",
    }

    @classmethod
    def get_stylesheet(cls):
        return f"""
        QMainWindow {{
            background-color: {cls.COLORS['background']};
            color: {cls.COLORS['text']};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}

        QGroupBox {{
            background-color: {cls.COLORS['surface']};
            border: 2px solid {cls.COLORS['frame_border']};
            border-radius: 12px;
            margin-top: 1ex;
            padding-top: 10px;
            font-weight: bold;
            color: {cls.COLORS['text']};
            min-width: 300px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 4px 12px;
            background-color: {cls.COLORS['surface']};
            color: {cls.COLORS['secondary']};
            font-size: 12px;
            font-weight: bold;
            border: 1px solid {cls.COLORS['frame_border']};
            border-radius: 8px;
        }}

        QPushButton {{
            border: none;
            border-radius: 8px;
            padding: 12px 8px;
            font-weight: bold;
            font-size: 11px;
            min-height: 25px;
            margin: 4px;
        }}

        QTextEdit, QListWidget {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: 8px;
            padding: 8px;
            color: {cls.COLORS['text']};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
        }}

        QSpinBox, QLineEdit, QComboBox {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: 6px;
            padding: 8px;
            color: {cls.COLORS['text']};
            font-size: 12px;
            min-height: 20px;
        }}

        QLabel {{
            color: {cls.COLORS['text']};
            padding: 6px;
            font-size: 12px;
        }}

        QProgressBar {{
            border: 1px solid {cls.COLORS['border']};
            border-radius: 4px;
            text-align: center;
            background-color: {cls.COLORS['surface']};
        }}

        QProgressBar::chunk {{
            background-color: {cls.COLORS['primary']};
            border-radius: 3px;
        }}

        QSlider::groove:horizontal {{
            border: 1px solid {cls.COLORS['border']};
            height: 6px;
            background: {cls.COLORS['surface']};
            margin: 2px 0;
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background: {cls.COLORS['primary']};
            border: 1px solid {cls.COLORS['primary']};
            width: 16px;
            margin: -4px 0;
            border-radius: 8px;
        }}

        QSlider::handle:horizontal:hover {{
            background: {cls.COLORS['secondary']};
        }}

        QComboBox {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: 6px;
            padding: 8px;
            min-width: 60px;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {cls.COLORS['primary']};
            width: 0px;
            height: 0px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {cls.COLORS['surface']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: 6px;
            selection-background-color: {cls.COLORS['accent']};
            selection-color: {cls.COLORS['text']};
        }}

        QLineEdit:focus, QComboBox:focus {{
            border: 2px solid {cls.COLORS['primary']};
            background-color: {cls.COLORS['surface_light']};
        }}
        """