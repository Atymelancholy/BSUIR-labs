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
    main.cpp \
    mainwindow.cpp \
    stepbutton.cpp

HEADERS += \
    battery.h \
    characteranimation.h \
    lab1window.h \
    lab4window.h \
    lab5window.h \
    mainwindow.h \
    stepbutton.h

FORMS += \
    mainwindow.ui

RESOURCES += \
    resources.qrc

win32 {
    LIBS += -lPowrProf
    LIBS += -lsetupapi
}
