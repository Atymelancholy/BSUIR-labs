QT += core gui widgets

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++17

# Подключаем настройки OpenCV
include(opencv.pri)

SOURCES += \
    battery.cpp \
    characteranimation.cpp \
    lab1window.cpp \
    lab4window.cpp \
    lab5window.cpp \
    lab6window.cpp \
    main.cpp \
    mainwindow.cpp \
    stepbutton.cpp \
    usbmanager.cpp

HEADERS += \
    battery.h \
    characteranimation.h \
    lab1window.h \
    lab4window.h \
    lab5window.h \
    lab6window.h \
    mainwindow.h \
    stepbutton.h \
    usbmanager.h

FORMS += \
    mainwindow.ui

RESOURCES += \
    resources.qrc

win32 {
    LIBS += -lPowrProf
    LIBS += -lsetupapi
    # Библиотеки для REAL Bluetooth
    LIBS += -lws2_32
    LIBS += -lBthprops
    LIBS += -lrpcrt4
}
