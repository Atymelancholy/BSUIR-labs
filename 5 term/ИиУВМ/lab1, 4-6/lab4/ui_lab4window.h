#ifndef UI_LAB4WINDOW_H
#define UI_LAB4WINDOW_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QGroupBox>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QTextEdit>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_Lab4Window
{
public:
    QWidget *centralWidget;
    QVBoxLayout *verticalLayout;
    QLabel *titleLabel;
    QGroupBox *groupBoxControls;
    QVBoxLayout *verticalLayout_2;
    QHBoxLayout *horizontalLayout;
    QPushButton *btnTakePhoto;
    QPushButton *btnRecordVideo;
    QSpinBox *spinVideoDuration;
    QLabel *labelDuration;
    QHBoxLayout *horizontalLayout_2;
    QPushButton *btnCameraInfo;
    QPushButton *btnToggleSecret;
    QPushButton *btnBack;
    QGroupBox *groupBoxLog;
    QVBoxLayout *verticalLayout_3;
    QTextEdit *textLog;

    void setupUi(QMainWindow *Lab4Window)
    {
        if (Lab4Window->objectName().isEmpty())
            Lab4Window->setObjectName("Lab4Window");
        Lab4Window->resize(800, 600);
        centralWidget = new QWidget(Lab4Window);
        centralWidget->setObjectName("centralWidget");
        verticalLayout = new QVBoxLayout(centralWidget);
        verticalLayout->setSpacing(15);
        verticalLayout->setContentsMargins(20, 20, 20, 20);
        verticalLayout->setObjectName("verticalLayout");

        titleLabel = new QLabel(centralWidget);
        titleLabel->setObjectName("titleLabel");
        titleLabel->setText("Лабораторная работа 4 - Работа с камерой");
        titleLabel->setStyleSheet("font-size: 24px; font-weight: bold; color: #8B4513;");
        titleLabel->setAlignment(Qt::AlignCenter);
        verticalLayout->addWidget(titleLabel);

        groupBoxControls = new QGroupBox(centralWidget);
        groupBoxControls->setObjectName("groupBoxControls");
        groupBoxControls->setTitle("Управление камерой");
        verticalLayout_2 = new QVBoxLayout(groupBoxControls);
        verticalLayout_2->setSpacing(10);
        verticalLayout_2->setObjectName("verticalLayout_2");

        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setSpacing(10);
        horizontalLayout->setObjectName("horizontalLayout");

        btnTakePhoto = new QPushButton(groupBoxControls);
        btnTakePhoto->setObjectName("btnTakePhoto");
        btnTakePhoto->setText("Сделать фото");
        horizontalLayout->addWidget(btnTakePhoto);

        btnRecordVideo = new QPushButton(groupBoxControls);
        btnRecordVideo->setObjectName("btnRecordVideo");
        btnRecordVideo->setText("Записать видео");
        horizontalLayout->addWidget(btnRecordVideo);

        labelDuration = new QLabel(groupBoxControls);
        labelDuration->setObjectName("labelDuration");
        labelDuration->setText("Длительность (сек):");
        horizontalLayout->addWidget(labelDuration);

        spinVideoDuration = new QSpinBox(groupBoxControls);
        spinVideoDuration->setObjectName("spinVideoDuration");
        spinVideoDuration->setMinimum(1);
        spinVideoDuration->setMaximum(3600);
        spinVideoDuration->setValue(10);
        horizontalLayout->addWidget(spinVideoDuration);

        horizontalLayout->addStretch();
        verticalLayout_2->addLayout(horizontalLayout);

        horizontalLayout_2 = new QHBoxLayout();
        horizontalLayout_2->setSpacing(10);
        horizontalLayout_2->setObjectName("horizontalLayout_2");

        btnCameraInfo = new QPushButton(groupBoxControls);
        btnCameraInfo->setObjectName("btnCameraInfo");
        btnCameraInfo->setText("Информация о камерах");
        horizontalLayout_2->addWidget(btnCameraInfo);

        btnToggleSecret = new QPushButton(groupBoxControls);
        btnToggleSecret->setObjectName("btnToggleSecret");
        btnToggleSecret->setText("Войти в скрытый режим");
        horizontalLayout_2->addWidget(btnToggleSecret);

        btnBack = new QPushButton(groupBoxControls);
        btnBack->setObjectName("btnBack");
        btnBack->setText("Назад в меню");
        horizontalLayout_2->addWidget(btnBack);

        horizontalLayout_2->addStretch();
        verticalLayout_2->addLayout(horizontalLayout_2);

        verticalLayout->addWidget(groupBoxControls);

        groupBoxLog = new QGroupBox(centralWidget);
        groupBoxLog->setObjectName("groupBoxLog");
        groupBoxLog->setTitle("Лог событий");
        verticalLayout_3 = new QVBoxLayout(groupBoxLog);
        verticalLayout_3->setSpacing(5);
        verticalLayout_3->setObjectName("verticalLayout_3");

        textLog = new QTextEdit(groupBoxLog);
        textLog->setObjectName("textLog");
        textLog->setReadOnly(true);
        verticalLayout_3->addWidget(textLog);

        verticalLayout->addWidget(groupBoxLog, 1);

        Lab4Window->setCentralWidget(centralWidget);

        retranslateUi(Lab4Window);

        QMetaObject::connectSlotsByName(Lab4Window);
    }

    void retranslateUi(QMainWindow *Lab4Window)
    {
        Lab4Window->setWindowTitle(QCoreApplication::translate("Lab4Window", "Лабораторная работа 4 - Работа с камерой", nullptr));
    }
};

namespace Ui {
class Lab4Window: public Ui_Lab4Window {};
}

QT_END_NAMESPACE

#endif // UI_LAB4WINDOW_H
