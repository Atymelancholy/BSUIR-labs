#ifndef MAININTERFACE_H
#define MAININTERFACE_H

#include <QMainWindow>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QLabel>
#include <QStackedWidget>
#include "device_scanner.h"

class MainInterface : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainInterface(QWidget *parent = 0);
    ~MainInterface();

private slots:
    void displayDeviceScanner();
    void displayNextLab();
    void returnToHome();

private:
    void initializeComponents();
    void setupVisualStyle();
    void createHomeScreen();
    void createNextLabScreen();

    QStackedWidget *contentArea;
    QWidget *homeScreen;
    DeviceScanner *deviceScanner;
    QWidget *nextLabScreen;
};

#endif
